from pydantic import Field, field_validator

from app.core.enums.llm_provider import LLM_Provider
from app.schemas.base import BaseRequest, BaseResponse


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class GetApiKeyRequest(BaseRequest):
    user_id: str = Field(..., min_length=1, max_length=100)


class SetDefaultProviderRequest(BaseRequest):
    user_id: str = Field(..., min_length=1, max_length=100)
    provider: LLM_Provider = Field(..., min_length=1, max_length=50)

    @field_validator("provider")
    def validate_provider(cls, provider: LLM_Provider) -> LLM_Provider:
        if provider not in LLM_Provider:
            raise ValueError(f"Invalid provider: {provider}. Must be one of {list(LLM_Provider)}.")
        return provider


class UpsertApiKeyRequest(BaseRequest):
    user_id: str = Field(..., min_length=1, max_length=100)
    value: str = Field(..., min_length=1, max_length=1000)
    provider: LLM_Provider = Field(..., min_length=1, max_length=50)

    @field_validator("value")
    def validate_value(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value cannot be empty or whitespace.")
        return value.strip()

    @field_validator("provider")
    def validate_provider(cls, provider: LLM_Provider) -> LLM_Provider:
        if provider not in LLM_Provider:
            raise ValueError(f"Invalid provider: {provider}. Must be one of {list(LLM_Provider)}.")
        return provider


class DeleteApiKeyRequest(BaseRequest):
    user_id: str = Field(..., min_length=1, max_length=100)
    provider: LLM_Provider = Field(..., min_length=1, max_length=50)

    @field_validator("provider")
    def validate_provider(cls, provider: LLM_Provider) -> LLM_Provider:
        if provider not in LLM_Provider:
            raise ValueError(f"Invalid provider: {provider}. Must be one of {list(LLM_Provider)}.")
        return provider


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class GetApiKeyResponse(BaseResponse):
    value: str = Field(..., min_length=1, max_length=1000)
    provider: LLM_Provider = Field(..., min_length=1, max_length=50)


class GetApiKeysResponse(BaseResponse):
    user_id: str = Field(..., min_length=1, max_length=100)
    api_keys: list[GetApiKeyResponse]


class SetDefaultProviderResponse(BaseResponse):
    pass


class UpsertApiKeyResponse(BaseResponse):
    pass


class DeleteApiKeyResponse(BaseResponse):
    pass
