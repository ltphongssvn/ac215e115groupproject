# services/nl-sql-service/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .nl_sql_agent import NLSQLAgent
import logging
import os

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(title="NL-SQL Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = NLSQLAgent()

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    success: bool
    question: str
    sql_query: str = None
    results: list = []
    row_count: int = 0
    error: str = None

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "nl-sql"}

@app.post("/query", response_model=QueryResponse)
async def process_nl_query(request: QueryRequest):
    result = await agent.process_query(request.question)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
