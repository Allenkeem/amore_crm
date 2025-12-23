import json
from typing import Dict, Any, List
from utils.llm_factory import get_llm_client
from .data_loader import get_data_loader

class IntentParser:
    def __init__(self):
        self.llm = get_llm_client()
        self.loader = get_data_loader()
        
    def parse_query(self, user_text: str) -> Dict[str, Any]:
        """
        Uses LLM to classify the user's intent into one of the Action IDs 
        defined in action_cycle_db.json.
        """
        
        # 1. Prepare Action Candidates (ID + Description)
        # We use the 'matching_description' field for accuracy.
        candidates_text = ""
        for action in self.loader.action_cycles:
            a_id = action.get("id", "UNKNOWN")
            desc = action.get("matching_description", action.get("name", ""))
            candidates_text += f"- [{a_id}]: {desc}\n"
            
        # 2. Build Prompt for Classification
        prompt = f"""
[TASK]
Classify the USER REQUEST into exactly one of the provided Action IDs.
Choose the ID whose description best matches the user's intent.
If the request implies a specific season (spring/summer/autumn/winter), ensure you pick the corresponding seasonal ID (e.g., G05_WINTER).

[ACTION ID LIST]
{candidates_text}

[USER REQUEST]
"{user_text}"

[OUTPUT FORMAT]
Return ONLY a JSON object in this format:
{{
    "selected_id": "ONE_OF_THE_IDS" or "NONE",
    "reason": "Short explanation why"
}}
"""

        # 3. Call LLM
        try:
            raw_response = self.llm.generate(prompt)
            # Basic cleaning for JSON parsing
            clean_json = raw_response.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean_json)
            
            selected_id = parsed.get("selected_id")
            
            # Verify if ID exists in our DB
            valid_ids = [a["id"] for a in self.loader.action_cycles]
            if selected_id not in valid_ids and selected_id != "NONE":
                # If invalid ID returned, treat as NONE (safe fail)
                selected_id = "NONE"

            return {
                "original_query": user_text,
                "selected_id": selected_id, # Can be "NONE"
                "reason": parsed.get("reason", "")
            }

        except Exception as e:
            print(f"[IntentParser] Error parsing query: {e}")
            # Fallback on error
            return {
                "original_query": user_text,
                "selected_id": "NONE",
                "error": str(e)
            }

# Singleton
_parser_instance = None
def get_intent_parser():
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = IntentParser()
    return _parser_instance
