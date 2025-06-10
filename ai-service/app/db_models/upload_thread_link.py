from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db_models.base_entity import BaseEntity


class UploadThreadLink(BaseEntity):
    __tablename__ = "upload_thread_links"

    upload_id: Mapped[str] = mapped_column(ForeignKey("uploads.id"), primary_key=True)
    thread_id: Mapped[str] = mapped_column(ForeignKey("threads.id"), primary_key=True)
