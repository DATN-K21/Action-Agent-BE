from sqlalchemy import Column, ForeignKey, Integer, String

from app.models.base_entity import BaseEntity


class Message(BaseEntity):
    __tablename__ = "messages"

    thread_id = Column(String, ForeignKey("threads.id"), nullable=False)
    content = Column(String, nullable=False)
    format = Column(Integer, nullable=False)
    role = Column(Integer, nullable=False)

    # For interruption
    question = Column(String, nullable=True)
    choices = Column(String, nullable=True)
    answer_idx = Column(Integer, nullable=True)

    # For file upload
    file_id = Column(String, ForeignKey("thread_files.id"), nullable=True)
