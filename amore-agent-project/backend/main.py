import sys
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uvicorn
import json

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
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    if not request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    async def event_generator():
        try:
            # Iterate over the generator from orchestrator
            # Note: process_query_stream is a synchronous generator, so we iterate normally.
            # If it were async, we'd use async for.
            for event in orch.process_query_stream(request.message):
                # Format as SSE (Server-Sent Events)
                # data: <json>\n\n
                json_data = json.dumps(event, ensure_ascii=False)
                yield f"data: {json_data}\n\n"
                
        except Exception as e:
            print(f"Error during streaming: {e}")
            error_event = {"type": "error", "msg": str(e)}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)
