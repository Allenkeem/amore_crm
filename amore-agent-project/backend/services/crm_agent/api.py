from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
from typing import List, Optional

# Import Model-1
from backend.scripts_model1.retriever import get_retriever
from backend.scripts_model1.schemas import ProductCandidate

# Import Model-2
from backend.model_2.generator import get_generator

app = FastAPI(title="Amore CRM AI Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------------
# Schemas
# -------------------------------------------------------------------------
class ChatRequest(BaseModel):
    user_query: str
    # Context (Optional)
    persona_name: str = "가성비 헌터"
    action_purpose: str = "제품 추천"
    channel: str = "문자(LMS)"

class ChatResponse(BaseModel):
    query: str
    retrieval_top_k: int
    candidates: List[ProductCandidate]
    # Model-2 Output
    generated_response: str

# -------------------------------------------------------------------------
# Startup
# -------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    print("[API] Initializing Models...")
    get_retriever() # Warm up Model-1
    get_generator() # Warm up Model-2 (Gemma)
    print("[API] All Models Loaded.")

# -------------------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------------------

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    End-to-End Flow:
    1. Model-1: Retrieve Top-K Products
    2. Model-2: Generate Message using Top-1 Product + Persona + Cycle + Brand Tone
    """
    try:
        # Step 1: Retrieve
        retriever = get_retriever()
        candidates = retriever.retrieve(req.user_query)
        
        if not candidates:
            return ChatResponse(
                query=req.user_query,
                retrieval_top_k=0,
                candidates=[],
                generated_response=" 죄송합니다. 요청하신 조건에 맞는 상품을 찾을 수 없습니다."
            )
            
        # Step 2: Generate (Using Top-1 Candidate)
        top_product = candidates[0]
        generator = get_generator()
        
        response_text = generator.generate_response(
            product_cand=top_product,
            persona_name=req.persona_name,
            action_purpose=req.action_purpose,
            channel=req.channel
        )
        
        return ChatResponse(
            query=req.user_query,
            retrieval_top_k=len(candidates),
            candidates=candidates,
            generated_response=response_text
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
