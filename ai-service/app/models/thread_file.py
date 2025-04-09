from sqlalchemy import Column, Integer, String

from app.models.base_entity import BaseEntity


class ThreadFile(BaseEntity):
    __tablename__ = "thread_files"

    url = Column(String, nullable=False)
    name = Column(String, nullable=False)
    size = Column(Integer, nullable=False)

    status = Column(Integer, nullable=False, default=0)  # 0: failed, 1: uploaded, 2: vectorizing, 3: vectorized
    error_message = Column(String, nullable=True)
