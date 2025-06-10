from sqlalchemy import Boolean, Float, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db_models.base_entity import BaseEntity


class Member(BaseEntity):
    __tablename__ = "members"

    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    team_id: Mapped[str] = mapped_column(String, ForeignKey("teams.id"), nullable=False)

    backstory: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str | None] = mapped_column(String, nullable=True)
    type: Mapped[str | None] = mapped_column(String, nullable=True)  # one of: leader, worker, freelancer
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    provider: Mapped[str | None] = mapped_column(String, nullable=True)
    model: Mapped[str | None] = mapped_column(String, nullable=True)
    temperature: Mapped[float | None] = mapped_column(Float, default=0.1, nullable=True)
    interrupt: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)

    # For drag-and-drop positioning in the UI
    position_x: Mapped[Numeric | None] = mapped_column(Numeric, nullable=True)
    position_y: Mapped[Numeric | None] = mapped_column(Numeric, nullable=True)

    team = relationship("Team", back_populates="members")

    skills = relationship("Skill", secondary="member_skill_links", back_populates="members")

    uploads = relationship("Upload", secondary="member_upload_links", back_populates="members")
