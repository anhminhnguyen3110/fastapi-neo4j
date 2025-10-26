from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api import embed, proxy
from app.db.crud import find_by_token
from app.db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from datetime import datetime, timezone
import os

app = FastAPI(
    title="Neo4j Embedder API",
    description="API for generating embeddable Neo4j graph visualizations",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    openapi_url="/openapi.json"  # OpenAPI schema
)

# Include API routers
app.include_router(embed.router)
app.include_router(proxy.router)

# Mount static files from public directory
app.mount("/static", StaticFiles(directory="public"), name="static")

@app.get("/", tags=["Health"], summary="Health Check")
async def root():
    """Health check endpoint"""
    return {"success": True, "message": "fastapi-neo4j backend"}

@app.get("/view/{token}", tags=["Embed"], summary="View Embed Page")
async def view_embed(token: str, session_gen=Depends(get_session)):
    """
    Serve the embed visualization page for a given token.
    
    - **token**: The embed token from the URL path
    
    Returns an HTML page that displays the Neo4j visualization.
    """
    async with session_gen as session:
        embed_record = await find_by_token(session, token)
        if not embed_record:
            return FileResponse("public/embed-not-found.html")
        if embed_record.expires_at < datetime.now(timezone.utc):
            return FileResponse("public/embed-expired.html")
    return FileResponse("public/embed.html")

@app.get("/api/embed/{token}", tags=["Embed"], summary="Get Embed Data")
async def get_embed_data(token: str, session_gen=Depends(get_session)):
    """
    Get embed data for a token (used by embed.html).
    
    - **token**: The embed token
    
    Returns the Cypher query and metadata associated with the token.
    """
    async with session_gen as session:
        embed_record = await find_by_token(session, token)
        if not embed_record:
            raise HTTPException(status_code=404, detail="Token not found")
        if embed_record.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="Token expired")
    return {
        "success": True,
        "data": {
            "cypherQuery": embed_record.cypher_query,
            "token": token,
            "expiresAt": embed_record.expires_at.isoformat()
        }
    }
