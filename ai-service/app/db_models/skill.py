from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db_models.base_entity import BaseEntity


class Skill(BaseEntity):
    __tablename__ = "skills"

    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="skills")

    members = relationship(
        "Member",
        secondary="member_skills_link",
        back_populates="skills"
    )
