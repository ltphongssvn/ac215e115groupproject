# services/nl-sql-service/app/nl_sql_agent.py
from typing import Dict, Any
from .database import db
from .sql_generator_local import SQLGenerator
import logging

logger = logging.getLogger(__name__)

class NLSQLAgent:
    def __init__(self):
        self.sql_generator = SQLGenerator()
        self.schema = """
        Tables:
        - inventory_data: id, item_type, quantity, price, date, supplier_id
        - suppliers: id, name, contact, address, rating
        - transactions: id, type, amount, date, item_id, supplier_id
        - price_history: id, item_type, price, date, market_conditions
        """
    
    async def process_query(self, question: str) -> Dict[str, Any]:
        """Process natural language query end-to-end"""
        try:
            # Test database connection
            if not db.test_connection():
                return {
                    "success": False,
                    "error": "Database connection failed"
                }
            
            # Generate SQL
            sql_query = self.sql_generator.generate_sql(question, self.schema)
            logger.info(f"Generated SQL: {sql_query}")
            
            # Execute query
            results = db.execute_query(sql_query)
            
            return {
                "success": True,
                "question": question,
                "sql_query": sql_query,
                "results": results,
                "row_count": len(results)
            }
            
        except Exception as e:
            logger.error(f"Query processing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "question": question
            }
