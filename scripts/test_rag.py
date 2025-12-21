import chromadb
from chromadb.utils import embedding_functions
import argparse
import json

# 설정
DB_PATH = "../data/chroma_db"
COLLECTION_NAME = "amore_news_collection"
MODEL_NAME = "jhgan/ko-sbert-nli"

def query_db(query_text, n_results=3):
    client = chromadb.PersistentClient(path=DB_PATH)
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)
    collection = client.get_collection(name=COLLECTION_NAME, embedding_function=sentence_transformer_ef)
    
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    return results

def print_results(results):
    for i, doc in enumerate(results['documents'][0]):
        meta = results['metadatas'][0][i]
        dist = results['distances'][0][i]
        doc_id = results['ids'][0][i]
        
        print(f"[{i+1}] ID: {doc_id} (Dist: {dist:.4f})")
        print(f"    Brand: {meta['brand']}, Product: {meta['product_name']}")
        
        # content_details_json 파싱
        try:
            details = json.loads(meta['content_details_json'])
            print(f"    [Specs]: {details.get('key_specs', '')}")
            
            # 마케팅 카피 1개만 예시로 출력
            copy_list = details.get('marketing_copy', [])
            if copy_list:
                print(f"    [Copy]: {copy_list[0]}")
        except:
            print("    [Details]: JSON parsing failed or not found.")

        print(f"    [Search Context]: {doc[:100]}...") # 검색에 사용된 텍스트 일부
        print("-" * 30)

def test_synonyms():
    print("=== 한국어 의미론적 유사성 검증 (Synonym Test) ===")
    
    query1 = "지성 피부에 좋다"
    query2 = "지성 피부에 좋고"
    
    print(f"\nQuery 1: '{query1}'")
    results1 = query_db(query1, n_results=1)
    print_results(results1)
    
    print(f"\nQuery 2: '{query2}'")
    results2 = query_db(query2, n_results=1)
    print_results(results2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-synonyms", action="store_true", help="Run synonym/semantic similarity test")
    parser.add_argument("--query", type=str, default="30대 직장인 주름 개선 화장품", help="Query string for testing")
    args = parser.parse_args()
    
    if args.test_synonyms:
        test_synonyms()
    else:
        print(f"Querying for: '{args.query}'")
        results = query_db(args.query)
        print_results(results)
