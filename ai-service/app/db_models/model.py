from typing import Any, Dict, List, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db_models.base_entity import BaseEntity  # Adjust as needed


class Model(BaseEntity):
    __tablename__ = "models"

    # AI model name with max length 128 characters, cannot be null
    ai_model_name: Mapped[str] = mapped_column(String(128), nullable=False)

    # Foreign key reference to ModelProvider table
    provider_id: Mapped[str] = mapped_column(String, ForeignKey("model_providers.id"), nullable=False)

    # Categories stored as PostgreSQL string array
    categories: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)

    # Capabilities stored as PostgreSQL string array, default empty list
    capabilities: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=[])

    # Metadata stored as JSONB, default empty JSON object
    metadata_: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")

    # Relationship to the provider (ModelProvider)
    provider = relationship("ModelProvider", back_populates="models")
