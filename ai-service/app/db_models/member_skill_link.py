from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db_models.base_entity import BaseEntity


class MemberSkillLink(BaseEntity):
    __tablename__ = "member_skill_links"

    member_id: Mapped[str] = mapped_column(ForeignKey("members.id"), primary_key=True)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id"), primary_key=True)
