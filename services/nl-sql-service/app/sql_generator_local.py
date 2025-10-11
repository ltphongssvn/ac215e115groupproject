# services/nl-sql-service/app/sql_generator_local.py
import os
import sqlparse
import logging

logger = logging.getLogger(__name__)

class SQLGenerator:
    def __init__(self):
        self.use_mock = os.getenv("USE_MOCK_LLM", "false").lower() == "true"
        if not self.use_mock:
            try:
                from langchain_google_vertexai import VertexAI
                from langchain.prompts import PromptTemplate
                from langchain.chains import LLMChain
                
                self.llm = VertexAI(
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
                
                self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
            except Exception as e:
                logger.warning(f"Failed to initialize Vertex AI: {e}. Using mock mode.")
                self.use_mock = True
    
    def validate_query(self, query: str) -> bool:
        """Validate SQL query for safety"""
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
        query_upper = query.upper()
        
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                logger.warning(f"Dangerous SQL keyword detected: {keyword}")
                return False
        
        return True
    
    def generate_sql(self, question: str, schema: str) -> str:
        """Generate SQL from natural language"""
        try:
            if self.use_mock:
                # Simple mock SQL generation for testing
                if "inventory" in question.lower():
                    query = "SELECT * FROM inventory_data LIMIT 10"
                elif "supplier" in question.lower():
                    query = "SELECT * FROM suppliers"
                elif "transaction" in question.lower():
                    query = "SELECT * FROM transactions ORDER BY date DESC LIMIT 10"
                else:
                    query = "SELECT 1"
            else:
                result = self.chain.run(question=question, schema=schema)
                query = result.strip()
            
            if not self.validate_query(query):
                raise ValueError("Generated query contains forbidden operations")
            
            formatted_query = sqlparse.format(query, reindent=True, keyword_case='upper')
            return formatted_query
        except Exception as e:
            logger.error(f"SQL generation failed: {str(e)}")
            raise
