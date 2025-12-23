from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .schemas import RetrievalRequest, RetrievalResponse
from .retriever import get_retriever

app = FastAPI(title="CRM Model-1: Product Retriever")

# Initialize Retriever on startup
retriever = get_retriever()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/retrieve_products", response_model=RetrievalResponse)
async def retrieve_products(request: RetrievalRequest):
    """
    Retrieve Top-K products and their factsheets for a user query.
    """
    try:
        candidates = retriever.retrieve(request.user_query)
        
        return RetrievalResponse(
            query=request.user_query,
            top_k=len(candidates),
            candidates=candidates
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok", "products_loaded": len(retriever.products)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
