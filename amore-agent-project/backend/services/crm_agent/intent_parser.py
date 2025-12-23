import json
from typing import List, Dict, Any
from utils.llm_factory import get_llm_client
from .data_loader import get_data_loader
from difflib import get_close_matches

class IntentParser:
    def __init__(self):
        self.llm = get_llm_client()
        self.loader = get_data_loader()
        
    def parse_query(self, user_text: str) -> Dict[str, Any]:
        """
        1. LLM Extraction: Extract target search terms.
        2. Candidate Matching: Find Top matches in DB.
        """
        
        # 1. Prepare Persona List for Context
        persona_context = "\n".join([f"- {name}: {pd.get('desc', '')}" for name, pd in self.loader.personas.items()])
        
        # 2. LLM Extraction & Matching
        prompt = f"""
        [ROLE]
        You are a smart extractor. Your task is to extract 'product', 'selected_persona', and 'purpose' from the User Request.

        [Persona Candidates]
        {persona_context}

        [User Request]
        "{user_text}"

        [Output Format]
        Return ONLY valid JSON. No explanations.
        {{
            "product": "Extract specific product name (or 'None' if not found)",
            "selected_persona": "Exact Persona Name from the list above (or 'None')",
            "purpose": "Marketing Goal (e.g. Purchase, Repurchase, Review)"
        }}
        """
        
        raw_json = self.llm.generate(prompt)
        print(f"[IntentParser] Raw LLM Output: {raw_json}") # Debug log
        
        # Robust Cleaning for Llama 3.1
        try:
            # Try to find JSON block
            if "```json" in raw_json:
                raw_json = raw_json.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_json:
                raw_json = raw_json.split("```")[1].split("```")[0].strip()
            # Try finding first { and last }
            else:
                p1 = raw_json.find("{")
                p2 = raw_json.rfind("}")
                if p1 != -1 and p2 != -1:
                    raw_json = raw_json[p1:p2+1]
            
            extracted = json.loads(raw_json)
        except Exception as e:
            print(f"[IntentParser] JSON Parse Error: {e}")
            # Fallback: Treat whole text as product if short, else fail
            product_guess = user_text if len(user_text) < 20 else "None"
            extracted = {"product": product_guess, "selected_persona": None, "purpose": "General"}
            
        # 3. Use LLM Selection
        selected_persona = extracted.get("selected_persona")
        top_k_personas = []
        
        if selected_persona and selected_persona in self.loader.personas:
            top_k_personas = [selected_persona]
            # Add scores for UI (Mock score)
            extracted["persona"] = selected_persona # For display
        else:
            # Fallback to fuzzy if LLM failed
            persona_query = extracted.get("persona") or user_text
            fuzzy = get_close_matches(persona_query, list(self.loader.personas.keys()), n=3, cutoff=0.4)
            top_k_personas = fuzzy
        
        if not top_k_personas:
             top_k_personas =  all_personas[:3] # Fallback to default list

        # 3. Find Candidates (Purpose)
        purpose_query = extracted.get("purpose") or ""
        all_actions = [a.get("stage_name", "Unknown") for a in self.loader.action_cycles]
        top_k_actions = []
        if purpose_query:
            matches = [a for a in all_actions if purpose_query in a or a in purpose_query]
            fuzzy = get_close_matches(purpose_query, all_actions, n=3, cutoff=0.4)
            candidates = list(set(matches + fuzzy))
            top_k_actions = candidates[:3]
            
        if not top_k_actions:
            top_k_actions = all_actions[:3]

        return {
            "original_query": user_text,
            "extracted": extracted,
            "candidates": {
                "persona": top_k_personas,
                "purpose": top_k_actions
            }
        }

# Singleton
_parser_instance = None
def get_intent_parser():
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = IntentParser()
    return _parser_instance
