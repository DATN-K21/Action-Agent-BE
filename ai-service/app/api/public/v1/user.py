from datetime import datetime

from fastapi import APIRouter, Header
from sqlalchemy import and_, delete, select, update

from app.api.deps import SessionDep
from app.core import logging
from app.db_models.user import User
from app.db_models.user_api_key import UserApiKey
from app.schemas.base import ResponseWrapper
from app.schemas.user_api_key import (
    DeleteApiKeyRequest,
    DeleteApiKeyResponse,
    GetApiKeyResponse,
    GetApiKeysResponse,
    SetDefaultApiKeyRequest,
    SetDefaultApiKeyResponse,
    UpsertApiKeyRequest,
    UpsertApiKeyResponse,
)

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/key/get-all", summary="Get API Keys.", response_model=ResponseWrapper[GetApiKeyResponse])
async def aget_api_key(
    session: SessionDep,
    x_user_id: str,
):
    try:
        # Fetch user data with API keys
        stmt = (
            select(User)
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
            return ResponseWrapper.wrap(status=404, message="User not found").to_response()

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
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except Exception as e:
        logger.error(f"Error fetching user with API keys: {e}")
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


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
                return ResponseWrapper.wrap(status=404, message="API key not found").to_response()

        # Update the user's default API key
        update_stmt = (
            update(User)
            .where(
                User.id == x_user_id,
                User.is_deleted.is_(False),
            )
            .values(default_api_key_id=api_key_id)
            .returning(User.default_api_key_id)
        )

        result = await session.execute(update_stmt)
        updated_default_api_key_id = result.scalar_one_or_none()

        if api_key_id and not updated_default_api_key_id:
            return ResponseWrapper.wrap(status=404, message="User not found").to_response()

        await session.commit()

        response_data = SetDefaultApiKeyResponse()
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except Exception as e:
        logger.error(f"Error setting default API key: {e}")
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


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
                return ResponseWrapper.wrap(status=404, message="API key not found").to_response()

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

            response_data = UpsertApiKeyResponse.model_validate(new_api_key)

        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except Exception as e:
        logger.error(f"Error upserting API key: {e}")
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.delete("/{user_id}/key/delete", summary="Delete API Key.", response_model=ResponseWrapper[DeleteApiKeyResponse])
async def delete_api_key(
    session: SessionDep,
    request: DeleteApiKeyRequest,
    x_user_id: str = Header(None),
):
    try:
        stmt = (
            delete(UserApiKey)
            .where(
                UserApiKey.user_id == x_user_id,
                UserApiKey.provider == request.provider,
                UserApiKey.is_deleted.is_(False),
            )
            .returning(UserApiKey.id)
        )

        result = await session.execute(stmt)
        deleted_api_key_id = result.scalar_one_or_none()

        if not deleted_api_key_id:
            return ResponseWrapper.wrap(status=404, message="API key not found").to_response()

        await session.commit()
        response_data = DeleteApiKeyResponse()
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except Exception as e:
        logger.error(f"Error deleting API key: {e}", exc_info=True)
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()
