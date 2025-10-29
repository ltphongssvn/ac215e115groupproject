# services/rag-orchestrator/app/graph_memory.py
from typing import Dict, Any, List, Optional
from datetime import datetime
from datetime import timezone
import logging

logger = logging.getLogger(__name__)

class GraphMemory:
    """4-layer memory system: Episodic, Semantic, Procedural, Temporal"""
    
    def __init__(self, graph_store):
        self.graph = graph_store
        self.episodic_buffer = []  # Short-term raw events
        self.consolidation_threshold = 10
    
    def add_episodic(self, event: Dict[str, Any]) -> str:
        """Store raw event in episodic memory (short-term)"""
        event_id = f"ep_{datetime.now(timezone.utc).isoformat()}_{len(self.episodic_buffer)}"
        event_time = datetime.now(timezone.utc).isoformat()
        ingestion_time = event_time
        
        event_data = {
            "id": event_id,
            "content": event.get("content", ""),
            "context": event.get("context", {}),
            "event_time": event_time,
            "ingestion_time": ingestion_time
        }
        
        self.episodic_buffer.append(event_data)
        
        # Store in graph
        self.graph.add_entity(
            entity_id=event_id,
            entity_type="EpisodicMemory",
            properties=event_data,
            event_time=event_time,
            ingestion_time=ingestion_time
        )
        
        # Trigger consolidation if threshold reached
        if len(self.episodic_buffer) >= self.consolidation_threshold:
            self._consolidate_to_semantic()
        
        return event_id
    
    def _consolidate_to_semantic(self):
        """Transform episodic memories into semantic facts"""
        logger.info(f"Consolidating {len(self.episodic_buffer)} episodic memories")
        
        # Extract entities and relationships from episodes
        entities = {}
        relationships = []
        
        for episode in self.episodic_buffer:
            # Simple entity extraction (extend with NER in production)
            content = episode.get("content", "")
            words = content.split()
            
            # Create semantic entities
            for i, word in enumerate(words):
                if len(word) > 5:  # Simple heuristic
                    entity_id = f"sem_{word.lower()}"
                    if entity_id not in entities:
                        entities[entity_id] = {
                            "term": word.lower(),
                            "frequency": 0,
                            "contexts": []
                        }
                    entities[entity_id]["frequency"] += 1
                    entities[entity_id]["contexts"].append(episode["id"])
                    
                    # Link to episode
                    relationships.append({
                        "source": episode["id"],
                        "target": entity_id,
                        "type": "MENTIONS",
                        "weight": 0.8
                    })
        
        # Store semantic entities
        for entity_id, data in entities.items():
            self.graph.add_entity(
                entity_id=entity_id,
                entity_type="SemanticMemory",
                properties=data,
                event_time=datetime.now(timezone.utc).isoformat(),
                ingestion_time=datetime.now(timezone.utc).isoformat()
            )
        
        # Store relationships
        for rel in relationships:
            self.graph.add_relationship(
                source_id=rel["source"],
                target_id=rel["target"],
                rel_type=rel["type"],
                weight=rel["weight"]
            )
        
        self.episodic_buffer.clear()
    
    def add_procedural(self, workflow_id: str, steps: List[Dict[str, Any]]) -> bool:
        """Store workflow/procedure in procedural memory"""
        procedure_id = f"proc_{workflow_id}"
        
        self.graph.add_entity(
            entity_id=procedure_id,
            entity_type="ProceduralMemory",
            properties={"workflow": workflow_id, "step_count": len(steps)},
            event_time=datetime.now(timezone.utc).isoformat(),
            ingestion_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Link steps in sequence
        for i, step in enumerate(steps):
            step_id = f"{procedure_id}_step_{i}"
            self.graph.add_entity(
                entity_id=step_id,
                entity_type="ProcedureStep",
                properties=step,
                event_time=datetime.now(timezone.utc).isoformat(),
                ingestion_time=datetime.now(timezone.utc).isoformat()
            )
            
            self.graph.add_relationship(
                source_id=procedure_id,
                target_id=step_id,
                rel_type="HAS_STEP",
                weight=1.0,
                properties={"sequence": i}
            )
            
            if i > 0:
                prev_step = f"{procedure_id}_step_{i-1}"
                self.graph.add_relationship(
                    source_id=prev_step,
                    target_id=step_id,
                    rel_type="NEXT_STEP",
                    weight=1.0
                )
        
        return True
    
    def query_temporal(self, entity_id: str, event_time: str) -> Optional[Dict[str, Any]]:
        """Query memory state at specific time"""
        return self.graph.temporal_query(entity_id, event_time)
    
    def retrieve_context(self, query: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """Retrieve relevant context via graph traversal"""
        # Simple keyword matching (extend with embeddings)
        query_terms = [w.lower() for w in query.split() if len(w) > 4]
        
        results = []
        for term in query_terms[:3]:  # Top 3 terms
            entity_id = f"sem_{term}"
            paths = self.graph.traverse(entity_id, max_depth=max_depth)
            results.extend(paths)
        
        return results
