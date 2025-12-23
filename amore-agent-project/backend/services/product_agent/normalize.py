import re

# Brand Aliases (English/Typo/Abbr -> Normalized Korean)
BRAND_ALIASES = {
    "sulwhasoo": "설화수", "sulwha": "설화수", "설화": "설화수",
    "hera": "헤라",
    "laneige": "라네즈", "라네즈": "라네즈",
    "mamonde": "마몽드",
    "iope": "아이오페",
    "hanyul": "한율",
    "primera": "프리메라",
    "etude": "에뛰드", "에뛰드하우스": "에뛰드",
    "innisfree": "이니스프리", "이니스": "이니스프리",
    "miseenscene": "미쟝센", "미장센": "미쟝센",
    "ryo": "려",
    "illiyoon": "일리윤", "일리": "일리윤",
    "laboh": "라보에이치", "라보": "라보에이치", "labo-h": "라보에이치",
    "aestura": "에스트라", "에스트라": "에스트라",
    "bready": "비레디", "비레디": "비레디", "be ready": "비레디",
    "amore": "아모레퍼시픽", "amorepacific": "아모레퍼시픽"
}

# Attribute Mapping (User Query Terms -> Standardized Attributes/Keywords)
ATTRIBUTE_MAPPING = {
    # Texture/Finish
    "끈적임x": ["산뜻", "흡수", "끈적임"],
    "산뜻": ["산뜻", "흡수", "가벼운"],
    "촉촉": ["촉촉", "보습", "수분"],
    "꾸덕": ["꾸덕", "보습", "영양"],
    
    # Efficacy
    "트러블": ["트러블", "진정", "시카", "티트리", "어성초"],
    "민감": ["민감", "순한", "저자극", "무자극", "진정"],
    "순한": ["순한", "저자극", "무자극"],
    "미백": ["미백", "톤업", "비타민", "잡티", "기미"],
    "주름": ["주름", "탄력", "안티에이징", "레티놀", "리프팅", "노화"],
    "탄력": ["탄력", "주름", "안티에이징", "리프팅"],
    "각질": ["각질", "필링", "스크럽", "피지"],
    "모공": ["모공", "피지", "수축"],
    
    # Category/Target
    "남성": ["남성", "옴므", "남자", "올인원"],
    "올인원": ["올인원", "간편"],
    "선크림": ["선크림", "자외선", "차단", "썬크림", "선케어", "spf"],
    "클렌징": ["클렌징", "세안", "폼", "오일", "워터"],
    "샴푸": ["샴푸", "두피", "머리", "탈모"],
    
    # Value
    "가성비": ["가성비", "대용량", "저렴", "합리", "가격"],
    "대용량": ["대용량", "점보", "리필"]
}

def normalize_brand(text: str) -> str:
    """Normalize brand name."""
    text = text.lower().replace(" ", "")
    return BRAND_ALIASES.get(text, text)

def normalize_query(query: str) -> str:
    """Normalize user query for better matching."""
    # Basic cleanup
    query = query.strip().lower()
    return query

def extract_attributes(query: str) -> list[str]:
    """Extract known attributes from query."""
    found = []
    # Simple substring match for now
    for key, values in ATTRIBUTE_MAPPING.items():
        if key in query:
            found.extend(values)
            continue
        # Check values too
        for v in values:
            if v in query:
                found.append(v)
    return list(set(found))
