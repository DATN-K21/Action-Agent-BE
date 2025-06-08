from sqlalchemy import Column, ForeignKey, String

from app.db_models.base_entity import BaseEntity


class TeamAssistantLink(BaseEntity):
    __tablename__ = "team_assistant_links"

    team_id = Column(String, ForeignKey("teams.id"), primary_key=True)
    assistant_id = Column(String, ForeignKey("assistants.id"), primary_key=True)
