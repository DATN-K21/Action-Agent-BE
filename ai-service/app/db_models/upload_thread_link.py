from sqlalchemy import Column, ForeignKey, String

from app.db_models.base_entity import BaseEntity


class UploadThreadLink(BaseEntity):
    __tablename__ = "upload_thread_links"

    upload_id = Column(String, ForeignKey("uploads.id"), primary_key=True)
    thread_id = Column(String, ForeignKey("threads.id"), primary_key=True)
