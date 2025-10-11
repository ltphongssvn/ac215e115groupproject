# services/nl-sql-service/app/sql_generator.py
import os
import re
import sqlparse
from typing import Dict, List
from langchain.prompts import PromptTemplate
from langchain_google_vertexai import ChatVertexAI
import logging

logger = logging.getLogger(__name__)

class SQLGenerator:
    def __init__(self):
        self.llm = ChatVertexAI(
            model_name=os.getenv("VERTEX_MODEL", "gemini-1.5-pro-001"),
            project=os.getenv("GCP_PROJECT"),
            location=os.getenv("GCP_LOCATION"),
            temperature=0.1,
            max_output_tokens=1024
        )
        
        self.prompt = PromptTemplate(
            input_variables=["question", "schema"],
            template="""You are a SQL expert for a rice market database.

Database Schema:
{schema}

User Question: {question}

Generate a PostgreSQL query that answers the question.
Rules:
- Use only SELECT statements (no INSERT/UPDATE/DELETE)
- Include proper JOIN conditions
- Use appropriate WHERE clauses
- Format dates correctly
- Return only the SQL query, no explanations

SQL Query:"""
        )
        
        # Use LCEL instead of LLMChain
        self.chain = self.prompt | self.llm
    
    def validate_query(self, query: str) -> bool:
        """Validate SQL query for safety"""
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
        query_upper = query.upper()
        
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                logger.warning(f"Dangerous keyword detected: {keyword}")
                return False
        return True
    
    def format_query(self, query: str) -> str:
        """Format SQL query for readability"""
        return sqlparse.format(query, reindent=True, keyword_case='upper')
    
    def generate(self, question: str, schema: str) -> Dict:
        """Generate SQL query from natural language question"""
        try:
            # Use invoke instead of run
            result = self.chain.invoke({"question": question, "schema": schema})
            
            # Extract query from result
            query = result.strip() if isinstance(result, str) else str(result)
            query = re.sub(r'^```sql\s*|\s*```$', '', query, flags=re.MULTILINE)
            query = query.strip()
            
            # Validate
            if not self.validate_query(query):
                return {
                    "success": False,
                    "error": "Query contains dangerous operations"
                }
            
            # Format
            formatted_query = self.format_query(query)
            
            return {
                "success": True,
                "query": formatted_query,
                "raw_query": query
            }
            
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
