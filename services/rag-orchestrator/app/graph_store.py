# services/rag-orchestrator/app/graph_store.py
from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)

class GraphStore:
    """Neo4j-based knowledge graph for hybrid RAG with vector+graph search"""
    
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self._initialize_schema()
            logger.info("GraphStore initialized successfully")
        except Exception as e:
            logger.warning(f"Neo4j unavailable, using in-memory mode: {e}")
            self.driver = None
    
    def _initialize_schema(self):
        """Create indexes and constraints for optimal query performance"""
        if not self.driver:
            return
            
        with self.driver.session() as session:
            # Entity uniqueness
            session.run("""
                CREATE CONSTRAINT entity_id IF NOT EXISTS
                FOR (e:Entity) REQUIRE e.id IS UNIQUE
            """)
            
            # Temporal indexes for bi-temporal queries
            session.run("""
                CREATE INDEX entity_event_time IF NOT EXISTS
                FOR (e:Entity) ON (e.event_time)
            """)
            session.run("""
                CREATE INDEX entity_ingestion_time IF NOT EXISTS
                FOR (e:Entity) ON (e.ingestion_time)
            """)
    
    def add_entity(self, entity_id: str, entity_type: str, properties: Dict[str, Any], 
                   event_time: str, ingestion_time: str) -> bool:
        """Add entity with bi-temporal tracking (T, T')"""
        if not self.driver:
            return False
            
        with self.driver.session() as session:
            result = session.run("""
                MERGE (e:Entity {id: $id})
                SET e.type = $type,
                    e.event_time = $event_time,
                    e.ingestion_time = $ingestion_time,
                    e += $properties
                RETURN e.id as id
            """, id=entity_id, type=entity_type, event_time=event_time,
                ingestion_time=ingestion_time, properties=properties)
            return result.single() is not None
    
    def add_relationship(self, source_id: str, target_id: str, rel_type: str,
                        weight: float = 1.0, properties: Dict[str, Any] = None) -> bool:
        """Add weighted relationship between entities"""
        if not self.driver:
            return False
            
        props = properties or {}
        props['weight'] = weight
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (a:Entity {id: $source}), (b:Entity {id: $target})
                MERGE (a)-[r:RELATES {type: $rel_type}]->(b)
                SET r += $properties
                RETURN r
            """, source=source_id, target=target_id, rel_type=rel_type, properties=props)
            return result.single() is not None
    
    def traverse(self, start_entity_id: str, max_depth: int = 2, 
                min_weight: float = 0.5) -> List[Dict[str, Any]]:
        """Graph traversal with configurable depth and relationship weights"""
        if not self.driver:
            return []
            
        with self.driver.session() as session:
            result = session.run("""
                MATCH path = (start:Entity {id: $start})-[r:RELATES*1..$depth]->(end:Entity)
                WHERE ALL(rel IN relationships(path) WHERE rel.weight >= $min_weight)
                WITH path, 
                     reduce(w = 1.0, rel IN relationships(path) | w * rel.weight) as path_weight
                WHERE path_weight >= $min_weight
                RETURN 
                    [node IN nodes(path) | {
                        id: node.id,
                        type: node.type,
                        properties: properties(node)
                    }] as nodes,
                    [rel IN relationships(path) | {
                        type: rel.type,
                        weight: rel.weight
                    }] as relationships,
                    path_weight
                ORDER BY path_weight DESC
                LIMIT 20
            """, start=start_entity_id, depth=max_depth, min_weight=min_weight)
            
            return [dict(record) for record in result]
    
    def temporal_query(self, entity_id: str, event_time: str) -> Optional[Dict[str, Any]]:
        """Query entity state at specific event time (temporal awareness)"""
        if not self.driver:
            return None
            
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e:Entity {id: $id})
                WHERE e.event_time <= $time
                WITH e ORDER BY e.event_time DESC LIMIT 1
                RETURN e.id as id, e.type as type, properties(e) as properties
            """, id=entity_id, time=event_time)
            
            record = result.single()
            return dict(record) if record else None
    
    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()
