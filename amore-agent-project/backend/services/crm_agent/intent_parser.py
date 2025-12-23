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
        Analyze the user request and map it to the provided Persona list.
        
        [Persona List]
        {persona_context}
        
        User Request: "{user_text}"
        
        Task:
        1. Extract 'product' name.
        2. Identify the best matching 'persona' from the list above. If none perfectly fit, pick the closest one.
        3. Identify 'purpose' (goal).
        
        Return ONLY a JSON object: {{"product": "String", "selected_persona": "Exact Name from List", "purpose": "String"}}
        """
        
        raw_json = self.llm.generate(prompt)
        # Basic cleaning
        if "```json" in raw_json:
            raw_json = raw_json.split("```json")[1].split("```")[0]
        elif "```" in raw_json:
            raw_json = raw_json.split("```")[1].split("```")[0]
            
        try:
            extracted = json.loads(raw_json)
        except:
            extracted = {"product": user_text, "selected_persona": None, "purpose": None}
            
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
             top_k_personas = list(self.loader.personas.keys())[:3] # Fallback to default list

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
