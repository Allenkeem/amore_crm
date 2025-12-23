import json
import math
import re
from typing import List, Dict, Any, Tuple
from collections import defaultdict, Counter
import logging

from .config import WEIGHTS, RETRIEVAL_TOP_K, CANDIDATE_POOL_SIZE
# Path moved:
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../"))
PRODUCT_CARDS_PATH = os.path.join(BACKEND_ROOT, "data", "product_agent", "product_cards.jsonl")
NEWS_CARDS_PATH = os.path.join(BACKEND_ROOT, "data", "product_agent", "news_cards.jsonl")
from .normalize import normalize_brand, normalize_query, extract_attributes
from .schemas import ProductCandidate, MatchDetails, Evidence, EvidenceHighlight
from .factsheet import build_factsheet

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleLexicalIndex:
    """A simple inverted index for retrieval."""
    def __init__(self):
        self.index = defaultdict(list)
        self.doc_lengths = {}
        self.avg_doc_length = 0
        self.total_docs = 0

    def tokenize(self, text: str) -> List[str]:
        # Simple whitespace and char filtering
        text = re.sub(r"[^a-zA-Z0-9가-힣\s]", "", text)
        return text.lower().split()

    def add_document(self, doc_id: str, text: str):
        tokens = self.tokenize(text)
        self.doc_lengths[doc_id] = len(tokens)
        term_freqs = Counter(tokens)
        for term, freq in term_freqs.items():
            self.index[term].append((doc_id, freq))
        self.total_docs += 1

    def finalize(self):
        if self.total_docs > 0:
            self.avg_doc_length = sum(self.doc_lengths.values()) / self.total_docs

    def search(self, query: str) -> Dict[str, float]:
        """BM25-like scoring."""
        tokens = self.tokenize(query)
        scores = defaultdict(float)
        k1 = 1.5
        b = 0.75
        
        for term in tokens:
            if term not in self.index: continue
            
            # IDF
            doc_freq = len(self.index[term])
            idf = math.log((self.total_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
            
            for doc_id, freq in self.index[term]:
                doc_len = self.doc_lengths[doc_id]
                term_score = idf * (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * (doc_len / self.avg_doc_length)))
                scores[doc_id] += term_score
        
        # Normalize scores to 0-1 range roughly
        if not scores: return {}
        max_score = max(scores.values())
        if max_score > 0:
            for d in scores:
                scores[d] /= max_score
        return scores

class ProductRetriever:
    def __init__(self):
        self.products = {} # id -> data
        self.news_data = {} # id -> data
        self.index = SimpleLexicalIndex()
        self.max_review_count = 1
        self._load_data()

    def _load_data(self):
        """Load product cards and build index."""
        logger.info(f"Loading products from {PRODUCT_CARDS_PATH}")
        try:
            with open(PRODUCT_CARDS_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    data = json.loads(line)
                    pid = data["product_id"]
                    self.products[pid] = data
                    
                    # Update max review for normalization
                    rc = data.get("review_count", 0)
                    if rc > self.max_review_count:
                        self.max_review_count = rc
                    
                    # Indexing Fields: Brand, Name, Keywords, Reviews (partial)
                    text_parts = [
                        data.get("brand", ""),
                        data.get("product_name", "")
                    ]
                    # Add topic keywords
                    if "signals" in data:
                        for mode in ["EFFICACY", "PURCHASE"]:
                            for topic in data["signals"].get(mode, []):
                                text_parts.extend(topic.get("keywords", []))
                                text_parts.append(topic.get("topic_label", ""))
                    
                    self.index.add_document(pid, " ".join(text_parts))
            
            self.index.finalize()
            logger.info(f"Indexed {len(self.products)} products.")

            # Load News Cards
            logger.info(f"Loading news from {NEWS_CARDS_PATH}")
            try:
                with open(NEWS_CARDS_PATH, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip(): continue
                        data = json.loads(line)
                        pid = data.get("product_id")
                        if pid:
                            self.news_data[pid] = data
                logger.info(f"Loaded {len(self.news_data)} news cards.")
            except FileNotFoundError:
                logger.warning(f"News data file not found: {NEWS_CARDS_PATH}")
            
        except FileNotFoundError:
            logger.error(f"Data file not found: {PRODUCT_CARDS_PATH}")

    def parse_query(self, user_query: str) -> Dict[str, Any]:
        """Step A: Query Parsing."""
        q_norm = normalize_query(user_query)
        
        # 1. Attributes
        atts = extract_attributes(q_norm)
        
        # 2. Brand (Heuristic: Check known brands against query)
        brand = None
        # We need a list of brands to check against. 
        # For optimization, we could build a trie, but iteration is fine for now.
        # Let's extract brands from loaded products or config
        known_brands = set(p.get("brand", "").lower() for p in self.products.values())
        
        # Also check normalized aliases (reverse check hard, so extracted from tokens)
        tokens = q_norm.split()
        for t in tokens:
            norm_t = normalize_brand(t)
            # Check if norm_t is a known brand
            # This is a simplification. Real world needs better NER.
            for kb in known_brands:
                if norm_t == kb or norm_t in kb: # 'hera' == 'hera'
                    brand = kb
                    break
            if brand: break
            
        return {
            "p_query": q_norm,
            "brand": brand,
            "attributes": atts
        }

    def retrieve(self, user_query: str) -> List[ProductCandidate]:
        """Execute retrieval pipeline."""
        
        # 1. Parse
        parsed = self.parse_query(user_query)
        logger.info(f"Parsed Query: {parsed}")
        
        # 2. Lexical Search (Candidate Generation)
        # Boost matches with brand if extracted
        search_query = parsed["p_query"]
        if parsed["brand"]:
            search_query += f" {parsed['brand']} " * 3 # Boost brand terms
        
        lex_scores = self.index.search(search_query)
        
        # If no lexical matches, return empty (or fallback to popularity?)
        if not lex_scores:
            logger.warning("No lexical matches found.")
            return []
            
        # Select Candidates (Top N)
        sorted_cands = sorted(lex_scores.items(), key=lambda x: x[1], reverse=True)[:CANDIDATE_POOL_SIZE]
        candidate_ids = [pid for pid, score in sorted_cands]
        
        # 3. Re-ranking
        ranked_candidates = []
        
        for pid in candidate_ids:
            product = self.products[pid]
            p_brand = product.get("brand", "").lower()
            p_name = product.get("product_name", "").lower()
            
            # --- Score Calculation ---
            
            # A. Entity Match
            entity_score = 0.0
            if parsed["brand"] and parsed["brand"] == p_brand:
                entity_score = 1.0
            # Simple name match overlap
            if parsed["p_query"] in p_name: 
                entity_score = max(entity_score, 0.8)
                
            # B. Lexical Score (Already normalized)
            lex_score = lex_scores.get(pid, 0.0)
            
            # C. Attribute Match
            att_score = 0.0
            matched_atts = []
            if parsed["attributes"]:
                # Check coverage in fit reasons + signals
                doc_text = str(product.get("signals", "")) + str(product.get("persona_fit", "")) + p_name
                hits = 0
                for att in parsed["attributes"]:
                    if att in doc_text:
                        hits += 1
                        matched_atts.append(att)
                att_score = hits / len(parsed["attributes"])
                
            # D. Review Count
            rc = product.get("review_count", 0)
            log_rc_score = 0.0
            if self.max_review_count > 0:
                log_rc_score = math.log(rc + 1) / math.log(self.max_review_count + 1)
                
            # Final Score
            # weights: entity(0.35), lex(0.25), vec(0.25), att(0.10), log_rc(0.05)
            # vector score is 0
            final_score = (
                WEIGHTS["entity_match"] * entity_score +
                WEIGHTS["lexical_score"] * lex_score +
                WEIGHTS["vector_score"] * 0.0 + 
                WEIGHTS["attribute_match"] * att_score +
                WEIGHTS["log_review_count"] * log_rc_score
            )
            
            # 4. Build Evidence & Highlight
            highlights = []
            if parsed["brand"] == p_brand:
                 highlights.append(EvidenceHighlight(type="brand_match", text=p_brand))
            for att in matched_atts:
                 highlights.append(EvidenceHighlight(type="attribute_match", text=att))
            # Review snippet check? (Optional/Simple)
            
            # 5. Build Object
            cand = ProductCandidate(
                rank=0, # Assigned later
                product_id=pid,
                brand=product.get("brand", ""),
                product_name=product.get("product_name", ""),
                score=round(final_score, 4),
                match=MatchDetails(
                    matched_entities=[parsed["brand"]] if parsed["brand"] else [],
                    matched_attributes=matched_atts
                ),
                factsheet=build_factsheet(product, self.news_data.get(pid)),
                evidence=Evidence(highlights=highlights)
            )
            ranked_candidates.append(cand)
            
        # Sort by Final Score
        ranked_candidates.sort(key=lambda x: x.score, reverse=True)
        
        # Apply Top-K and Reranking filter (Max 2 per base product?)
        # For now just simple Top-K
        final_top = ranked_candidates[:RETRIEVAL_TOP_K]
        
        # Assign Ranks
        for i, cand in enumerate(final_top):
            cand.rank = i + 1
            
        return final_top

# Singleton Instance (Optional, but useful for API)
_retriever_instance = None
def get_retriever():
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = ProductRetriever()
    return _retriever_instance
