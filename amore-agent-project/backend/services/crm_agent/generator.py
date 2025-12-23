from typing import Dict, Any
from .prompt_engine import build_prompt
from utils.llm_factory import get_llm_client

class Generator:
    def __init__(self):
        print("[Model-2] Initializing Generator with OpenAI Client...")
        self.client = get_llm_client()

    def generate_response(self, 
                          product_cand: Any, # ProductCandidate object from Model-1
                          persona_name: str,
                          action_purpose: str,
                          channel: str = "문자(LMS)") -> str:
        
        # 1. Extract Factsheet from Candidate
        factsheet = product_cand.factsheet.dict()
        product_name = product_cand.product_name
        brand_name = product_cand.brand
        
        # 2. Build Prompt
        full_prompt = build_prompt(
            product_name=product_name,
            brand_name=brand_name,
            factsheet=factsheet,
            persona_name=persona_name,
            action_purpose=action_purpose,
            channel=channel
        )
        
        # 3. Generate (via OpenAI)
        print("[Model-2] Sending request to OpenAI (gpt-4o-mini)...")
        return self.client.generate(prompt=full_prompt)

# Singleton
_gen_instance = None
def get_generator():
    global _gen_instance
    if _gen_instance is None:
        _gen_instance = Generator()
    return _gen_instance
