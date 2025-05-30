from sqlalchemy import Column, ForeignKey, String

from app.db_models.base_entity import BaseEntity


class MemberUploadLink(BaseEntity):
    __tablename__ = "member_upload_links"

    member_id: str = Column(String, ForeignKey("members.id"), primary_key=True)
    upload_id: str = Column(String, ForeignKey("uploads.id"), primary_key=True)
