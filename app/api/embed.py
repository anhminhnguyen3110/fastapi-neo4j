from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from uuid import uuid4
from datetime import datetime, timedelta, timezone
import os

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.db.crud import create_embed as crud_create_embed

router = APIRouter()


class EmbedRequest(BaseModel):
    cypherQuery: str = Field(
        ..., 
        description="Cypher query to execute",
        example="MATCH (p:Person)-[r:ACTED_IN]->(m:Movie) RETURN p,r,m LIMIT 25"
    )
    expiresInDays: int = Field(
        7, 
        description="Expiration in days", 
        ge=1,
        example=7
    )
    
    class Config:
        schema_extra = {
            "example": {
                "cypherQuery": "MATCH (p:Person)-[r:ACTED_IN]->(m:Movie) RETURN p,r,m LIMIT 25",
                "expiresInDays": 7
            }
        }


class EmbedResponse(BaseModel):
    success: bool = Field(True, description="Success status")
    data: dict = Field(..., description="Embed data containing URL, token, and expiration info")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "embedUrl": "http://localhost:8000/view/abc123def456",
                    "embedToken": "abc123def456",
                    "expiresAt": "2025-11-03T00:00:00Z",
                    "expiresIn": 604800
                }
            }
        }


class EmbedData(BaseModel):
    embedUrl: str = Field(..., description="Complete embed URL")
    embedToken: str = Field(..., description="Unique embed token")
    expiresAt: str = Field(..., description="Expiration timestamp (ISO format)")
    expiresIn: int = Field(..., description="Time-to-live in seconds")


@router.post("/api/embed", tags=["Embed"], summary="Create Embed URL", response_model=EmbedResponse)
async def create_embed_endpoint(
    request: EmbedRequest, 
    session_gen=Depends(get_session)
):
    """
    Create an embed URL for a Cypher query.
    
    - **cypherQuery**: Cypher query to execute in the visualization
    - **expiresInDays**: Number of days the embed token will remain valid (default: 1)
    
    Returns an embed URL that can be used to display the graph visualization.
    """
    if not request.cypherQuery or request.cypherQuery.strip() == "":
        raise HTTPException(status_code=400, detail="cypherQuery is required")

    expires_days = request.expiresInDays or 1
    expires_in = expires_days * 24 * 60 * 60
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    token = str(uuid4())

    async with session_gen as session:
        await crud_create_embed(session, embed_token=token, cypher_query=request.cypherQuery.strip(), expires_at=expires_at)

    base_url = os.environ.get("EMBED_BASE_URL", "http://localhost:8000")
    embed_url = f"{base_url}/view/{token}"

    return {
        "success": True,
        "data": {
            "embedUrl": embed_url,
            "embedToken": token,
            "expiresAt": expires_at.isoformat(),
            "expiresIn": expires_in,
        },
    }
