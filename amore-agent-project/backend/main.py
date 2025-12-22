from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# 프론트에서 보낼 데이터 형식 정의
class GenerationRequest(BaseModel):
    persona: str
    tone: str
    purpose: str

@app.post("/generate")
def generate_message(request: GenerationRequest):
    # 실제 모델이 들어오기 전까지는 임시 응답을 반환
    # 나중에 팀원이 이 부분을 실제 RAG/LLM 코드로 교체하면 됩니다.
    return {
        "title": f"[광고] {request.persona}님을 위한 맞춤 혜택!",
        "content": f"{request.tone} 톤으로 작성된 메시지입니다. {request.purpose}를 위해 아모레몰에서 준비했습니다. (이곳에 생성된 350자 이내의 본문이 들어갑니다.)"
    }