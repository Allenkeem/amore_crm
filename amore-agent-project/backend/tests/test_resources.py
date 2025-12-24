import os
import json
import pytest
from services.product_agent.config import PRODUCT_CARDS_PATH, NEWS_CARDS_PATH, TOPIC_CARDS_PATH, PERSONA_CARDS_PATH
from services.crm_agent.data_loader import BRAND_VOICE_PATH, ACTION_CYCLE_PATH

# Maps file paths to their expected format (json or jsonl)
DATA_FILES = [
    (PRODUCT_CARDS_PATH, "jsonl"),
    (NEWS_CARDS_PATH, "jsonl"),
    (TOPIC_CARDS_PATH, "jsonl"),
    (PERSONA_CARDS_PATH, "jsonl"), # This is from product_agent config
    (BRAND_VOICE_PATH, "json"),
    (ACTION_CYCLE_PATH, "json"),
]

def test_data_files_exist():
    """Verify all data files exist."""
    print("\n[Resource Check] Checking file existence...")
    missing_files = []
    for path, fmt in DATA_FILES:
        exists = os.path.exists(path)
        status = "✅ Found" if exists else "❌ Missing"
        print(f"{status}: {path}")
        if not exists:
            missing_files.append(path)
    
    assert not missing_files, f"Missing data files: {missing_files}"

def test_data_files_validity():
    """Verify data files are valid JSON/JSONL."""
    print("\n[Resource Check] Validating file content...")
    
    for path, fmt in DATA_FILES:
        if not os.path.exists(path):
            continue 
            
        print(f"Validating {os.path.basename(path)} ({fmt})...")
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                if fmt == "json":
                    data = json.load(f)
                    assert isinstance(data, (dict, list)), "JSON root must be dict or list"
                    print(f"  -> Valid JSON. Item count/Keys: {len(data)}")
                elif fmt == "jsonl":
                    count = 0
                    for line in f:
                        if line.strip():
                            json.loads(line)
                            count += 1
                    print(f"  -> Valid JSONL. Line count: {count}")
                    
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in {path}: {e}")
        except Exception as e:
            pytest.fail(f"Error reading {path}: {e}")
