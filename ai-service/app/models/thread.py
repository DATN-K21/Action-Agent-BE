from sqlalchemy import Column, ForeignKey, String

from app.models.base_entity import BaseEntity


class Thread(BaseEntity):
    """
    Represents a thread in the application. This model stores information about the thread's title,
    type, and the user who created it. Threads can be used to organize conversations or discussions
    within the application.
    """
    __tablename__ = "threads"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=True)
    thread_type = Column(String, nullable=True)
    assistant_id = Column(String, ForeignKey("assistants.id"), nullable=True)

    # user = relationship("User", back_populates="threads", passive_deletes=True)
    # assistant = relationship("Assistant", back_populates="threads", passive_deletes=True)
