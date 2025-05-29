from sqlalchemy import Column, ForeignKey, String, UniqueConstraint, Numeric
from sqlalchemy.orm import relationship

from app.db_models.base_entity import BaseEntity


class Member(BaseEntity):
    __tablename__ = "members"
    __table_args__ = (
        UniqueConstraint("name", "belongs_to", name="unique_team_and_name"),
    )

    name = Column(String(64), unique=True, nullable=False)
    belongs_to = Column(String, ForeignKey("teams.id"), nullable=False)

    backstory = Column(String, nullable=True)
    role = Column(String, nullable=True)
    type = Column(String, nullable=True)  # one of: leader, worker, freelancer
    owner_of = Column(String, nullable=True)
    position_x = Column(Numeric, nullable=True)
    position_y = Column(Numeric, nullable=True)
    source = Column(String, nullable=True)
    provide = Column(String, nullable=True)
    model = Column(String, nullable=True)
    temperature = Column(Numeric, nullable=True)
    interrupt = Column(Numeric, nullable=True, default=False)

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
