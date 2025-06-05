from sqlalchemy import Boolean, Column, Float, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db_models.base_entity import BaseEntity


class Member(BaseEntity):
    __tablename__ = "members"
    __table_args__ = UniqueConstraint("name", "assistant_id", name="unique_assistant_and_name")

    name = Column(String(64), unique=True, nullable=False)
    team_id = Column(String, ForeignKey("teams.id"), nullable=False)

    backstory = Column(String, nullable=True)
    role = Column(String, nullable=True)
    type = Column(String, nullable=True)  # one of: leader, worker, freelancer
    source = Column(String, nullable=True)
    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)
    temperature = Column(Float, default=0.1, nullable=True)
    interrupt = Column(Boolean, default=False, nullable=True)

    # For drag-and-drop positioning in the UI
    position_x = Column(Numeric, nullable=True)
    position_y = Column(Numeric, nullable=True)

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
