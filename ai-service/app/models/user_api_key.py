from sqlalchemy import Column, Enum, ForeignKey, Index, String

from app.core.enums.llm_provider import LLM_Provider
from app.models.base_entity import BaseEntity


class UserApiKey(BaseEntity):
    __tablename__ = "user_api_keys"

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    provider = Column(Enum(LLM_Provider), nullable=False)
    encrypted_value = Column(String, nullable=False)

    __table_args__ = Index(
        "idx_user_api_keys_user_id_provider",
        "user_id",
        "provider",
    )
