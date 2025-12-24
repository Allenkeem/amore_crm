# ... existing code ...
import json
import os
import ast
import pandas as pd
from typing import Dict, Any, List

# Define Paths relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# services/crm_agent/ -> ... -> data/crm_agent/
BACKEND_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../"))

BRAND_VOICE_PATH = os.path.join(BACKEND_ROOT, "data", "crm_agent", "brand_voice_guidelines.json")
ACTION_CYCLE_PATH = os.path.join(BACKEND_ROOT, "data", "crm_agent", "action_cycle_db.json")
PERSONA_CARDS_PATH = os.path.join(BACKEND_ROOT, "data", "crm_agent", "persona_cards.jsonl")
CUSTOMER_DATA_PATH = os.path.join(BACKEND_ROOT, "data", "crm_agent", "customer_data_final.csv")

class DataLoader:
    def __init__(self):
        self.brand_voices = {} # New Structure
        self.action_cycles = []
        self.personas = {}
        self.customers_df = None
        
        self._load_data()
        
    def _load_data(self):
        # 2. Load Action Cycle
        try:
            with open(ACTION_CYCLE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.action_cycles = data.get("marketing_scenarios", [])
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
        # 4. Load Brand Voices
        try:
            with open(BRAND_VOICE_PATH, "r", encoding="utf-8") as f:
                self.brand_voices = json.load(f)
        except Exception as e:
            print(f"[Model-2] Error loading brand_voice_guidelines.json: {e}")

        # 5. Load Customer Data (CSV)
        try:
            if os.path.exists(CUSTOMER_DATA_PATH):
                self.customers_df = pd.read_csv(CUSTOMER_DATA_PATH)
                # Ensure column names are clean (no BOM or whitespace)
                self.customers_df.columns = self.customers_df.columns.str.strip()
            else:
                print(f"[Model-2] Customer data file not found at: {CUSTOMER_DATA_PATH}")
        except Exception as e:
            print(f"[Model-2] Error loading customer_data_final.csv: {e}")

    def get_brand_voice(self, brand_name: str) -> Dict[str, Any]:
        """Find brand voice guideline by brand name."""
        if not brand_name:
            return {}

        # 1. Exact match
        if brand_name in self.brand_voices:
            return self.brand_voices[brand_name]
            
        # 2. Fuzzy match
        for b_name, b_data in self.brand_voices.items():
            if brand_name in b_name or b_name in brand_name:
                return b_data
        
        return {}

    def get_action_info(self, purpose_query: str) -> Dict[str, Any]:
        """Find action cycle info by purpose name or stage."""
        if not purpose_query:
            return {}
            
        # Normalize
        q = purpose_query.lower()
        
        for action in self.action_cycles:
            stage = action.get("stage_name", "").lower()
            goal = action.get("message_goal", "").lower()
            name = action.get("name", "").lower()
            a_id = action.get("id", "").lower()
            
            if q in stage or q in goal or q in name or q == a_id:
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

    def filter_customers_by_target(self, target_suffix: str) -> List[str]:
        """
        Filter customers who have a Target_Code ending with information (e.g., 'WINBACK', 'SPRING').
        User requirement: In Target_Code column, codes are like 'G04_WINBACK', use 'WINBACK' to distinguish.
        Returns a list of customer_ids.
        """
        if self.customers_df is None or self.customers_df.empty:
            return []
            
        if not target_suffix:
            return []
            
        target_upper = target_suffix.upper() # Ensure case-insensitive or standardized comparison if needed
        
        filtered_ids = []
        
        for _, row in self.customers_df.iterrows():
            target_codes_str = row.get("Target_Code", "[]")
            customer_id = row.get("customer_id")
            
            if not isinstance(target_codes_str, str):
                continue
                
            try:
                # Parse string representation of list "['A', 'B']"
                codes_list = ast.literal_eval(target_codes_str)
                if not isinstance(codes_list, list):
                    continue
                
                # Check if any code matches the suffix logic
                # logic: code string split by '_' and last part matches target_upper? 
                # OR code ends with f"_{target_upper}"
                
                match = False
                for code in codes_list:
                    # Example code: 'G04_WINBACK'
                    # Split by '_' -> ['G04', 'WINBACK']
                    if "_" in code:
                        parts = code.split("_")
                        if len(parts) > 1 and parts[-1] == target_upper:
                            match = True
                            break
                
                if match:
                    filtered_ids.append(customer_id)
                    
            except (ValueError, SyntaxError):
                continue
                
        return filtered_ids

# Singleton instance
_loader_instance = None
def get_data_loader():
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = DataLoader()
    return _loader_instance
