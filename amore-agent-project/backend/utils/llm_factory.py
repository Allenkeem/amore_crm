import os
import openai
from typing import Optional
from dotenv import load_dotenv

# Load .env from backend directory (where this script runs or parent)
load_dotenv()

class LLMClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "llama3.1"):
        # [Local Switch] Use Ollama settings
        self.api_key = "ollama" # Dummy key for Ollama
        self.base_url = "http://localhost:11434/v1"
        self.model = model
        
        print(f"[LLMClient] Connecting to Local LLM at {self.base_url} (Model: {self.model})...")
        
        self.client = openai.OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

    def generate(self, prompt: str, system_message: str = None) -> str:
        if not self.client:
             return "[MOCK RESPONSE] OpenAI API Key가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 넣어주세요.\n(하지만 엔진 연결은 성공했습니다!)"

        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        # In our prompt structure, 'prompt' often contains system directives. 
        # If so, we can just treat it as user message or split it. 
        # For simplicity, we send the whole chunk as user message if system_message is empty.
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=600  # Smaller limit for cost control
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ OpenAI API 호출 실패: {str(e)}"

# Singleton
_client_instance = None
def get_llm_client():
    global _client_instance
    if _client_instance is None:
        _client_instance = LLMClient()
    return _client_instance
