import sys
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uvicorn

# -------------------------------------------------------------------------
# Path Setup
# -------------------------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from services.crm_agent.orchestrator import get_orchestrator

# -------------------------------------------------------------------------
# Initialize
# -------------------------------------------------------------------------
print("Initializing Orchestrator...")
orch = get_orchestrator()

app = FastAPI(title="Amore Agent API")

# -------------------------------------------------------------------------
# Models
# -------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    final_message: str
    candidates: Dict[str, Any]
    parsed: Dict[str, Any] = {}

# -------------------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        # 1. Orchestrator Process
        results = orch.process_query(request.message)
        
        # 2. Extract Response
        final_msg = results.get("final_message", "Error generation message.")
        candidates = results.get("candidates", {})
        parsed = results.get("parsed", {})
        
        return ChatResponse(
            final_message=final_msg,
            candidates=candidates,
            parsed=parsed
        )
            
    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)
