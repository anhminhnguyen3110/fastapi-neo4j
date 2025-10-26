from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import EmbedToken
import uuid
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException


async def create_embed(session: AsyncSession, embed_token: str, cypher_query: str, expires_at: datetime):
    try:
        embed = EmbedToken(
            embed_token=embed_token,
            cypher_query=cypher_query,
            expires_at=expires_at
        )
        session.add(embed)
        await session.commit()
        return embed
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


async def find_by_token(session: AsyncSession, token: str):
    try:
        result = await session.execute(
            select(EmbedToken).where(EmbedToken.embed_token == token)
        )
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
