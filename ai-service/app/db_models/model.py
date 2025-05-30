from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.db_models.base_entity import BaseEntity  # Adjust as needed


class Model(BaseEntity):
    __tablename__ = "models"

    # AI model name with max length 128 characters, cannot be null
    ai_model_name: str = Column(String(128), nullable=False)

    # Foreign key reference to ModelProvider table
    provider_id: str = Column(String, ForeignKey("model_providers.id"), nullable=False)

    # Categories stored as PostgreSQL string array
    categories: str | None = Column(ARRAY(String), nullable=True)

    # Capabilities stored as PostgreSQL string array, default empty list
    capabilities = Column(ARRAY(String), nullable=False, default=[])

    # Metadata stored as JSONB, default empty JSON object
    meta_ = Column("metadata", JSONB, nullable=False, server_default="{}")

    # Relationship to the provider (ModelProvider)
    provider = relationship("ModelProvider", back_populates="models")
