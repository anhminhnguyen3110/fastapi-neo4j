from sqlalchemy import Column, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import datetime
import uuid

Base = declarative_base()


class EmbedToken(Base):
    __tablename__ = "embed_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    embed_token = Column(String, unique=True, nullable=False)
    cypher_query = Column(Text, nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.datetime.utcnow)
