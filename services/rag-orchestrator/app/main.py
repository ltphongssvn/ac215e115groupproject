# services/rag-orchestrator/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from .agentic_rag import AgenticRAG
import logging
import os

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(title="Agentic Graph RAG Orchestrator", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize at module level with proper cleanup
agentic_rag = AgenticRAG()

@app.on_event("shutdown")
def shutdown_event():
    agentic_rag.graph_store.close()

class RAGQuery(BaseModel):
    query: str
    context: Optional[str] = None
    max_results: int = 5

class RAGResponse(BaseModel):
    query: str
    query_type: str
    retrieved_documents: List[Dict[str, Any]]
    answer: str
    confidence: float
    metadata: Dict[str, Any]

class WorkflowRequest(BaseModel):
    workflow_id: str
    steps: List[Dict[str, Any]]

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "agentic-graph-rag", "version": "2.0.0"}

@app.post("/rag/query", response_model=RAGResponse)
async def process_rag_query(request: RAGQuery):
    """Agentic Graph RAG query with hybrid retrieval"""
    try:
        result = await agentic_rag.process_query(
            query=request.query,
            context=request.context
        )
        return RAGResponse(**result)
    except Exception as e:
        logger.error(f"RAG processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/workflow")
async def add_workflow(request: WorkflowRequest):
    """Store procedural workflow in graph memory"""
    try:
        success = agentic_rag.add_workflow(
            workflow_id=request.workflow_id,
            steps=request.steps
        )
        return {"success": success, "workflow_id": request.workflow_id}
    except Exception as e:
        logger.error(f"Workflow storage failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rag/stats")
async def get_stats():
    """Get usage statistics for self-evolution monitoring"""
    return {
        "usage_patterns": agentic_rag.usage_patterns,
        "episodic_buffer_size": len(agentic_rag.memory.episodic_buffer)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
