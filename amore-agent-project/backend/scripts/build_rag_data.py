import pandas as pd
import json
import os
import hashlib
import re
from collections import defaultdict, Counter
from tqdm import tqdm

# ==================================================================================
# [CONFIG]
# ==================================================================================
INPUT_CSV = "../../data_crawl/FINAL_RESULT.csv"
TOPIC_RESULT_DIR = "../data/topic_model_results"
OUTPUT_DIR = "../data/rag_documents"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 페르소나 정의 (수동 매핑 기반)
# 실제로는 LLM을 이용해 Topic->Persona 매핑을 자동화하면 좋지만, 
# 여기서는 예시로 "Rule Base" 매핑을 시뮬레이션합니다.
# (User 요청: 반자동/수동 권장. 여기서는 코드 레벨에서 간단한 매핑 테이블 예시 구현)

# ==================================================================================
# [FILTERING CONSTANTS] - Copied & Expanded from topic_modeling.py
# ==================================================================================

# 1. 브랜드 블랙리스트
BRANDS = {
    "설화수", "마몽드", "에스쁘아", "아이오페", "해피바스", "라네즈", "프리메라", "헤라", "일리윤", "한율", "미쟝센", "려", "바이탈뷰티",
    "sulwhasoo", "mamonde", "espoir", "iope", "happybath", "laneige", "primera", "hera", "illiyoon", "hanyul", "miseenscene", "ryo", "vitalbeauty",
    "웰라쥬", "오디세이", "헤라옴므", "아하바하파하", "아모레", "아모레퍼시픽", "amore", "pacific",
    # [Added] Iteration 4 Noise Filters
    "이니스프리", "에뛰드", "에뛰", "미장센", "오딧세이", "아페쎄", "라보", "에이치", "innisfree", "etude",
    # [Added] Iteration 10 Brand Variants
    "에스뿌아", "진설", "자음" # 설화수/헤라/에스쁘아 관련
}
BRANDS |= {b.lower() for b in BRANDS}

# 2. 프로모션/구매/리뷰 메타어 (Derived 후보에서 제거)
STOPWORDS_DERIVED_NOISE = {
    # 프로모션
    "원플러스원", "행사", "세일", "특가", "증정", "사은품", "쿠폰", "혜택", "이벤트", "리미티드", "기획", "구성", "패키지", "할인", "구매", "내돈내산",
    # [Mod] Removed "가격", "저렴" to allow Value signals. Kept Promo terms.
    # 리뷰 메타/일반
    "배송", "도착", "택배", "기사", "박스", "포장", "샘플", "강추", "비추", "추천", "재구매", "사용", "제품", "진짜", "완전", "너무", "정말", "생각", "느낌",
    "리뷰", "후기", "기자", "체험단", "총평", "평가", "한달", "일주일", "정도", "부분", "이번", "오늘", "역시", "항상",
    # 노이즈/오타 의심
    "가겍", "아싑게", "퀄리디", "허접", "픽드벡", "글쿠", "쇽쇽", "스킨소프너"
}

# 3. 도메인 노이즈 (음식/생활용품 등 메이크업 오분류 유발)
STOPWORDS_DOMAIN_NOISE = {
    "할라피뇨", "요플레", "양치", "수건", "트레이", "치약", "칫솔", "음식", "간식", "쓰레기", 
    "욕실", "청소", "주방", "설거지", "빨래", "가슴" # 신체 부위 노이즈
}

# 4. 일반어/추상명사 노이즈 (Iteration 10)
STOPWORDS_GENERAL = {
    "인원", "전반", "동시", "나중", "방식", "제공", "특징", "현상", "해결", "선호", "만족도", "만족감",
    "대박", "짱짱", "최고", "굿굿", "굳굳", "오오", "우와", "대신", "기존", "비교", "고민", "걱정",
    "마음", "기대", "사람", "사용자", "친구", "언니", "동생", "지인", "어머니", "엄마",
    # [Added] Iteration 11 General Stopwords (Season, Emotion, Common Verbs)
    "요즘", "처음", "구입", "구매", "필요", "감사", "판매", "세트", "겨울", "여름", "봄", "가을", "마스크",
    "때문", "정도", "느낌", "생각", "장점", "단점", "광고"
}

