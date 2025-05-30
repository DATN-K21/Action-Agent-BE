from sqlalchemy import Column, ForeignKey, String

from app.db_models.base_entity import BaseEntity


class MemberSkillLink(BaseEntity):
    __tablename__ = "member_skill_links"

    member_id: str = Column(String, ForeignKey("members.id"), primary_key=True)
    skill_id: str = Column(String, ForeignKey("skills.id"), primary_key=True)
