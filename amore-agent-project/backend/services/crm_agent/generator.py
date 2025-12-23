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

    def generate_suggestions(self, original_msg: str, product_name: str, target_persona: str) -> list:
        """
        Generate 3 actionable follow-up suggestions based on the generated message.
        """
        print(f"[Model-2] Generating dynamic suggestions...")
        
        prompt = f"""
        [Role]
        You are a senior CRM Marketing Editor.
        
        [Task]
        Analyze the following CRM message generated for '{product_name}' targeting '{target_persona}'.
        Suggest 3 specific, short, and actionable requests to improve or vary the message.
        
        [Input Message]
        "{original_msg}"
        
        [Guidelines]
        1. Access from 4 perspectives: Length/Readability, Tone, Benefit Emphasis, Engagement.
        2. Suggestions must be concise (under 15 Korean characters).
        3. Examples: "더 짧게 줄여줘", "감성적인 톤으로", "할인율을 제목에", "이모지 더 많이"
        4. Return ONLY a Python list of strings. Do not include markdown formatting or explanations.
        
        [Output Format]
        ["Valid Suggestion 1", "Valid Suggestion 2", "Valid Suggestion 3"]
        """
        
        response_text = self.client.generate(prompt=prompt)
        
        # Simple parsing to ensure list format
        try:
            import ast
            # Cleanup markdown code blocks if present
            cleaned_text = response_text.replace("```json", "").replace("```python", "").replace("```", "").strip()
            suggestions = ast.literal_eval(cleaned_text)
            if isinstance(suggestions, list):
                return suggestions[:3] # Ensure max 3
            return ["더 짧게 줄여줘", "톤을 부드럽게", "혜택 강조해줘"] # Fallback
        except:
            return ["더 짧게 줄여줘", "톤을 부드럽게", "혜택 강조해줘"] # Fallback

# Singleton
_gen_instance = None
def get_generator():
    global _gen_instance
    if _gen_instance is None:
        _gen_instance = Generator()
    return _gen_instance