# [Added] Iteration 12 Generic 'Hada' Stopwords (Replaces Regex)
STOPWORDS_GENERIC_HADA = {
    "괜찮다", "좋다", "편하다", "만족하다", "추천하다",
    "그렇다", "나쁘다", "아쉽다", "별로다", "적당하다",
    "훌륭하다", "최고다", "대박이다", "간편하다" 
}

# [Added] Iteration 12 Value/Price Tokens (Boost for specific personas)
VALUE_TOKENS = {
    "가성비", "저렴", "저렴하다", "합리", "합리적", "가격", "할인", "특가", "세일", "구성", "대용량", "혜자"
}

def is_valid_derived_token(token):
    """Derived Keyword로 쓰기에 적합한지 검사"""
    token = token.strip()
    if len(token) < 2: return False
    if token.lower() in BRANDS: return False
    if token in STOPWORDS_DERIVED_NOISE: return False
    if token in STOPWORDS_DOMAIN_NOISE: return False 
    if token in STOPWORDS_GENERAL: return False # [Added] General Stopwords
    if token.isdigit(): return False # 숫자만 있는 경우
    
    # 한글 자모만 있는 경우 (ㅋㅋ, ㅎㅎ 등)
    if re.fullmatch(r'[ㄱ-ㅎㅏ-ㅣ]+', token): return False
    
    # [Added] Iteration 11 Regex Filter: Drop '.*하다' (Verb/Adjective forms)
    # e.g. 간편하다, 저렴하다, 괜찮다, 편하다, 촉촉하다 -> False
    # Exception: '순하다', '촉촉하다' might be good, but user requested to drop '.*하다'.
    # [Mod] Iteration 12: Remove global '.*하다' drop. Use explicit blacklist instead.
    # if re.search(r'하다$', token): return False
    
    # [Added] Iteration 12: Generic 'Hada' Check
    if token in STOPWORDS_GENERIC_HADA: return False
    
    return True

# 3. 페르소나별 제약조건 (Iteration 3)
PERSONA_CONSTRAINTS = {
    "레이지 스킵케어 워킹MZ": {
        # [Refinement] Lazy Mandatory Split: Gate (One of these REQUIRED) vs Bonus (Optional)
        # Gate: "Time/Simple" focus
        "mandatory_gate": ["올인원", "간편", "3분", "루틴", "귀찮"], 
        "negative": ["샴푸", "린스", "헤어", "모발", "두피", "탈모", "머릿결", "염색",
                     "남성", "남자", "남편", "면도", "옴므", "바디", "샤워", "워시", "핸드", "비누"] # Men/Body/Hair Negative
    },
    "가치소비 클린·비건 뷰티액티비스트": {
        # [Refinement] Vegan Mandatory Grouped: Must satisfy Group A AND Group B
        "mandatory_groups": [
            ["비건", "클린", "친환경", "크루얼티프리", "크루얼티"], # Group A: Values
            ["리필", "공병", "재활용", "분리수거", "플라스틱", "종이", "라벨", "친환경"] # Group B: Action/Packaging
        ],
        "negative": ["염색", "새치", "모발", "샴푸", "린스", "트리트먼트", "헤어", "두피", "비듬", "탈모", "머릿결"] 
    },
    "프리미엄 안티에이징 시커": {
        "mandatory": ["탄력", "주름", "노화", "리프팅", "아이크림", "레티놀", "안티에이징", "링클"], 
        "negative": ["샴푸", "린스", "헤어", "모발", "두피", "탈모", "머릿결", 
                     "파데", "파운데이션", "틴트", "립", "섀도우", "팔레트", "쿠션", "블러셔", "메이크업"] 
    }
}

