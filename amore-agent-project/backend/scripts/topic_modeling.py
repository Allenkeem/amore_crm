import pandas as pd
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
from kiwipiepy import Kiwi
from umap import UMAP
from sentence_transformers import SentenceTransformer
import os
import time
from tqdm import tqdm
import numpy as np
import hashlib
import re

# ==================================================================================
# [설정 및 상수 정의]
# ==================================================================================
INPUT_FILE = "../../data_crawl/FINAL_RESULT.csv"
OUTPUT_DIR_ROOT = "../data/topic_model_results"

# 1. 기본 불용어 (공통)
STOPWORDS_COMMON = {
    '제품', '구매', '사용', '진짜', '완전', '너무', '정말', '것', '수', '저', '이', '거', 
    '상품', '주문', '도착', '생각', '사람', '마음', '준비', '기간', '정도', '느낌',
    '오늘', '이번', '역시', '항상', '때문', '부분', '근데', '하지만', '그리고'
}

# 2. 브랜드 블랙리스트 (공통)
BRANDS = {
    "설화수", "마몽드", "에스쁘아", "아이오페", "해피바스", "라네즈", "프리메라", "헤라", "일리윤", "한율", "미쟝센", "려", "바이탈뷰티",
    "sulwhasoo", "mamonde", "espoir", "iope", "happybath", "laneige", "primera", "hera", "illiyoon", "hanyul", "miseenscene", "ryo", "vitalbeauty"
}
BRANDS |= {b.lower() for b in BRANDS}

# 3. 메타/평가 불용어 (효능 모드용: 구매/감탄/배송 관련 제거)
STOPWORDS_META = {
    "배송", "포장", "사은품", "추천", "최고", "재구매", "만족", "별로", "강추", "비추", 
    "선물", "쿠폰", "가격", "행사", "세일", "박스", "택배", "기사", "도착", "빠름"
}

# 4. 효능 관련 SL(영어) 화이트리스트 (효능 모드용)
EFFICACY_SL_WHITELIST = {
    "SPF","PA","UVA","UVB","UV","AHA","BHA","PHA","CICA","TECA","PH",
    "RETINOL","NIACINAMIDE","CERAMIDE","HA","HYA","VITAMIN","COLLAGEN",
    "PANTHENOL","TEA","TREE","MUGWORT"
}
EFFICACY_SL_WHITELIST |= {w.lower() for w in EFFICACY_SL_WHITELIST}

# ==================================================================================
# [Helper Functions]
# ==================================================================================

def compute_data_fingerprint(docs):
    """
    데이터 지문 생성 (검증 강화: 샘플 증가 + 앞뒤 내용 사용)
    """
    if not docs:
        return "empty"
    n = len(docs)
    # 샘플 50개 추출
    sample_indices = np.linspace(0, n - 1, num=min(50, n), dtype=int)
    
    signature_str = f"{n}"
    for idx in sample_indices:
        # 앞 50자 + 뒤 50자 사용하여 중간 내용 변경 감지 강화
        d_str = str(docs[idx])
        signature_str += f"|{d_str[:50]}|{d_str[-50:]}"
        
    return hashlib.md5(signature_str.encode('utf-8')).hexdigest()

def pre_tokenize(texts, mode='EFFICACY'):
    """
    Kiwi 토큰화 (모드별 차별화)
    - mode='EFFICACY': 효능/사용감 중심. SL 화이트리스트 적용, 메타어 제거.
    - mode='PURCHASE': 구매패턴/라이프스타일 포함. SL 허용폭 넓음.
    """
    kiwi = Kiwi(num_workers=4)
    print(f"🚀 Pre-tokenizing Reviews (Mode: {mode})...")
    
    tokenized_docs = []
    
    # 정규식 패턴 (fullmatch용 ^...$)
    # 한글 2글자 이상 OR 영문/숫자 2글자 이상
    # (효능 모드에서는 SL Whitelist로 2차 검증하므로 여기선 Broad하게 잡음)
    valid_pattern = re.compile(r'^(?:[가-힣]{2,}|[a-zA-Z0-9]{2,})$')
    
    # 모드별 불용어 설정
    if mode == 'EFFICACY':
        final_stopwords = STOPWORDS_COMMON | STOPWORDS_META
    else: # PURCHASE
        final_stopwords = STOPWORDS_COMMON 
        # PURCHASE 모드에서는 '배송/선물/가격' 등은 살림
    
    for res in tqdm(kiwi.analyze(texts), total=len(texts)):
        tokens = []
        try:
            if res and res[0] and res[0][0]:
                for token, pos, _, _ in res[0][0]:
                    
                    # 1. 브랜드 필터 (공통)
                    if token.lower() in BRANDS:
                        continue
                        
                    # 2. 기본 패턴 확인 (길이/형식)
                    # 효능 모드라도 '한글 1글자'는 보통 무의미 (향, 톤 등은 문맥 없이 잡기 힘듦. 필요시 예외처리)
                    if not valid_pattern.fullmatch(token):
                         continue
                         
                    # 3. 불용어 확인
                    if token in final_stopwords:
                        continue
                        
                    # 4. 품사별 로직
                    if pos in ['NNG', 'NNP', 'VA', 'SL']:
                        # 형용사 원복
                        word = token + '다' if pos == 'VA' else token
                        
                        # [EFFICACY 모드 특화] SL(영어) 화이트리스트 적용
                        if mode == 'EFFICACY' and pos == 'SL':
                            if word.lower() not in EFFICACY_SL_WHITELIST:
                                continue
                        
                        tokens.append(word)
        except Exception:
            pass
        
        tokenized_docs.append(" ".join(tokens))
        
    return tokenized_docs

