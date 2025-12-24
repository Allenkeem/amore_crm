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
        
        # 2. Action List for Context
        action_context = "\n".join([f"- {ac['id']}: {ac.get('matching_description', '')}" for ac in self.loader.action_cycles])
        
        # 3. LLM Extraction & Matching
        prompt = f"""
        Analyze the user request and map it to the provided Persona list and Action Scenario list.
        
        [Persona List]
        {persona_context}

        [Action Scenario List]
        {action_context}
        
        User Request: "{user_text}"
        
        Task:
        1. Extract 'product' name.
        2. Identify the best matching 'persona' from the list above.
        3. Identify the best matching 'action_id' from the Action Scenario List. (e.g., G01_WELCOME, G05_WINTER)
        4. Summarize the 'purpose' (intent).
        
        Return ONLY a JSON object: {{"product": "String", "selected_persona": "Exact Name", "selected_action_id": "ID", "purpose": "String"}}
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
            extracted = {"product": user_text, "selected_persona": None, "selected_action_id": None, "purpose": None}
            
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

        # 5. Determine Action Candidate
        selected_id = extracted.get("selected_action_id")
        
        # Validate ID
        valid_ids = [ac['id'] for ac in self.loader.action_cycles]
        if selected_id and selected_id not in valid_ids:
            selected_id = None # Invalid ID from LLM
            
        top_k_actions = []
        
        # Specific Action Selected by LLM?
        if selected_id:
             for ac in self.loader.action_cycles:
                 if ac['id'] == selected_id:
                     desc = ac.get("matching_description", ac.get("name", ""))
                     # UPDATE: Use Name for cleaner display, ID handles lookup
                     display_name = ac.get("name", "")
                     top_k_actions.append(display_name)
                     break
        
        # Fallback: Search by Purpose if no ID or ID was invalid
        if not top_k_actions:
            purpose_query = extracted.get("purpose") or ""
            
            all_actions_for_matching = []
            for action in self.loader.action_cycles:
                a_id = action.get("id", "UNKNOWN")
                desc = action.get("matching_description", action.get("name", ""))
                # Inject situation for better manual reading if needed
                situation = action.get("situation", "")
                extra_context = f" [SITUATION: {situation}]" if situation else ""
                    
                full_action_description = f"[{a_id}]: {desc}{extra_context}"
                all_actions_for_matching.append(full_action_description) 
            
            if purpose_query:
                matches = [a for a in all_actions_for_matching if purpose_query.lower() in a.lower() or a.lower() in purpose_query.lower()]
                fuzzy = get_close_matches(purpose_query, all_actions_for_matching, n=3, cutoff=0.4)
                # Preserving order while removing duplicates
                raw_candidates = list(dict.fromkeys(matches + fuzzy))[:3]
                
                # Convert to clean format: Name Only
                for i, cand in enumerate(raw_candidates):
                     # cand is "[ID]: Description..."
                     if "[" in cand and "]" in cand:
                         mid = cand.split("[")[1].split("]")[0]
                         # Find name
                         action_obj = next((x for x in self.loader.action_cycles if x["id"] == mid), None)
                         if action_obj:
                             top_k_actions.append(action_obj.get("name", ""))
                             # Set selected_id to the top candidate if not already set
                             if not selected_id and i == 0:
                                 selected_id = mid
                         else:
                             top_k_actions.append(cand)
                     else:
                         top_k_actions.append(cand)
            
        if not top_k_actions:
            # Fallback: Just take the first 3 actions' display names
            # Note: action_candidates is not defined in this scope in original code, 
            # assuming it meant listing all actions. But let's just make it empty or generic.
            pass

        return {
            "original_query": user_text,
            "extracted": extracted, # Keep for debugging
            "candidates": {
                "persona": top_k_personas,
                "purpose": top_k_actions
            },
            # Map to Orchestrator expected keys
            "target_product": extracted.get("product"),
            "target_persona": extracted.get("selected_persona"), # or use selected_persona variable
            "target_purpose": extracted.get("purpose"),
            "selected_id": selected_id
        }

# Singleton
_parser_instance = None
def get_intent_parser():
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = IntentParser()
    return _parser_instance
