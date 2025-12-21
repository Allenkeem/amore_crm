import os
import pandas as pd
import json
from openai import OpenAI
from dotenv import load_dotenv
import concurrent.futures
from tqdm import tqdm
import time

# 환경변수 로드 (.env)
load_dotenv()

# 설정
INPUT_FILE = "../data/targets_with_news.xlsx"
OUTPUT_FILE = "../data/structured_data.json"
MODEL = "gpt-4o-mini"
MAX_WORKERS = 10  # 병렬 처리 개수 (API Rate Limit 고려)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def clean_text(text):
    if pd.isna(text):
        return ""
    return str(text).strip()

def process_with_llm(row_idx, brand, product, url, raw_text):
    prompt = f"""
    당신은 전문 CRM 마케터입니다.
    제품 정보와 원문 텍스트를 분석하여 RAG 시스템용 JSON 데이터를 생성하세요.

    [제약 사항]
    1. **Target Persona**: 반드시 아래 5가지 페르소나 중 제품과 가장 관련성 높은 1~2개만 선택하세요. (임의 생성 금지)
       - 혜택 중시형 (가격, 할인, 증정 민감)
       - 성분 확인형 (원료, 비건, 유해성분 민감)
       - 효능 중시형 (임상 결과, 기능성, 효과 민감)
       - 리뷰 신뢰형 (체험단, 입소문, 랭킹 민감)
       - 트렌드 세터 (신상, 한정판, 콜라보 민감)
    
    2. **Review**: 뉴스룸 데이터에는 실제 고객 리뷰가 없으므로, **절대로 가상의 리뷰를 생성하지 마세요.**
    
    [제품] {brand} {product} ({url})
    [원문] {raw_text[:3000]}

    [출력 포맷 (JSON Only)]
    {{
      "id": "{brand}_{product}_{row_idx}",
      "metadata": {{ "brand": "{brand}", "product_name": "{product}", "url": "{url}" }},
      "search_context": {{
        "summary": "핵심 요약 (3문장)",
        "keywords": ["키워드1", "키워드2", "키워드3"],
        "target_persona": ["선택한_페르소나1"]
      }},
      "content_details": {{
        "key_specs": "용량/가격/성분 등 스펙",
        "marketing_copy": ["카피1", "카피2"]
      }}
    }}
    """
    
    retries = 3
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "Output JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2) # 재시도 대기
                continue
            print(f"Failed row {row_idx}: {e}")
            return None

def process_row_wrapper(args):
    """
    병렬 처리를 위한 래퍼 함수
    args: (idx, row) 튜플
    """
    idx, row = args
    clean_desc = clean_text(row['Newsroom_Desc'])
    
    if not clean_desc or len(clean_desc) < 50:
        return None

    return process_with_llm(
        row_idx=idx,
        brand=row['Brand'],
        product=row['Product_Name'],
        url=row['URL'],
        raw_text=clean_desc
    )

def main():
    print(f"Loading {INPUT_FILE}...")
    df = pd.read_excel(INPUT_FILE)
    
    # 데이터 준비
    data_to_process = []
    for idx, row in df.iterrows():
        data_to_process.append((idx, row))
        
    print(f"Starting parallel processing for {len(data_to_process)} items with {MAX_WORKERS} workers...")
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # tqdm으로 진행률 표시
        futures = {executor.submit(process_row_wrapper, item): item for item in data_to_process}
        
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(data_to_process)):
            res = future.result()
            if res:
                results.append(res)
                
    print(f"Processing complete. Saving {len(results)} items to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("Done!")

if __name__ == "__main__":
    main()
