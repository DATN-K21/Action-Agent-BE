from datetime import datetime
from typing import Optional

from pydantic import Field, field_validator

from app.core.enums import LlmProvider
from app.schemas.base import BaseRequest, BaseResponse


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class SetDefaultApiKeyRequest(BaseRequest):
    user_id: str = Field(..., min_length=1, max_length=100)
    provider: Optional[LlmProvider] = Field(...)

    @field_validator("provider")
    def validate_provider(cls, provider: Optional[LlmProvider]) -> Optional[LlmProvider]:
        if provider and provider not in LlmProvider:
            raise ValueError(f"Invalid provider: {provider}. Must be null or one of {list(LlmProvider)}.")
        return provider


class UpsertApiKeyRequest(BaseRequest):
    user_id: str = Field(..., min_length=1, max_length=100)
    encrypted_value: str = Field(..., min_length=1, max_length=1000)
    provider: LlmProvider = Field(...)

    @field_validator("encrypted_value")
    def validate_value(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value cannot be empty or whitespace.")
        return value.strip()

    @field_validator("provider")
    def validate_provider(cls, provider: LlmProvider) -> LlmProvider:
        if provider not in LlmProvider:
            raise ValueError(f"Invalid provider: {provider}. Must be one of {list(LlmProvider)}.")
        return provider


class DeleteApiKeyRequest(BaseRequest):
    user_id: str = Field(..., min_length=1, max_length=100)
    provider: LlmProvider = Field(...)

    @field_validator("provider")
    def validate_provider(cls, provider: LlmProvider) -> LlmProvider:
        if provider not in LlmProvider:
            raise ValueError(f"Invalid provider: {provider}. Must be one of {list(LlmProvider)}.")
        return provider


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class GetApiKeyResponse(BaseResponse):
    id: str
    provider: LlmProvider
    created_at: datetime


class GetApiKeysResponse(BaseResponse):
    user_id: str
    default_api_key_id: Optional[str]
    remain_trial_tokens: int
    api_keys: list[GetApiKeyResponse]


class SetDefaultApiKeyResponse(BaseResponse):
    pass


class UpsertApiKeyResponse(BaseResponse):
    id: str
    user_id: str
    provider: LlmProvider
    is_default: bool


class DeleteApiKeyResponse(BaseResponse):
    pass