PERSONAS = {
    # ... (Personas remain same, just context reference)
    "레이지 스킵케어 워킹MZ": {
        "keywords": ["올인원", "간편", "흡수", "끈적임", "귀찮", "하나만", "패드", "3분", "루틴"],
        "desc": "20–30대 직장인·학생. 바쁜 일상 속 최소한의 시간으로 관리. 가성비·편리함·올인원 선호."
    },
    "성분깐깐 민감케어러": {
        "keywords": ["진정", "트러블", "성분", "순하다", "자극", "민감", "장벽", "시카", "판테놀", "전성분", "테스트"],
        "desc": "20후반–30대. 민감/트러블 경험. 저자극·무자극·장벽 강화, 성분/임상 신뢰 중요."
    },
    "트렌드 메이크업 헌터": {
        "keywords": ["신상", "한정", "컬러", "발색", "무드", "패키지", "콜라보", "틴트", "글리터"],
        "desc": "20대 초중반. SNS/유튜브 영향. 시즌/한정판/콜라보 색조 위주. 유행하는 룩 구현."
    },
    "프리미엄 안티에이징 시커": {
        "keywords": ["탄력", "주름", "기미", "노화", "영양", "광채", "리프팅", "선물", "품격"],
        "desc": "40대 이상. 탄력·주름 등 복합 안티에이징. 브랜드 헤리티지와 신뢰 중시."
    },
    "가치소비 클린·비건 뷰티액티비스트": {
        "keywords": ["비건", "환경", "지구", "리필", "플라스틱", "클린", "동물", "패키지"],
        "desc": "20–30대. 환경·지속가능성 중시. 비건·크루얼티프리·친환경 패키지 선호."
    },
    "실용파 패밀리·헬스케어 매니저": {
        "keywords": ["가족", "아이", "대용량", "모두", "함께", "안전", "가성비", "마트"],
        "desc": "30–40대 주부/맞벌이. 온 가족이 쓰는 안전한 대용량/실용적 제품 선호."
    },
    "남성 그루밍 입문·업그레이더": {
        "keywords": ["남편", "아빠", "남자", "신랑", "향", "끈적이지", "올인원", "티안나게"],
        "desc": "20–30대 남성. 귀찮지 않지만 티 나는 개선(피부결/모공) 원함. 쉬운 루틴."
    }
}

# ==================================================================================
# [Functions]
# ==================================================================================

# ... (Functions clean_text_for_id, make_brand_id, make_product_id, load_topic_data stay)
def clean_text_for_id(text):
    """ID 생성을 위한 텍스트 정규화 (한글 포함)"""
    if pd.isna(text) or str(text).strip() == "" or str(text).lower() == "nan":
        return "unknown"
    # 한글, 영문, 숫자만 남기고 공백은 dash로
    text = str(text).lower().strip()
    text = re.sub(r'[\s]+', '-', text) # 공백 -> -
    text = re.sub(r'[^a-z0-9가-힣\-]', '', text) # 특수문자 제거
    return text[:30] # 너무 길지 않게 자름

def make_brand_id(brand_name):
    """Brand ID 생성: brand:<normalized>:<hash>"""
    norm = clean_text_for_id(brand_name)
    if norm == "unknown": return "brand:unknown"
    
    # 해시는 정규화된 문자열 기준 (충돌 방지 + 동일성 보장)
    h = hashlib.md5(norm.encode()).hexdigest()[:6]
    return f"brand:{norm}:{h}"

def make_product_id(brand_name, product_name):
    """Product ID 생성: prod:<brand>:<product>:<hash>"""
    b_norm = clean_text_for_id(brand_name)
    p_norm = clean_text_for_id(product_name)
    
    if p_norm == "unknown": return f"prod:unknown:{hashlib.md5(str(product_name).encode()).hexdigest()[:8]}"
    
    # 식별자: 정규화된 값 기준
    raw_key = f"{b_norm}_{p_norm}"
    h = hashlib.md5(raw_key.encode()).hexdigest()[:6]
    
    return f"prod:{b_norm}:{p_norm}:{h}"

