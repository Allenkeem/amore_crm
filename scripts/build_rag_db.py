import chromadb
from chromadb.utils import embedding_functions
import json
import os

# 설정
INPUT_FILE = "../data/structured_data.json"
DB_PATH = "../data/chroma_db"
COLLECTION_NAME = "amore_news_collection"
MODEL_NAME = "jhgan/ko-sbert-nli"

def main():
    print(f"Loading data from {INPUT_FILE}...")
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found. Please run structure_data.py first.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Loaded {len(data)} items.")

    # ChromaDB 초기화
    print(f"Initializing ChromaDB at {DB_PATH}...")
    client = chromadb.PersistentClient(path=DB_PATH)
    
    # 임베딩 함수 설정 (Sentence-BERT)
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)
    
    # 컬렉션 생성 (이미 존재하면 로드)
    # 기존 데이터가 있을 수 있으므로 reset 하거나 지우고 다시 만드는 것이 깔끔함 (개발 단계)
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"Deleted existing collection '{COLLECTION_NAME}'")
    except:
        pass

    collection = client.create_collection(name=COLLECTION_NAME, embedding_function=sentence_transformer_ef)
    
    ids = []
    documents = []
    metadatas = []

    print("Preparing data for ingestion...")
    for item in data:
        # 1. ID
        doc_id = item['id']
        
        # 2. Document (Embedding 대상)
        # search_context의 summary와 keywords를 합쳐서 검색 텍스트로 사용
        context = item['search_context']
        # Persona는 검색 텍스트에 넣을지 메타데이터에 넣을지 결정해야 함. 
        # 여기서는 검색 텍스트에 포함시켜 의미적 검색이 되도록 함. ('30대 직장인' 검색 시 매칭되도록)
        search_text = f"요약: {context.get('summary', '')}\n"
        search_text += f"키워드: {', '.join(context.get('keywords', []))}\n"
        search_text += f"타겟: {', '.join(context.get('target_persona', []))}"
        
        # 3. Metadata
        # content_details (전체 JSON)를 문자열로 변환하여 메타데이터에 저장 (Retrieval 후 LLM 제공용)
        meta = item['metadata'].copy()
        meta['content_details_json'] = json.dumps(item['content_details'], ensure_ascii=False)
        # 필요한 경우 search_context도 메타데이터에 저장 가능
        meta['search_context_json'] = json.dumps(item['search_context'], ensure_ascii=False)

        ids.append(doc_id)
        documents.append(search_text)
        metadatas.append(meta)

    # 배치 처리 (ChromaDB 권장)
    batch_size = 100
    total_docs = len(ids)
    print(f"Upserting {total_docs} documents into ChromaDB...")
    
    for i in range(0, total_docs, batch_size):
        end_idx = min(i + batch_size, total_docs)
        print(f"  Processing batch {i} to {end_idx}...")
        collection.upsert(
            ids=ids[i:end_idx],
            documents=documents[i:end_idx],
            metadatas=metadatas[i:end_idx]
        )
        
    print("Database construction completed!")

if __name__ == "__main__":
    main()
