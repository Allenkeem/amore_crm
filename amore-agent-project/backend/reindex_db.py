import json
import os
from pathlib import Path
from services.regulation_agent.retrieval import RetrievalEngine
from services.regulation_agent.config import SPAM_DB_PATH, COSMETICS_DB_PATH

# Define new paths for local DBs
DATA_DIR = Path(SPAM_DB_PATH).parent
LOCAL_SPAM_DB_PATH = DATA_DIR / "불법스팸_방지_안내서_임베딩_local.json"
LOCAL_COSMETICS_DB_PATH = DATA_DIR / "화장품_지침_임베딩_local.json"

def reindex_db(original_path, new_path, engine):
    print(f"Re-indexing {original_path} -> {new_path}...")
    
    if not os.path.exists(original_path):
        print(f"Error: {original_path} not found.")
        return

    with open(original_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    new_data = []
    total = len(data)
    
    for i, item in enumerate(data):
        # Extract content to re-embed. 
        # Usually checking metadata['content'] or if the text was stored elsewhere.
        # Based on previous code: doc['metadata']['content']
        content = item['metadata'].get('content', '')
        if not content:
            print(f"Skipping item {i}: No content found.")
            continue
            
        # Generate new embedding using Local Model (768 dims)
        new_embedding = engine.get_embedding(content)
        
        new_item = {
            "metadata": item['metadata'],
            "embedding": new_embedding
        }
        new_data.append(new_item)
        
        if (i+1) % 5 == 0:
            print(f"Processed {i+1}/{total}")
            
    with open(new_path, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
        
    print(f"Saved {len(new_data)} items to {new_path}")

def main():
    engine = RetrievalEngine()
    
    # Reindex Spam DB
    reindex_db(SPAM_DB_PATH, LOCAL_SPAM_DB_PATH, engine)
    
    # Reindex Cosmetics DB
    reindex_db(COSMETICS_DB_PATH, LOCAL_COSMETICS_DB_PATH, engine)
    
    print("\nRe-indexing Complete. Please update config.py to point to the created *_local.json files.")

if __name__ == "__main__":
    main()
