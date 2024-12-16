from sqlalchemy import Column, String, UUID, ForeignKey
from sqlalchemy.orm import relationship

from app.db.models.base import AuditBase


class Thread(AuditBase):
    __tablename__ = "threads"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=True)
    user = relationship("User", back_populates="threads", lazy="select")