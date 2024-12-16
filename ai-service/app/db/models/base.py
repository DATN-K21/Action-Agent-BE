import uuid
from datetime import datetime

from sqlalchemy import DateTime, Column, String, UUID, Boolean
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class AuditBase(Base):
    __abstract__ = True  # This ensures SQLAlchemy does not treat this as a table
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow(), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    def delete(self):
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        return self

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id}>"

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)