def load_topic_data(mode):
    """
    Load document_topics.csv and topic_info.csv for a given mode
    """
    base_path = f"{TOPIC_RESULT_DIR}/{mode}"
    doc_path = f"{base_path}/document_topics.csv"
    info_path = f"{base_path}/topic_info.csv"
    
    if not os.path.exists(doc_path):
        print(f"Warning: {doc_path} not found.")
        return None, None
        
    df_doc = pd.read_csv(doc_path)
    df_info = pd.read_csv(info_path)
    
    # Topic Info를 Dictionary로 변환 (Topic -> {Name, Keywords...})
    # BERTopic output topic_info columns: Topic, Count, Name, Representation, Representative_Docs
    topic_meta = {}
    for _, row in df_info.iterrows():
        # Representation string to list
        # "['a', 'b']" -> clean list
        try:
            keywords = eval(row['Representation'])
        except:
            keywords = []
            
        topic_meta[row['Topic']] = {
            "label": row['Name'], 
            "keywords": keywords
        }
        
    return df_doc, topic_meta

def calculate_persona_fit(prod_keywords, prod_reviews, prod_topic_labels):
    """
    제품의 키워드/리뷰/토픽라벨을 기반으로 페르소나 적합도 점수 계산 (Hybrid)
    """
    scores = []
    
    # 텍스트 통합 (키워드 + 리뷰 + 토픽라벨)
    full_text_blob = " ".join(prod_keywords) + " " + " ".join(prod_reviews[:5]) + " " + " ".join(prod_topic_labels * 2)
    
    # Metadata Only Blob (for Negative Constraints) - 리뷰 노이즈 배제
    meta_blob = " ".join(prod_keywords) + " " + " ".join(prod_topic_labels)

    for persona, meta in PERSONAS.items():
        score = 0
        hits = []
        
        # [Constraint Check 1] Mandatory Keywords
        # 만약 Mandatory가 정의되어 있는데 하나도 없으면 Skip
        constraints = PERSONA_CONSTRAINTS.get(persona)
        # [Constraint Check 1] Mandatory Keywords (Complex Logic)
        constraints = PERSONA_CONSTRAINTS.get(persona, {})
        
        # 1-1. Regular Mandatory (OR logic) - For Anti-Aging or others
        if constraints.get("mandatory"):
            if not any(kw in full_text_blob for kw in constraints["mandatory"]):
                continue
            hits.append("[Bonus]Mandatory")
            score += 3.0
            
        # 1-2. Gated Mandatory (OR logic for Gate) - For Lazy
        if constraints.get("mandatory_gate"):
            if not any(kw in full_text_blob for kw in constraints["mandatory_gate"]):
                continue
            # Note: Gated ones don't necessarily get +3.0 unless specified.
            # User said "Optional bonus ... don't gate". 
            # If we want to boost Lazy if they have gate, we can.
            # Let's apply boost if gate satisfied to help it compete.
            hits.append("[Bonus]GateAvg") 
            score += 3.0

        # 1-3. Grouped Mandatory (AND logic for Groups) - For Vegan
        if constraints.get("mandatory_groups"):
            groups_satisfied = True
            for group in constraints["mandatory_groups"]:
                if not any(kw in full_text_blob for kw in group):
                    groups_satisfied = False
                    break
            if not groups_satisfied:
                continue
            hits.append("[Bonus]Grouped")
            score += 3.0

        # [Constraint Check 2] Negative Keywords
        # [Refinement] Negative Check: Exact Match (Safe) OR Substring (Root)
        if constraints.get("negative"):
             is_negative = False
             for n_kw in constraints["negative"]:
                 # Substring check on full metadata (covers compounds like "바디워시")
                 if n_kw in meta_blob: 
                     is_negative = True
                     break
             if is_negative:
                 continue

        # 1. 키워드 매칭
        for kw in meta['keywords']:
            if kw in full_text_blob:
                score += 1
                hits.append(kw)
        
        # 2. [Refinement] 토픽 기반 추가 점수 (토픽 라벨에 페르소나 키워드가 직접 있으면 가산점)
        for topic_label in prod_topic_labels:
            for kw in meta['keywords']:
                if kw in topic_label:
                    score += 0.5 
                    if f"[Topic]{kw}" not in hits:
                        hits.append(f"[Topic]{kw}")
        
        # 3. [Refinement] Value/Price Boost (Only for Lazy & Family) - Iteration 12
        if persona in ["레이지 스킵케어 워킹MZ", "실용파 패밀리·헬스케어 매니저"]:
            if any(v in full_text_blob for v in VALUE_TOKENS):
                 score += 0.5
                 hits.append("[Bonus]Value")

        # Max score normalization
        # 키워드 1개만 매칭되어도(1.0) / 2.5 = 0.4 -> Threshold 0.35 넘김
        # [Refinement] Cap Removed to allow 'Bonus' scores to create Gap
        final_score = score / 2.5 
        
        if final_score > 0.3: # Candidate Threshold
            scores.append({
                "persona": persona,
                "score": round(final_score, 2),
                "why": hits[:5] 
            })
            
    # Sort by score
    scores.sort(key=lambda x: x['score'], reverse=True)
    return scores

