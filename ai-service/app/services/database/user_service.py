import traceback
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import logging
from app.models import User
from app.schemas.base import PagingRequest, ResponseWrapper
from app.schemas.user import (
    CreateUserRequest,
    CreateUserResponse,
    DeleteUserResponse,
    GetListUsersResponse,
    GetUserResponse,
    UpdateUserRequest,
)
from app.utils.constants import SYSTEM

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
                created_by=SYSTEM,
            )

            self.db.add(db_user)
            await self.db.commit()
            await self.db.refresh(db_user)

            response_data = CreateUserResponse.model_validate(db_user)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.error(f"Has error: {str(e)}", exec_info=e, traceback=traceback.format_exc())
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def get_user_by_id(self, user_id: str) -> ResponseWrapper[GetUserResponse]:
        """Get a user by user_id."""
        try:
            stmt = (
                select(
                    User.id,
                    User.username,
                    User.email,
                    User.first_name,
                    User.last_name,
                    User.created_at,
                )
                .where(
                    User.id == user_id,
                    User.is_deleted.is_(False),
                )
                .limit(1)
            )

            result = await self.db.execute(stmt)
            db_user = result.scalar_one_or_none()

            if not db_user:
                return ResponseWrapper.wrap(status=404, message="User not found")

            response_data = GetUserResponse.model_validate(db_user)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.error(f"Has error: {str(e)}", exec_info=e, traceback=traceback.format_exc())
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def get_all_users(self, paging: PagingRequest) -> ResponseWrapper[GetListUsersResponse]:
        """Get all users."""
        logger.info(f"Get all users: {paging.model_dump()}")
        try:
            stmt = (
                select(
                    User.id,
                    User.username,
                    User.email,
                    User.first_name,
                    User.last_name,
                    User.created_at,
                )
                .where(
                    User.is_deleted.is_(False),
                )
                .offset(paging.pageNumber * paging.maxPerPage)
                .limit(paging.maxPerPage)
                .order_by(User.created_at.desc())
            )

            result = await self.db.execute(stmt)
            db_users = result.scalars().all()

            response_data = [GetUserResponse.model_validate(db_user) for db_user in db_users]
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.exception(f"Has error: {str(e)}", exec_info=e, traceback=traceback.format_exc())
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
                .values(**user.model_dump())
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
            logger.error(f"Has error: {str(e)}", exec_info=e, traceback=traceback.format_exc())
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
                    deleted_by=deleted_by,
                    deleted_at=datetime.now(timezone.utc),
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
            logger.error(f"Has error: {str(e)}", exec_info=e, traceback=traceback.format_exc())
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")
