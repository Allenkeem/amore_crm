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
        
        # Store tuples of (full_desc, clean_name)
        action_candidates = []
        
        for action in self.loader.action_cycles:
            a_id = action.get("id", "UNKNOWN")
            name = action.get("name", "") # Clean name for display, e.g. "신규 고객 제안"
            desc = action.get("matching_description", name)
            
            # [NEW] Inject Context/Situation for better selection
            situation = action.get("situation", "")
            context_guide = action.get("core_guide", {}).get("context", "")
            
            extra_context = ""
            if situation:
                extra_context = f" [SITUATION: {situation}]"
            elif context_guide:
                extra_context = f" [CONTEXT: {context_guide}]"
                
            full_action_description = f"[{a_id}]: {desc}{extra_context}"
            
            # Use full description for matching, but keep clean name for display
            action_candidates.append({
                "full": full_action_description,
                "display": name if name else a_id # Use Name if available, else ID
            })
            
        top_k_actions = []
        if purpose_query:
            # Filter based on full description
            matches = [a for a in action_candidates if purpose_query.lower() in a["full"].lower()]
            
            # Extract just the full strings for fuzzy matching
            full_strings = [a["full"] for a in action_candidates]
            fuzzy_strs = get_close_matches(purpose_query, full_strings, n=3, cutoff=0.4)
            
            # Re-map fuzzy strings back to objects
            fuzzy_matches = [a for a in action_candidates if a["full"] in fuzzy_strs]
            
            # Combine
            combined = matches + fuzzy_matches
            # Deduplicate by display name to avoid duplicates
            seen = set()
            unique_candidates = []
            for c in combined:
                if c["display"] not in seen:
                    unique_candidates.append(c["display"])
                    seen.add(c["display"])
            
            top_k_actions = unique_candidates[:3]
            
        if not top_k_actions:
            # Fallback: Just take the first 3 actions' display names
            top_k_actions = [a["display"] for a in action_candidates[:3]]

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