def main():
    print("1. Loading Meta Data...")
    try:
        df_meta = pd.read_csv(INPUT_CSV, encoding='utf-8-sig')
    except:
        df_meta = pd.read_csv(INPUT_CSV, encoding='cp949')
        
    # Preprocessing to match logic in topic_modeling.py
    # But wait, we need to map via 'Review' text.
    # Create lookup: ReviewText -> List of {Brand, Product}
    # (Using list because identical text might appear for distinct products)
    
    review_map = defaultdict(list)
    for _, row in df_meta.iterrows():
        if pd.isna(row['Review']):
            continue
        # Use simple string cleanup to maximize match probability
        r_text = str(row['Review']).strip()
        if len(r_text) > 5:
            review_map[r_text].append({
                "Brand": row['Brand'],
                "Product": row['Product'] # User's CSV has 'Product', mapping to 'ProductName' logic
            })
            
    print(f"  - Indexed metadata for {len(review_map)} distinct review texts.")

    # -------------------------------------------------------------
    # 2. Load Topic Results (EFFICACY & PURCHASE)
    # -------------------------------------------------------------
    modes = ['EFFICACY', 'PURCHASE']
    
    # Structure:
    # product_agg[ (brand_id, prod_id) ] = { 
    #   'meta': { ... }, 
    #   'reviews': [], 
    #   'EFFICACY_topics': Counter(),
    #   'PURCHASE_topics': Counter()
    # }
    
    product_agg = defaultdict(lambda: {
        'count': 0,
        'reviews': [],
        'tokens': [], # [Add] 실제 토큰 수집
        'EFFICACY_topics': [],
        'PURCHASE_topics': []
    })
    
    # Store Topic Meta for JSON generation
    all_topic_cards = []
    
    # [Add] Global Token Frequency (for Ratio calculation)
    global_token_counts = Counter()
    
    for mode in modes:
        print(f"2. Processing Mode: {mode}...")
        df_doc, topic_meta = load_topic_data(mode)
        if df_doc is None: continue
        
        # Generate Topic Cards
        for t_id, t_data in topic_meta.items():
            if t_id == -1: continue # Outlier topic skip
            
            card = {
                "doc_type": "topic_card",
                "mode": mode,
                "topic_id": t_id,
                "topic_label": t_data['label'],
                "top_keywords": t_data['keywords'],
            }
            all_topic_cards.append(card)
            
        # Aggregate to Product
        print(f"  - Aggregating {len(df_doc)} documents...")
        for _, row in df_doc.iterrows():
            try:
                r_text = str(row['Review_Raw']).strip()
                tokens_str = str(row['Tokens']).strip() # [Add]
                topic_id = int(row['Topic'])
                
                if topic_id == -1: continue # Skip outliers
                
                # Find matching products
                matched_metas = review_map.get(r_text)
                if not matched_metas:
                    continue
                
                token_list = tokens_str.split()
                
                # [Refinement] Global Freq는 EFFICACY 모드에서만 집계 (배송/가격 노이즈 배제)
                if mode == 'EFFICACY':
                    global_token_counts.update([t for t in token_list if is_valid_derived_token(t)])
                    
            except Exception as e:
                # print(f"Error in row: {e}")
                continue
                
            for meta in matched_metas:
                b_name = meta['Brand']
                p_name = meta['Product']
                b_id = make_brand_id(b_name)
                p_id = make_product_id(b_name, p_name)
                key = (b_id, p_id)
                
                entry = product_agg[key]
                if entry['count'] == 0:
                     entry['brand_name'] = b_name
                     entry['product_name'] = p_name
                
                entry['count'] += 1
                entry[f'{mode}_topics'].append(topic_id)
                
                if len(entry['reviews']) < 20:
                    entry['reviews'].append(r_text)
                    # [Refinement] Harvest Tokens ONLY from EFFICACY mode
                    if mode == 'EFFICACY':
                        entry['tokens'].extend([t for t in token_list if is_valid_derived_token(t)])

    # -------------------------------------------------------------
    # 3. Build Product Cards & Collect Details for Persona Expansion
    # -------------------------------------------------------------
    print("3. Building Product Cards & Analyzing Persona Patterns...")
    product_cards = []
    
    # 페르소나별 토큰 수집 (Tokens)
    persona_token_harvest = defaultdict(Counter)
    
    # [Debug] Sample Harvested Products
    persona_sample_products = defaultdict(list)
    
    # Need global topic maps to resolve IDs to Labels/Keywords
    topic_meta_maps = {}
    for mode in modes:
        _, tm = load_topic_data(mode)
        topic_meta_maps[mode] = tm
        
    for (b_id, p_id), data in tqdm(product_agg.items()):
        
        # Calculate Signals
        signals = {}
        all_keywords = set()
        product_topic_labels = [] # For Hybrid Scoring
        
        for mode in modes:
            t_list = data[f'{mode}_topics']
            if not t_list: 
                signals[mode] = []
                continue
                
            total = len(t_list)
            counts = Counter(t_list)
            
            sig_list = []
            for t_id, cnt in counts.most_common(3): # Top 3 topics per mode
                t_info = topic_meta_maps[mode].get(t_id)
                if not t_info: continue
                
                sig_list.append({
                    "topic_id": t_id,
                    "topic_label": t_info['label'],
                    "keywords": t_info['keywords'][:5],
                    "share": round(cnt / total, 2)
                })
                all_keywords.update(t_info['keywords'][:5])
                product_topic_labels.append(t_info['label'])
            
            signals[mode] = sig_list
            
        # [Refinement] Hybrid Scoring (Keywords + Review + TopicLabels)
        persona_fit = calculate_persona_fit(list(all_keywords), data['reviews'], product_topic_labels)
        
        # [Iteration 3] Strict Harvest Rules (Relaxed in Iteration 4 & 5)
        # Rule: Top1 Score >= 0.35 AND (Top1 - Top2) >= 0.10
        if persona_fit:
            top_fit = persona_fit[0]
            
            should_harvest = False
            
            # 조건 1: 절대 점수 (0.5->0.35)
            if top_fit['score'] >= 0.35:
                # 조건 2: Gap Check (0.1)
                if len(persona_fit) >= 2:
                    second_fit = persona_fit[1]
                    gap = top_fit['score'] - second_fit['score']
                    if gap >= 0.10:
                        should_harvest = True
                else:
                    # 2등이 없으면(=유일한 적합) 무조건 Harvest
                    should_harvest = True
            
            # [DEBUG] Check why specific personas are empty
            if top_fit['persona'] in ["가치소비 클린·비건 뷰티액티비스트", "프리미엄 안티에이징 시커"]:
                # Print sample debug info
                if should_harvest:
                    if len(data['tokens']) < 5:
                        print(f"[DEBUG] {top_fit['persona']} Harvested but low tokens ({len(data['tokens'])}): {data.get('product_name')}")
                else:
                    # Why failed?
                    # pass 
                    print(f"[DEBUG] {top_fit['persona']} Skipped. Score: {top_fit['score']}, Gap: {gap if len(persona_fit)>=2 else 'inf'}")

            if should_harvest:
                 persona_token_harvest[top_fit['persona']].update(data['tokens'])
                 # [Debug] Collect sample products
                 if len(persona_sample_products[top_fit['persona']]) < 5:
                     persona_sample_products[top_fit['persona']].append(data.get('product_name', 'Unknown'))

        # Handle potential NaNs
        brand_str = str(data['brand_name']) if pd.notna(data['brand_name']) else ""
        prod_str = str(data['product_name']) if pd.notna(data['product_name']) else "Unknown Product"
        
        product_card = {
            "doc_type": "product_card",
            "product_id": p_id,
            "brand_id": b_id,
            "product_name": f"{brand_str} {prod_str}".strip(), 
            "brand": brand_str,
            "signals": signals,
            "persona_fit": persona_fit,
            "review_count": data['count'],
            "sample_reviews": data['reviews'][:3] 
        }
        product_cards.append(product_card)
        
    # -------------------------------------------------------------
    # 4. Export
    # -------------------------------------------------------------
    print("4. Generating Persona Cards with Data-Derived Keywords (Distinctive Ratio)...")
    
    persona_cards = []
    
    for p_name, p_meta in PERSONAS.items():
        card = {
            "doc_type": "persona_card",
            "persona": p_name,
            "desc": p_meta['desc'],
            "target_keywords": p_meta['keywords'],
            "derived_keywords": []
        }
        
        # [Refinement] Ratio Logic: Frequency in Persona / (Global Frequency + 1)
        # -> 흔한 단어(피부, 사용)는 점수가 낮아지고, 해당 페르소나 특화 단어는 높아짐
        
        p_counts = persona_token_harvest[p_name]
        # Distinctive Ratio Filter
        distinctive_scores = []
        for token, p_freq in p_counts.items():
            if len(token) < 2: continue # 1글자 제외
            if p_freq < 3: continue # Minimum frequency
            
            # Global Frequency (from Efficacy mode)
            g_freq = global_token_counts.get(token, 0)
            
            # Ratio Calculation
            ratio = p_freq / (g_freq + 20) # Smoothing
            
            # [Refinement] Iteration 12: Penalize Value Tokens to prevent domination
            if token in VALUE_TOKENS:
                ratio *= 0.35
            
            distinctive_scores.append((token, ratio))
        
        # Sort by Ratio
        distinctive_scores.sort(key=lambda x: x[1], reverse=True)
        top_derived = [token for token, score in distinctive_scores[:30]] # Top 30
        card["derived_keywords"] = top_derived
            
        persona_cards.append(card)

    print("5. Exporting JSONL...")
    
    # Product Cards
    with open(f"{OUTPUT_DIR}/product_cards.jsonl", 'w', encoding='utf-8') as f:
        for card in product_cards:
            f.write(json.dumps(card, ensure_ascii=False) + "\n")
            
    # Topic Cards
    with open(f"{OUTPUT_DIR}/topic_cards.jsonl", 'w', encoding='utf-8') as f:
        for card in all_topic_cards:
            f.write(json.dumps(card, ensure_ascii=False) + "\n")
    
    # Persona Cards (Updated)
    with open(f"{OUTPUT_DIR}/persona_cards.jsonl", 'w', encoding='utf-8') as f:
        for card in persona_cards:
            f.write(json.dumps(card, ensure_ascii=False) + "\n")
            
    print(f"✅ DONE! Files saved to {OUTPUT_DIR}")
    print(f"  - Products: {len(product_cards)}")
    print(f"  - Topics: {len(all_topic_cards)}")
    print(f"  - Personas: {len(persona_cards)}")
    
    print(f"  - Personas: {len(persona_cards)}")
    
    # [Debug] Print Total Harvested Tokens per Persona
    print("\n[DEBUG] Harvested Token Analysis:")
    for p in PERSONAS:
        total = sum(persona_token_harvest[p].values())
        unique = len(persona_token_harvest[p])
        print(f"\n>> Persona: {p} (Total {total}, Unique {unique})")
        
        # Print Top 20 Harvested Tokens
        top_tokens = persona_token_harvest[p].most_common(20)
        print(f"   Top Tokens: {[t[0] for t in top_tokens]}")
        
        # Print Sample Products Info
        print(f"   Samples: {persona_sample_products[p][:3]}") # Show top 3 samples
    
    print("\n  - Data-Derived Keywords added to Persona Cards.")

if __name__ == "__main__":
    main()
