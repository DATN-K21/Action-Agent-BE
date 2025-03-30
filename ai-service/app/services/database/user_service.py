from datetime import datetime
from typing import Optional

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import logging
from app.core.constants import SYSTEM, TRIAL_TOKENS
from app.core.enums import LlmProvider
from app.models import User
from app.models.user_api_key import UserApiKey
from app.schemas.base import PagingRequest, ResponseWrapper
from app.schemas.user import (
    CreateUserRequest,
    CreateUserResponse,
    DeleteUserResponse,
    GetListUsersResponse,
    GetUserResponse,
    UpdateUserRequest,
)
from app.schemas.user_api_key import DeleteApiKeyResponse, GetApiKeysResponse, SetDefaultApiKeyResponse, UpsertApiKeyResponse

logger = logging.get_logger(__name__)


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @logging.log_function_inputs(logger)
    async def create_user(self, user: CreateUserRequest) -> ResponseWrapper[CreateUserResponse]:
        """Create a new user in the database."""
        try:
            # 1. Check if user already exists
            stmt = (
                select(User.id)
                .where(
                    User.email == user.email,
                    User.is_deleted.is_(False),
                )
                .limit(1)
            )

            result = await self.db.execute(stmt)
            existing_user = result.scalar_one_or_none()
            if existing_user:
                return ResponseWrapper.wrap(status=400, message="User already exists")

            # 2. Create new user
            db_user = User(
                **user.model_dump(),
                default_api_key_id=None,
                remain_trial_tokens=TRIAL_TOKENS,
                created_by=SYSTEM,
            )

            self.db.add(db_user)
            await self.db.commit()
            await self.db.refresh(db_user)

            response_data = CreateUserResponse.model_validate(db_user)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.exception(f"Has error: {str(e)}", exc_info=True)
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def get_user_by_id(self, user_id: str) -> ResponseWrapper[GetUserResponse]:
        """Get a user by user_id."""
        try:
            stmt = (
                select(
                    User.id.label("id"),
                    User.username.label("username"),
                    User.email.label("email"),
                    User.first_name.label("first_name"),
                    User.last_name.label("last_name"),
                    User.created_at.label("created_at"),
                )
                .where(
                    User.id == user_id,
                    User.is_deleted.is_(False),
                )
                .limit(1)
            )

            result = await self.db.execute(stmt)
            db_user = result.mappings().one_or_none()
            logger.info(f"db_user: {db_user}")

            if not db_user:
                return ResponseWrapper.wrap(status=404, message="User not found")

            response_data = GetUserResponse.model_validate(db_user)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.exception(f"Has error: {str(e)}", exc_info=True)
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def get_all_users(self, paging: PagingRequest) -> ResponseWrapper[GetListUsersResponse]:
        """Get all users."""
        try:
            page_number = paging.page_number
            max_per_page = paging.max_per_page

            # COUNT total users
            count_stmt = select(func.count(User.id)).where(User.is_deleted.is_(False))
            count_result = await self.db.execute(count_stmt)
            total_users = count_result.scalar_one()
            logger.info(f"total_users: {total_users}")
            if total_users == 0:
                response_data = GetListUsersResponse(
                    users=[],
                    page_number=page_number,
                    max_per_page=max_per_page,
                    total_page=0,
                )
                return ResponseWrapper.wrap(status=200, data=response_data)
            total_pages = (total_users + max_per_page - 1) // max_per_page

            # GET users
            stmt = (
                select(
                    User.id.label("id"),
                    User.username.label("username"),
                    User.email.label("email"),
                    User.first_name.label("first_name"),
                    User.last_name.label("last_name"),
                    User.created_at.label("created_at"),
                )
                .where(
                    User.is_deleted.is_(False),
                )
                .offset((page_number - 1) * max_per_page)
                .limit(paging.max_per_page)
                .order_by(User.created_at.desc())
            )

            result = await self.db.execute(stmt)
            db_users = result.mappings().all()

            users = [GetUserResponse.model_validate(db_user) for db_user in db_users]
            response_data = GetListUsersResponse(
                users=users,
                page_number=paging.page_number,
                max_per_page=paging.max_per_page,
                total_page=total_pages,
            )
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.exception(f"Has error: {str(e)}", exc_info=True)
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def update_user(self, user_id: str, user: UpdateUserRequest) -> ResponseWrapper[CreateUserResponse]:
        """Update a user."""
        try:
            stmt = (
                update(User)
                .where(
                    User.id == user_id,
                    User.is_deleted.is_(False),
                )
                .values(**user.model_dump(exclude_unset=True))
                .returning(User)
            )

            result = await self.db.execute(stmt)
            db_user = result.scalar_one_or_none()
            if not db_user:
                return ResponseWrapper.wrap(status=404, message="User not found")

            await self.db.commit()
            await self.db.refresh(db_user)

            response_data = CreateUserResponse.model_validate(db_user)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.exception(f"Has error: {str(e)}", exc_info=True)
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def delete_user(self, user_id: str, deleted_by: str = SYSTEM) -> ResponseWrapper[DeleteUserResponse]:
        """Delete a user."""
        try:
            stmt = (
                update(User)
                .where(
                    User.id == user_id,
                    User.is_deleted.is_(False),
                )
                .values(
                    is_deleted=True,
                    deleted_at=datetime.now(),
                )
                .returning(User.id)
            )

            result = await self.db.execute(stmt)
            deleted_user_id = result.scalar_one_or_none()
            if not deleted_user_id:
                return ResponseWrapper.wrap(status=404, message="User not found")

            await self.db.commit()
            return ResponseWrapper.wrap(status=200, data=DeleteUserResponse(id=deleted_user_id))

        except Exception as e:
            logger.exception(f"Has error: {str(e)}", exc_info=True)
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def get_user_with_api_keys(self, user_id: str) -> ResponseWrapper[GetApiKeysResponse]:
        """Get user with API keys."""
        try:
            # Fetch user data with API keys
            stmt = (
                select(
                    User.id.label("user_id"),
                    User.default_api_key_id.label("default_api_key_id"),
                    User.remain_trial_tokens.label("remain_trial_tokens"),
                    UserApiKey.id.label("api_key_id"),
                    UserApiKey.provider.label("provider"),
                    UserApiKey.created_at.label("created_at"),
                )
                .join(UserApiKey, (User.id == UserApiKey.user_id) and (UserApiKey.is_deleted.is_(False)), isouter=True)
                .where(
                    User.id == user_id,
                    User.is_deleted.is_(False),
                )
            )

            result = await self.db.execute(stmt)
            db_records = result.mappings().all()
            logger.info(f"db_records: {db_records}")

            if not db_records:
                return ResponseWrapper.wrap(status=404, message="User not found")

            # Convert query result into structured object
            user_with_keys = None
            api_keys = []

            for record in db_records:
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

    @logging.log_function_inputs(logger)
    async def set_default_api_key(self, user_id: str, provider: Optional[LlmProvider]) -> ResponseWrapper[SetDefaultApiKeyResponse]:
        """Set default API key for a user."""
        try:
            if not provider:
                api_key_id = None
            else:
                # Fetch the API key for the given provider
                stmt = (
                    select(UserApiKey.id)
                    .where(
                        UserApiKey.user_id == user_id,
                        UserApiKey.provider == provider,
                        UserApiKey.is_deleted.is_(False),
                    )
                    .limit(1)
                )

                result = await self.db.execute(stmt)
                api_key_id = result.scalar_one_or_none()

                if not api_key_id:
                    return ResponseWrapper.wrap(status=404, message="API key not found")

            # Update the user's default API key
            update_stmt = (
                update(User)
                .where(
                    User.id == user_id,
                    User.is_deleted.is_(False),
                )
                .values(default_api_key_id=api_key_id)
                .returning(User.default_api_key_id)
            )

            result = await self.db.execute(update_stmt)
            updated_default_api_key_id = result.scalar_one_or_none()

            if api_key_id and not updated_default_api_key_id:
                return ResponseWrapper.wrap(status=404, message="User not found")

            await self.db.commit()

            response_data = SetDefaultApiKeyResponse()
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.error(f"Error setting default API key: {e}")
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def upsert_api_key(self, user_id: str, provider: LlmProvider, encrypted_value: str) -> ResponseWrapper[UpsertApiKeyResponse]:
        """Upsert API key for a user."""
        try:
            # Check if the API key already exists
            stmt = (
                select(UserApiKey.id)
                .where(
                    UserApiKey.user_id == user_id,
                    UserApiKey.provider == provider,
                    UserApiKey.is_deleted.is_(False),
                )
                .limit(1)
            )

            result = await self.db.execute(stmt)
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
                        encrypted_value=encrypted_value,
                        created_at=datetime.utcnow(),
                        created_by=user_id,
                    )
                    .returning(UserApiKey.id, UserApiKey.provider, UserApiKey.created_at)
                )

                result = await self.db.execute(update_stmt)
                updated_api_key = result.mappings().one_or_none()

                if not updated_api_key:
                    return ResponseWrapper.wrap(status=404, message="API key not found")

                await self.db.commit()
                response_data = SetDefaultApiKeyResponse.model_validate(updated_api_key)

            else:
                # Create a new API key
                new_api_key = UserApiKey(
                    user_id=user_id,
                    provider=provider,
                    encrypted_value=encrypted_value,
                    created_by=user_id,
                )

                self.db.add(new_api_key)
                await self.db.commit()
                await self.db.refresh(new_api_key)

                response_data = SetDefaultApiKeyResponse.model_validate(new_api_key)

            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.error(f"Error upserting API key: {e}")
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def delete_api_key(self, user_id: str, provider: LlmProvider) -> ResponseWrapper[DeleteApiKeyResponse]:
        """Delete an API key."""
        try:
            stmt = (
                delete(UserApiKey)
                .where(
                    UserApiKey.user_id == user_id,
                    UserApiKey.provider == provider,
                    UserApiKey.is_deleted.is_(False),
                )
                .returning(UserApiKey.id)
            )

            result = await self.db.execute(stmt)
            deleted_api_key_id = result.scalar_one_or_none()

            if not deleted_api_key_id:
                return ResponseWrapper.wrap(status=404, message="API key not found")

            await self.db.commit()
            response_data = DeleteApiKeyResponse()
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.error(f"Error deleting API key: {e}")
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")