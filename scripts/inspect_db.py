import chromadb
from chromadb.utils import embedding_functions
import json
import os

# 설정
# 설정
DB_PATH = "../data/chroma_db"
COLLECTION_NAME = "amore_news_collection"
MODEL_NAME = "jhgan/ko-sbert-nli"
OUTPUT_FILE = "../data/rag_db_dump.json"

def dump_db():
    print(f"Connecting to DB at {DB_PATH}...")
    client = chromadb.PersistentClient(path=DB_PATH)
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)
    
    try:
        collection = client.get_collection(name=COLLECTION_NAME, embedding_function=sentence_transformer_ef)
    except Exception as e:
        print(f"Error loading collection: {e}")
        return

    # 모든 데이터 가져오기
    # ChromaDB get() without arguments returns all data (limit might apply, but usually gets all)
    result = collection.get()
    
    if not result['ids']:
        print("DB is empty.")
        return

    print(f"Found {len(result['ids'])} documents.")
    
    dump_data = []
    for i in range(len(result['ids'])):
        item = {
            "id": result['ids'][i],
            "metadata": result['metadatas'][i],
            "content": result['documents'][i],
            # embeddings are not returned by default in get() unless include=['embeddings'] is specified
            # We skip embeddings for the JSON dump to keep it readable, unless requested.
        }
        dump_data.append(item)
        
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(dump_data, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully dumped DB content to {os.path.abspath(OUTPUT_FILE)}")

if __name__ == "__main__":
    dump_db()
