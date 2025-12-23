import os
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from .config import OPENAI_API_KEY, EMBEDDING_MODEL, LLM_MODEL

class RetrievalEngine:
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set.")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        
    def get_embedding(self, text, model=EMBEDDING_MODEL):
        text = text.replace("\n", " ")
        return self.client.embeddings.create(input=[text], model=model).data[0].embedding

    def retrieve_top_k(self, query_embedding, db, k=5):
        if not db:
            return []
        
        db_embeddings = [item['embedding'] for item in db]
        if not db_embeddings:
            return []
            
        similarities = cosine_similarity([query_embedding], db_embeddings)[0]
        
        # Get top-k indices
        top_indices = similarities.argsort()[-k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                "score": similarities[idx],
                "metadata": db[idx]['metadata']
            })
        return results

    def generate_legal_queries(self, crm_message):
        """
        Smart Query Generation using LLM.
        """
        prompt = f"""
        Analyze the CRM message and generate 3 specific legal search queries.
        Goal: Retrieve rules that apply to SMS/LMS, but ALSO common rules for all advertising media (e.g., Article 50).
        
        CRM Message:
        {crm_message}
        
        Generate concise queries for:
        1. SMS-specific marking requirements (Opt-out, Sender ID).
        2. Common advertising prohibitions (False/Exaggerated claims, common to all media).
        3. Product-specific restrictions (e.g., Cosmetics medical claims).
        
        Output List only.
        """
        
        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        queries = response.choices[0].message.content.strip().split("\n")
        return [q.split(". ")[-1] for q in queries if q.strip()]

    def get_combined_context(self, message, spam_db, cosmetics_db):
        # 1. Query Expansion
        search_queries = self.generate_legal_queries(message)
        print(f"[RegulationAgent] Generated Search Queries: {search_queries}")
        
        all_spam_docs = []
        all_cosmetics_docs = []
        
        # 2. Retrieve for EACH query
        for q in search_queries:
            q_vec = self.get_embedding(q)
            all_spam_docs.extend(self.retrieve_top_k(q_vec, spam_db, k=3))
            all_cosmetics_docs.extend(self.retrieve_top_k(q_vec, cosmetics_db, k=3))
            
        # Also retrieve for original message
        original_vec = self.get_embedding(message)
        all_spam_docs.extend(self.retrieve_top_k(original_vec, spam_db, k=3))
        all_cosmetics_docs.extend(self.retrieve_top_k(original_vec, cosmetics_db, k=3))
        
        # 3. Deduplicate
        def deduplicate(docs):
            unique_docs = []
            seen_headers = set()
            for doc in docs:
                key = doc['metadata']['header'] + doc['metadata']['content'][:30]
                if key not in seen_headers:
                    unique_docs.append(doc)
                    seen_headers.add(key)
            return unique_docs

        final_spam_docs = deduplicate(all_spam_docs)
        final_cosmetics_docs = deduplicate(all_cosmetics_docs)
        
        context_text = f"-- [Regulation 1: Spam Prevention & IT Network Act (Total {len(final_spam_docs)})] --\n"
        for doc in final_spam_docs:
            context_text += f"Header: {doc['metadata']['header']}\nContent: {doc['metadata']['content']}\n\n"
            
        context_text += f"\n-- [Regulation 2: Cosmetics Guidelines (Total {len(final_cosmetics_docs)})] --\n"
        for doc in final_cosmetics_docs:
            context_text += f"Header: {doc['metadata']['header']}\nContent: {doc['metadata']['content']}\n\n"
            
        return context_text
