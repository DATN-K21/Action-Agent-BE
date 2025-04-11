import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class BaseEntity(Base):
    """
    Base class for all entities in the application. This class provides common attributes and methods
    for all entities, such as `id`, `created_by`, `created_at`, `is_deleted`, and `deleted_at`.
    """
    __abstract__ = True  # This ensures SQLAlchemy does not treat this as a table

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id}>"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def __hash__(self):
        return hash(self.id)
