import json
import os
from typing import Dict, Any, List

# Define Paths relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# services/crm_agent/ -> ... -> data/crm_agent/
BACKEND_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../"))

BRAND_TONE_PATH = os.path.join(BACKEND_ROOT, "data", "crm_agent", "brand_tone_db.json")
ACTION_CYCLE_PATH = os.path.join(BACKEND_ROOT, "data", "crm_agent", "action_cycle_db.json")
PERSONA_CARDS_PATH = os.path.join(BACKEND_ROOT, "data", "crm_agent", "persona_cards.jsonl")

class DataLoader:
    def __init__(self):
        self.brand_tones = {}
        self.action_cycles = []
        self.personas = {}
        
        self._load_data()
        
    def _load_data(self):
        # 1. Load Brand Tone
        try:
            with open(BRAND_TONE_PATH, "r", encoding="utf-8") as f:
                self.brand_tones = json.load(f)
        except Exception as e:
            print(f"[Model-2] Error loading brand_tone_db: {e}")
            
        # 2. Load Action Cycle
        try:
            with open(ACTION_CYCLE_PATH, "r", encoding="utf-8") as f:
                self.action_cycles = json.load(f)
        except Exception as e:
            print(f"[Model-2] Error loading action_cycle_db: {e}")
            
        # 3. Load Personas (JSONL)
        try:
            with open(PERSONA_CARDS_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    p = json.loads(line)
                    # Use persona name as key
                    if "persona" in p:
                        self.personas[p["persona"]] = p
        except Exception as e:
            print(f"[Model-2] Error loading persona_cards.jsonl: {e}")
            
    def get_brand_tone(self, brand_name: str) -> Dict[str, Any]:
        """Find tone by brand name (fuzzy match)."""
        # 1. Direct key match
        if brand_name in self.brand_tones:
            return self.brand_tones[brand_name]
            
        # 2. Search in values (brand_name field)
        for key, info in self.brand_tones.items():
            db_name = info.get("brand_name", "")
            if brand_name.lower() in db_name.lower() or db_name.lower() in brand_name.lower():
                return info
                
        # 3. Return General/Default if exists, else empty
        return self.brand_tones.get("general", {})

    def get_action_info(self, purpose_query: str) -> Dict[str, Any]:
        """Find action cycle info by purpose name or stage."""
        if not purpose_query:
            return {}
            
        # Normalize
        q = purpose_query.lower()
        
        for action in self.action_cycles:
            stage = action.get("stage_name", "").lower()
            goal = action.get("message_goal", "").lower()
            
            if q in stage or q in goal:
                return action
        
        # Default: return a dummy structure if not found
        return {
            "stage_name": purpose_query,
            "message_goal": purpose_query,
            "strategy": "고객의 니즈에 맞춰 친절하게 응대",
            "example_templates": []
        }
        
    def get_persona_info(self, persona_name: str) -> Dict[str, Any]:
        """Get full persona card context."""
        if not persona_name:
            return {}
            
        # 1. Exact match
        if persona_name in self.personas:
            return self.personas[persona_name]
            
        # 2. Fuzzy match
        for p_name, p_data in self.personas.items():
            if persona_name in p_name or p_name in persona_name:
                return p_data
                
        return {}

# Singleton instance
_loader_instance = None
def get_data_loader():
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = DataLoader()
    return _loader_instance
