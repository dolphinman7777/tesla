from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class QueryIntent:
    query_type: str
    parameters: Dict[str, Any]
    time_period: Optional[str] = None
    comparison: Optional[str] = None

@dataclass
class QueryResult:
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str] = None
