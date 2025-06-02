
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db_models.base_entity import BaseEntity  # Adjust according to your project structure


class Subgraph(BaseEntity):
    __tablename__ = "subgraphs"

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    assistant_id = Column(String, ForeignKey("assistants.id"), nullable=False)
    name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    config = Column(JSONB, nullable=False, default=dict)
    metadata_ = Column("metadata", JSONB, nullable=False, default=dict)
    is_public = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
    )

    # Relationships
    user = relationship("User", back_populates="subgraphs")
    assistant = relationship("Assistant", back_populates="subgraphs")
