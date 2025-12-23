from typing import Dict, List, Any
import re
from .schemas import Factsheet, FactsheetSignals, VoiceInfo, OfficialInfo

def extract_usage(reviews: List[str]) -> List[str]:
    """Extract usage instructions from reviews (Heuristic)."""
    usage_patterns = [
        r"([^.]*발라[^.]*)",
        r"([^.]*사용[^.]*)",
        r"([^.]*단계[^.]*)",
        r"([^.]*루틴[^.]*)"
    ]
    extracted = []
    for review in reviews[:5]: # Check top 5 reviews
        for pattern in usage_patterns:
            matches = re.findall(pattern, review)
            for m in matches:
                if len(m) < 10 or len(m) > 50: continue # Filter noise
                extracted.append(m.strip())
                if len(extracted) >= 3: break
        if len(extracted) >= 3: break
    
    return list(set(extracted))[:3]

def infer_category(product_name: str, topic_labels: List[str]) -> str:
    """Infer product category from name and topics."""
    name = product_name.lower()
    if "스킨" in name or "토너" in name: return "스킨/토너"
    if "크림" in name or "밤" in name: return "크림/밤"
    if "세럼" in name or "에센스" in name or "앰플" in name: return "에센스/세럼/앰플"
    if "선크림" in name or "자외선" in name or "선케어" in name: return "선케어"
    if "샴푸" in name or "트리트먼트" in name or "두피" in name: return "헤어케어"
    if "쿠션" in name or "파운데이션" in name or "메이크업" in name: return "메이크업"
    if "클렌징" in name or "워시" in name or "폼" in name: return "클렌징"
    return "기타"

def build_factsheet(product_data: Dict[str, Any], news_data: Dict[str, Any] = None) -> Factsheet:
    """Construct a Factsheet from product data and optional news data."""
    
    # 1. Category
    topics = []
    if "signals" in product_data:
        for t in product_data["signals"].get("EFFICACY", []):
            topics.append(t.get("topic_label", ""))
    
    category = infer_category(product_data.get("product_name", ""), topics)
    
    # 2. Key Claims (Persona Keywods + Topic Keywords) -> Voice Info
    key_claims = set()
    
    # Add fit reasons (which are keywords)
    for fit in product_data.get("persona_fit", [])[:2]: # Top 2 Personas
        for reason in fit.get("why", []):
            if reason.startswith("["): continue # Skip debug tags
            key_claims.add(reason)
            
    # Add top topic keywords
    if "signals" in product_data:
        for mode in ["EFFICACY", "PURCHASE"]:
            for topic in product_data["signals"].get(mode, [])[:2]:
                for k in topic.get("keywords", [])[:3]:
                    key_claims.add(k)
    
    # 3. Signals -> Voice Info
    signals = FactsheetSignals()
    if "signals" in product_data:
        eff = product_data["signals"].get("EFFICACY", [])
        pur = product_data["signals"].get("PURCHASE", [])
        
        signals.EFFICACY = [t.get("topic_label", "").split("_", 1)[1] if "_" in t.get("topic_label", "") else t.get("topic_label", "") 
                            for t in eff[:3]]
        signals.PURCHASE = [t.get("topic_label", "").split("_", 1)[1] if "_" in t.get("topic_label", "") else t.get("topic_label", "") 
                            for t in pur[:3]]

    # 4. Usage -> Voice Info
    reviews = product_data.get("sample_reviews", [])
    usage = extract_usage(reviews)
    
    voice_info = VoiceInfo(
        key_claims=list(key_claims)[:10],
        usage=usage,
        signals=signals
    )
    
    # 5. Official Info (from News)
    official_info = OfficialInfo()
    if news_data:
        official_info.extracted_facts = news_data.get("extracted_facts", [])
    
    return Factsheet(
        product_id=product_data.get("product_id", ""),
        category=category,
        official_info=official_info,
        voice_info=voice_info
    )