def run_analysis(docs, mode='EFFICACY'):
    """
    분석 파이프라인 실행 로직
    """
    output_dir = f"{OUTPUT_DIR_ROOT}/{mode}"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n[{mode} Mode] Starting Analysis...")
    
    # 1. 토큰화
    print(f"  - Tokenizing...")
    pre_tokenized_docs = pre_tokenize(docs, mode=mode)
    
    # 2. 빈 문서 필터링
    print(f"  - Filtering empty documents...")
    valid_indices = [i for i, t in enumerate(pre_tokenized_docs) if t.strip()]
    
    filtered_docs = [docs[i] for i in valid_indices]
    filtered_tokens = [pre_tokenized_docs[i] for i in valid_indices]
    
    print(f"  - Removed {len(docs) - len(filtered_docs)} empty docs. Count: {len(filtered_docs)}")
    
    if len(filtered_docs) < 10:
        print("  ! Not enough data to proceed.")
        return

    # 3. 임베딩 (캐시 관리)
    # 모드별로 임베딩을 공유할 수도 있지만, filtered_docs가 다를 수 있으므로 별도 관리 권장 
    # 혹은 'filtered_docs' 내용 기반 hash로 관리
    
    emb_file = f"{output_dir}/embeddings.npy"
    hash_file = f"{output_dir}/embeddings_hash.txt"
    
    current_hash = compute_data_fingerprint(filtered_docs)
    embeddings = None
    embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    
    if os.path.exists(emb_file) and os.path.exists(hash_file):
        with open(hash_file, 'r') as f:
            saved_hash = f.read().strip()
        if saved_hash == current_hash:
            try:
                cached_emb = np.load(emb_file)
                if len(cached_emb) == len(filtered_docs):
                    embeddings = cached_emb
                    print("  - Cache Hit! Loaded embeddings.")
            except:
                pass
                
    if embeddings is None:
        print("  - Calculating embeddings...")
        embeddings = embedding_model.encode(
            filtered_docs, 
            show_progress_bar=True, 
            batch_size=64, 
            normalize_embeddings=True
        )
        np.save(emb_file, embeddings)
        with open(hash_file, 'w') as f:
            f.write(current_hash)
            
    # 4. BERTopic
    print("  - Fitting BERTopic...")
    # 모드별 파라미터 미세 조정 가능
    min_topic_s = 30 if mode == 'EFFICACY' else 50
    
    vectorizer_model = CountVectorizer(
        tokenizer=None, preprocessor=None, analyzer='word',
        min_df=10, max_df=0.9, ngram_range=(1, 1), max_features=15000
    )
    
    umap_model = UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric='cosine', random_state=42)
    
    topic_model = BERTopic(
        embedding_model=embedding_model,
        vectorizer_model=vectorizer_model,
        umap_model=umap_model,
        calculate_probabilities=False,
        min_topic_size=min_topic_s,
        verbose=True
    )
    
    topics, probs = topic_model.fit_transform(filtered_tokens, embeddings)
    
    # 5. 저장
    print(f"  - Saving results to {output_dir}...")
    topic_model.get_topic_info().to_csv(f"{output_dir}/topic_info.csv", index=False, encoding='utf-8-sig')
    
    # Doc Info Map
    doc_info = topic_model.get_document_info(filtered_tokens)
    doc_info['Review_Raw'] = filtered_docs
    doc_info = doc_info[['Topic', 'Review_Raw', 'Document', 'Representative_document']]
    doc_info.rename(columns={'Document':'Tokens'}, inplace=True)
    doc_info.to_csv(f"{output_dir}/document_topics.csv", index=False, encoding='utf-8-sig')
    
    # Rep Docs
    if 'Representative_document' in doc_info.columns:
        rep = doc_info[doc_info['Representative_document'] == True].copy()
        rep.to_csv(f"{output_dir}/topic_representative_reviews.csv", index=False, encoding='utf-8-sig')
        
    # Viz
    font_family = "Malgun Gothic"
    try:
        fig = topic_model.visualize_barchart(top_n_topics=15)
        fig.update_layout(font=dict(family=font_family))
        fig.write_html(f"{output_dir}/topics_barchart.html")
    except:
        pass

def main():
    print("\n[Step 1] Loading Data...")
    try:
        df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')
    except UnicodeDecodeError:
        df = pd.read_csv(INPUT_FILE, encoding='cp949')
        
    if 'Review' not in df.columns:
        return

    docs = df['Review'].dropna().tolist()
    docs = [str(doc) for doc in docs if len(str(doc)) > 5]
    print(f"Valid docs: {len(docs)}")
    
    # ---------------------------------------------------------
    # Dual Mode Execution
    # ---------------------------------------------------------
    # Mode 1: 효능/사용감 중심 (EFFICACY)
    # - 메타어(배송/추천) 제거
    # - 영어(SL)는 Whitelist(성분/기능)만 허용
    run_analysis(docs, mode='EFFICACY')
    
    # Mode 2: 구매패턴/라이프스타일 중심 (PURCHASE)
    # - 메타어(선물/가격/엄마 등) 허용
    # - 영어(SL) 허용
    # - 토픽 사이즈 좀 더 크게 잡음
    run_analysis(docs, mode='PURCHASE')
    
    print("\n✅ All Dual-Mode Analyses Complete!")

if __name__ == "__main__":
    main()
