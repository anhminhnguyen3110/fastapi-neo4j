from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.services import run_cypher

router = APIRouter()


class ProxyQueryRequest(BaseModel):
    cypher: str = Field(
        ..., 
        description="Cypher query to execute",
        example="MATCH (p:Person)-[r:ACTED_IN]->(m:Movie) RETURN p,r,m LIMIT 25"
    )
    params: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Query parameters",
        example={}
    )
    
    class Config:
        schema_extra = {
            "example": {
                "cypher": "MATCH (p:Person)-[r:ACTED_IN]->(m:Movie) RETURN p,r,m LIMIT 25",
                "params": {}
            }
        }


class ProxyQueryResponse(BaseModel):
    success: bool = Field(..., description="Success status")
    data: Optional[list] = Field(None, description="Query results")
    error: Optional[dict] = Field(None, description="Error information")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": [
                    {
                        "p": {
                            "identity": 1,
                            "labels": ["Person"],
                            "properties": {"name": "Tom Hanks", "born": 1956}
                        },
                        "r": {
                            "identity": 1,
                            "start": 1,
                            "end": 2,
                            "type": "ACTED_IN",
                            "properties": {"roles": ["Forrest"]}
                        },
                        "m": {
                            "identity": 2,
                            "labels": ["Movie"],
                            "properties": {"title": "Forrest Gump", "released": 1994}
                        }
                    }
                ]
            }
        }


@router.post("/api/proxy/query", tags=["Proxy"], summary="Execute Neo4j Query", response_model=ProxyQueryResponse)
async def proxy_query_endpoint(request: ProxyQueryRequest):
    """
    Execute a Cypher query against Neo4j database.
    
    - **cypher**: Cypher query to execute
    - **params**: Optional parameters for the query
    
    Returns the query results in JSON format.
    """
    if not request.cypher or request.cypher.strip() == "":
        raise HTTPException(status_code=400, detail="cypher is required")

    try:
        result = await run_cypher(request.cypher, request.params or {})
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": {"message": str(e)}}
