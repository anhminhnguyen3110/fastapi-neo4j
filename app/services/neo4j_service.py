from neo4j import AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable, Neo4jError
from fastapi import HTTPException

# Use the app settings (which load .env) instead of reading os.environ directly.
from app.config import settings

# Ensure we use string values from settings
NEO4J_URI = str(getattr(settings, "NEO4J_URI", "bolt://localhost:7687"))
NEO4J_USER = getattr(settings, "NEO4J_USER", "neo4j")
NEO4J_PASSWORD = getattr(settings, "NEO4J_PASSWORD", "password")

# Create driver using settings so credentials from `.env` (via Settings) are used.
driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


async def run_cypher(cypher: str, params: dict):
    try:
        async with driver.session() as session:
            result = await session.run(cypher, **params)
            # AsyncResult is asynchronous; collect records asynchronously
            records = [record.data() async for record in result]
            return records
    except ServiceUnavailable as e:
        raise HTTPException(status_code=503, detail=f"Neo4j service unavailable: {str(e)}")
    except Neo4jError as e:
        raise HTTPException(status_code=400, detail=f"Cypher query error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
