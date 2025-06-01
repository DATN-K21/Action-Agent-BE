from sqlalchemy import Column, ForeignKey, String, UniqueConstraint, Numeric, Boolean
from sqlalchemy.orm import relationship

from app.db_models.base_entity import BaseEntity


class Member(BaseEntity):
    __tablename__ = "members"
    __table_args__ = (
        UniqueConstraint("name", "team_id", name="unique_team_and_name"),
    )

    name: str = Column(String(64), unique=True, nullable=False)
    team_id: str = Column(String, ForeignKey("teams.id"), nullable=False)

    backstory: str | None = Column(String, nullable=True)
    role: str | None = Column(String, nullable=True)
    type: str | None = Column(String, nullable=True)  # one of: leader, worker, freelancer
    position_x: float | None = Column(Numeric, nullable=True)
    position_y: float | None = Column(Numeric, nullable=True)
    source: str | None = Column(String, nullable=True)
    provider: str | None = Column(String, nullable=True)
    model: str | None = Column(String, nullable=True)
    temperature: float | None = Column(Numeric, default=0.1, nullable=True)
    interrupt: bool | None = Column(Boolean, default=False, nullable=True)

    team = relationship("Team", back_populates="members")

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
