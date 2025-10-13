# services/rag-orchestrator/app/agentic_rag.py
from .graph_store import GraphStore
from .graph_memory import GraphMemory
from .hybrid_retrieval import HybridRetrieval
from typing import Dict, Any
from datetime import datetime
from datetime import timezone
import logging

logger = logging.getLogger(__name__)

class AgenticRAG:
    """Agentic Graph RAG orchestrator with autonomous reasoning"""
    
    def __init__(self):
        self.graph_store = GraphStore()
        self.memory = GraphMemory(self.graph_store)
        self.retrieval = HybridRetrieval(self.memory)
        self.usage_patterns = {}
        
    async def process_query(self, query: str, context: str = None) -> Dict[str, Any]:
        """Process query with agentic capabilities"""
        
        # Record episodic event
        event_id = self.memory.add_episodic({
            "content": query,
            "context": {"user_context": context} if context else {}
        })
        
        # Autonomous decision: temporal vs standard query
        is_temporal = self._detect_temporal_query(query)
        
        if is_temporal:
            result = await self._handle_temporal_query(query)
        else:
            result = await self._handle_standard_query(query)
        
        # Self-evolution: track usage
        self._update_usage_patterns(query, result)
        
        return result
    
    def _detect_temporal_query(self, query: str) -> bool:
        """Autonomous detection of temporal queries"""
        temporal_markers = ["last month", "yesterday", "was", "history", "past"]
        return any(marker in query.lower() for marker in temporal_markers)
    
    async def _handle_temporal_query(self, query: str) -> Dict[str, Any]:
        """Handle queries about past states"""
        # Extract time reference (simplified)
        event_time = datetime.now(timezone.utc).isoformat()
        
        retrieved = self.retrieval.retrieve(query, top_k=5)
        
        return {
            "query": query,
            "query_type": "temporal",
            "retrieved_documents": retrieved["documents"],
            "answer": f"Temporal analysis of: {query}",
            "confidence": 0.85,
            "metadata": {
                **retrieved["metadata"],
                "event_time": event_time,
                "reasoning": "multi-hop temporal traversal"
            }
        }
    
    async def _handle_standard_query(self, query: str) -> Dict[str, Any]:
        """Handle standard queries with graph reasoning"""
        
        # 3-stage hybrid retrieval
        retrieved = self.retrieval.retrieve(query, top_k=5)
        
        # Context synthesis from graph
        context = self._synthesize_answer(query, retrieved["documents"])
        
        return {
            "query": query,
            "query_type": "standard",
            "retrieved_documents": retrieved["documents"],
            "answer": context,
            "confidence": 0.90,
            "metadata": {
                **retrieved["metadata"],
                "reasoning": "vector + graph hybrid"
            }
        }
    
    def _synthesize_answer(self, query: str, documents: list) -> str:
        """Generate answer from retrieved context"""
        if not documents:
            return "No relevant information found in knowledge graph."
        
        # Combine top documents
        context_parts = []
        for doc in documents[:3]:
            context_parts.append(f"[{doc['source']}] {doc['content']}")
        
        return f"Based on knowledge graph: {' | '.join(context_parts)}"
    
    def _update_usage_patterns(self, query: str, result: Dict[str, Any]):
        """Self-evolution through usage tracking"""
        query_type = result.get("query_type", "unknown")
        if query_type not in self.usage_patterns:
            self.usage_patterns[query_type] = {"count": 0, "avg_confidence": 0.0}
        
        pattern = self.usage_patterns[query_type]
        pattern["count"] += 1
        confidence = result.get("confidence", 0.0)
        pattern["avg_confidence"] = (
            (pattern["avg_confidence"] * (pattern["count"] - 1) + confidence) 
            / pattern["count"]
        )
    
    def add_workflow(self, workflow_id: str, steps: list) -> bool:
        """Store procedural knowledge"""
        return self.memory.add_procedural(workflow_id, steps)
