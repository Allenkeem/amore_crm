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

    def refine_response(self, original_msg: str, feedback: str, feedback_detail: str) -> str:
        """
        Refine the message based on compliance feedback.
        """
        print(f"[Model-2] Refining response due to compliance violation...")
        
        prompt = f"""
        다음 광고 메시지는 아래 규정을 위반했다.

        [VIOLATION]
        {feedback}

        [FIX INSTRUCTION]
        - {feedback_detail}
        - 기존 문맥과 톤은 유지하되 규칙만 수정하라.
        - 새로운 주장이나 표현을 추가하지 마라.
        - 메시지 맨 앞에 '(광고)'가 없다면 반드시 추가하라.

        [ORIGINAL MESSAGE]
        {original_msg}
        """
        return self.client.generate(prompt=prompt)
        return self.client.generate(prompt=prompt)

# Singleton
_gen_instance = None
def get_generator():
    global _gen_instance
    if _gen_instance is None:
        _gen_instance = Generator()
    return _gen_instance
