from datetime import datetime

from fastapi import APIRouter, Header
from sqlalchemy import and_, select, update

from app.api.deps import SessionDep
from app.core import logging
from app.core.enums import LlmProvider
from app.db_models.user import User
from app.db_models.user_api_key import UserApiKey
from app.schemas.base import ResponseWrapper
from app.schemas.user_api_key import (
    DeleteApiKeyRequest,
    DeleteApiKeyResponse,
    GetApiKeysResponse,
    SetDefaultApiKeyRequest,
    SetDefaultApiKeyResponse,
    UpsertApiKeyRequest,
    UpsertApiKeyResponse,
)

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/key/get-all", summary="Get API Keys.", response_model=ResponseWrapper[GetApiKeysResponse])
async def aget_api_key(
    session: SessionDep,
    x_user_id: str = Header(None),
):
    try:
        # Fetch user data with API keys
        stmt = (
            select(
                User.id.label("user_id"),
                User.default_api_key_id,
                User.remain_trial_tokens,
                UserApiKey.id.label("api_key_id"),
                UserApiKey.provider,
                UserApiKey.created_at,
            )
            .join(UserApiKey, and_((User.id == UserApiKey.user_id), (UserApiKey.is_deleted.is_(False))), isouter=True)
            .where(
                User.id == x_user_id,
                User.is_deleted.is_(False),
            )
        )

        result = await session.execute(stmt)
        records = result.mappings().all()
        logger.info(f"db_records: {records}")

        if not records:
            return ResponseWrapper.wrap(status=404, message="User not found")

        # Convert query result into structured object
        user_with_keys = None
        api_keys = []

        for record in records:
            if not user_with_keys:
                user_with_keys = {
                    "user_id": record["user_id"],
                    "default_api_key_id": record["default_api_key_id"],
                    "remain_trial_tokens": record["remain_trial_tokens"],
                    "api_keys": [],
                }

            if record["api_key_id"]:
                api_keys.append(
                    {
                        "id": record["api_key_id"],
                        "provider": record["provider"],
                        "created_at": record["created_at"],
                    }
                )

        if user_with_keys:
            user_with_keys["api_keys"] = api_keys

        response_data = GetApiKeysResponse.model_validate(user_with_keys)
        return ResponseWrapper.wrap(status=200, data=response_data)

    except Exception as e:
        logger.error(f"Error fetching user with API keys: {e}")
        return ResponseWrapper.wrap(status=500, message="Internal server error")


@router.post("/key/set-default", summary="Set default API Key.", response_model=ResponseWrapper[SetDefaultApiKeyResponse])
async def aset_default_api_key(session: SessionDep, request: SetDefaultApiKeyRequest, x_user_id: str = Header(None)):
    try:
        if not request.provider:
            api_key_id = None
        else:
            # Fetch the API key for the given provider
            stmt = (
                select(UserApiKey.id)
                .where(
                    UserApiKey.user_id == x_user_id,
                    UserApiKey.provider == request.provider,
                    UserApiKey.is_deleted.is_(False),
                )
                .limit(1)
            )

            result = await session.execute(stmt)
            api_key_id = result.scalar_one_or_none()

            if not api_key_id:
                return ResponseWrapper.wrap(status=404, message="API key not found")

        # Update the user's default API key
        update_stmt = (
            update(User)
            .where(
                User.id == x_user_id,
                User.is_deleted.is_(False),
            )
            .values(default_api_key_id=api_key_id)
            .returning(User.id)
        )

        result = await session.execute(update_stmt)
        updated_user_id = result.scalar_one_or_none()

        if updated_user_id is None:
            await session.rollback()
            return ResponseWrapper.wrap(status=404, message="User not found")

        await session.commit()

        response_data = SetDefaultApiKeyResponse()
        return ResponseWrapper.wrap(status=200, data=response_data)

    except Exception as e:
        logger.error(f"Error setting default API key: {e}")
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal server error")


@router.put("/key/upsert", summary="Upsert API Key.", response_model=ResponseWrapper[UpsertApiKeyResponse])
async def upsert_api_key(
    session: SessionDep,
    request: UpsertApiKeyRequest,
    x_user_id: str = Header(None),
):
    try:
        # Check if the API key already exists
        stmt = (
            select(UserApiKey.id)
            .where(
                UserApiKey.user_id == x_user_id,
                UserApiKey.provider == request.provider,
                UserApiKey.is_deleted.is_(False),
            )
            .limit(1)
        )

        result = await session.execute(stmt)
        existing_api_key_id = result.scalar_one_or_none()

        if existing_api_key_id:
            # Update the existing API key
            update_stmt = (
                update(UserApiKey)
                .where(
                    UserApiKey.id == existing_api_key_id,
                    UserApiKey.is_deleted.is_(False),
                )
                .values(
                    encrypted_value=request.encrypted_value,
                    created_at=datetime.utcnow(),
                    created_by=x_user_id,
                )
                .returning(UserApiKey.id, UserApiKey.provider, UserApiKey.created_at)
            )

            result = await session.execute(update_stmt)
            updated_api_key = result.mappings().one_or_none()

            if not updated_api_key:
                await session.rollback()
                return ResponseWrapper.wrap(status=404, message="API key not found")

            await session.commit()
            response_data = UpsertApiKeyResponse.model_validate(updated_api_key)

        else:
            # Create a new API key
            new_api_key = UserApiKey(
                user_id=x_user_id,
                provider=request.provider,
                encrypted_value=request.encrypted_value,
                created_by=x_user_id,
            )

            session.add(new_api_key)
            await session.commit()
            await session.refresh(new_api_key)

            response_data = UpsertApiKeyResponse(
                id=new_api_key.id,
                provider=LlmProvider(new_api_key.provider),
                created_at=new_api_key.created_at,
            )

        return ResponseWrapper.wrap(status=200, data=response_data)

    except Exception as e:
        logger.error(f"Error upserting API key: {e}")
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal server error")


@router.delete("/key/delete", summary="Delete API Key.", response_model=ResponseWrapper[DeleteApiKeyResponse])
async def delete_api_key(
    session: SessionDep,
    request: DeleteApiKeyRequest,
    x_user_id: str = Header(None),
):
    try:
        # Soft delete by updating is_deleted flag
        stmt = (
            update(UserApiKey)
            .where(
                UserApiKey.user_id == x_user_id,
                UserApiKey.provider == request.provider,
                UserApiKey.is_deleted.is_(False),
            )
            .values(
                is_deleted=True,
                deleted_at=datetime.utcnow(),
            )
            .returning(UserApiKey.id)
        )

        result = await session.execute(stmt)
        deleted_api_key_id = result.scalar_one_or_none()

        if not deleted_api_key_id:
            await session.rollback()
            return ResponseWrapper.wrap(status=404, message="API key not found")

        await session.commit()
        response_data = DeleteApiKeyResponse()
        return ResponseWrapper.wrap(status=200, data=response_data)

    except Exception as e:
        logger.error(f"Error deleting API key: {e}", exc_info=True)
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal server error")
