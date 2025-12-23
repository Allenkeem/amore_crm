import json
import os
from .config import SPAM_DB_PATH, COSMETICS_DB_PATH

def load_json_db(path):
    if not os.path.exists(path):
        print(f"Warning: {path} not found.")
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_regulation_dbs():
    """
    Load both Spam and Cosmetics vector databases.
    Returns:
        tuple: (spam_db, cosmetics_db)
    """
    spam_db = load_json_db(SPAM_DB_PATH)
    cosmetics_db = load_json_db(COSMETICS_DB_PATH)
    
    print(f"[RegulationAgent] Loaded Spam DB: {len(spam_db)} chunks")
    print(f"[RegulationAgent] Loaded Cosmetics DB: {len(cosmetics_db)} chunks")
    
    return spam_db, cosmetics_db
