# fastapi-neo4j

Minimal FastAPI backend for Neo4j embed service.

This service exposes two endpoints only:

- POST /api/embed -> generate embed token and return embed URL
- POST /api/proxy/query -> proxy a Cypher query to Neo4j and return results

How to run (local, basic):

1. Create a virtualenv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Set environment variables (example):

```bash
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/embeddb
export NEO4J_URI=bolt://neo4j:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=secret
export EMBED_BASE_URL=http://localhost:8000
```

3. Run the app:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Docker and pyproject build instructions are provided in `Dockerfile` and `pyproject.toml`.
