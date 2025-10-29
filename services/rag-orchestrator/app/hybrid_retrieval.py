# services/rag-orchestrator/app/hybrid_retrieval.py
from typing import List, Dict, Any
import numpy as np
import logging

logger = logging.getLogger(__name__)

class HybridRetrieval:
    """3-stage pipeline: Vector Search → Graph Traversal → Context Synthesis"""
    
    def __init__(self, graph_memory):
        self.memory = graph_memory
        self.vector_cache = {}  # Mock embeddings
    
    def retrieve(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Execute hybrid retrieval pipeline"""
        
        # Stage 1: Vector search for candidate nodes
        candidates = self._vector_search(query, top_k * 2)
        logger.info(f"Stage 1 - Vector search: {len(candidates)} candidates")
        
        # Stage 2: Graph traversal from candidates
        graph_results = []
        for candidate in candidates[:top_k]:
            paths = self.memory.graph.traverse(
                start_entity_id=candidate["id"],
                max_depth=2,
                min_weight=0.5
            )
            graph_results.extend(paths)
        logger.info(f"Stage 2 - Graph traversal: {len(graph_results)} paths")
        
        # Stage 3: Context synthesis
        synthesized = self._synthesize_context(query, candidates, graph_results)
        logger.info(f"Stage 3 - Synthesis: {len(synthesized['documents'])} docs")
        
        return synthesized
    
    def _vector_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Mock vector search - replace with real embeddings"""
        query_terms = set(w.lower() for w in query.split() if len(w) > 3)
        
        candidates = []
        for term in list(query_terms)[:5]:
            entity_id = f"sem_{term}"
            candidates.append({
                "id": entity_id,
                "score": 0.9,
                "content": term,
                "type": "SemanticMemory"
            })
        
        return candidates[:top_k]
    
    def _synthesize_context(self, query: str, vector_results: List[Dict],
                           graph_results: List[Dict]) -> Dict[str, Any]:
        """Combine vector and graph results with relevance scoring"""
        
        # Deduplicate and score
        seen = set()
        documents = []
        
        # Add vector results (high relevance)
        for item in vector_results:
            if item["id"] not in seen:
                documents.append({
                    "id": item["id"],
                    "content": item.get("content", ""),
                    "score": item.get("score", 0.8),
                    "source": "vector"
                })
                seen.add(item["id"])
        
        # Add graph results (contextual relevance)
        for path in graph_results:
            for node in path.get("nodes", []):
                node_id = node.get("id")
                if node_id and node_id not in seen:
                    documents.append({
                        "id": node_id,
                        "content": str(node.get("properties", {})),
                        "score": path.get("path_weight", 0.6) * 0.8,
                        "source": "graph"
                    })
                    seen.add(node_id)
        
        # Sort by score
        documents.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "query": query,
            "documents": documents[:10],
            "metadata": {
                "vector_count": len(vector_results),
                "graph_paths": len(graph_results),
                "total_retrieved": len(documents)
            }
        }
