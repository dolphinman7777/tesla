from typing import Optional, Dict, Any
from dune_client.types import QueryParameter
from dune_client.client import DuneClient
from dune_client.query import QueryBase
from config.settings import DUNE_API_KEY, QUERIES
from models.query_types import QueryIntent, QueryResult

class DuneManager:
    def __init__(self):
        self.client = DuneClient(DUNE_API_KEY)
        
    def build_query(self, intent: QueryIntent) -> QueryBase:
        query_id = QUERIES.get(intent.query_type)
        if not query_id:
            raise ValueError(f"Unknown query type: {intent.query_type}")
        
        # Define parameters based on intent type
        params = []
        
        if 'token_symbol' in intent.parameters:
            params.append(
                QueryParameter.text_type(
                    name="token_symbol",
                    value=intent.parameters['token_symbol'].upper()
                )
            )
            
        if 'wallet_address' in intent.parameters:
            params.append(
                QueryParameter.text_type(
                    name="wallet_address",
                    value=intent.parameters['wallet_address'].lower()
                )
            )
            
        return QueryBase(
            name=intent.query_type,
            query_id=query_id,
            params=params
        )
        
    async def execute_query(self, intent: QueryIntent) -> QueryResult:
        try:
            query = self.build_query(intent)
            print(f"Executing query with parameters: {intent.parameters}")
            results = self.client.run_query(query)
            
            if results and hasattr(results, 'result'):
                return QueryResult(
                    success=True,
                    data=results.result.rows[0] if results.result.rows else None
                )
            
            return QueryResult(success=False, data=None, error="No results found")
            
        except Exception as e:
            print(f"Query execution error: {str(e)}")
            return QueryResult(success=False, data=None, error=str(e))
