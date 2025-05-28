from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.models import MemberBase
from app.db_models.base_entity import BaseEntity


class Member(MemberBase, BaseEntity):
    __tablename__ = "members"
    __table_args__ = (
        UniqueConstraint("name", "belongs_to", name="unique_team_and_name"),
    )

    name = Column(String, nullable=False)
    belongs_to = Column(String, ForeignKey("teams.id"), nullable=False)

    belongs = relationship("Team", back_populates="members")

    skills = relationship(
        "Skill",
        secondary="member_skills_link",
        back_populates="members"
    )

    uploads = relationship(
        "Upload",
        secondary="member_uploads_link",
        back_populates="members"
    )
