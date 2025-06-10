from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db_models.base_entity import BaseEntity


class MemberUploadLink(BaseEntity):
    __tablename__ = "member_upload_links"

    member_id: Mapped[str] = mapped_column(ForeignKey("members.id"), primary_key=True)
    upload_id: Mapped[str] = mapped_column(ForeignKey("uploads.id"), primary_key=True)
