from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.db.models.base import AuditBase


class User(AuditBase):
    __tablename__ = "users"
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)

    threads = relationship(
        "Thread",
        back_populates="user",
        cascade="all, delete",
        lazy="select"
    )
