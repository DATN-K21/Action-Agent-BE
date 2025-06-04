from fastapi import APIRouter, Depends, Header
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import SessionDep
from app.core import logging
from app.db_models.connected_extension import ConnectedExtension
from app.schemas.base import PagingRequest, ResponseWrapper
from app.schemas.connected_extension import GetConnectedExtensionResponse, GetConnectedExtensionsResponse

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/connected-extension", tags=["API-V2 | Connected Extension"])


@router.get("/get-all", summary="Get all connections.", response_model=ResponseWrapper[GetConnectedExtensionsResponse])
async def aget_all(
    session: SessionDep,
    paging: PagingRequest = Depends(),
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
):
    try:
        page_number = paging.page_number if paging else 1
        max_per_page = paging.max_per_page if paging else 10

        if x_user_role == "admin" or x_user_role == "super_admin":
            # COUNT total connected apps
            count_stmt = select(func.count(ConnectedExtension.id)).where(
                ConnectedExtension.is_deleted.is_(False),
            )

            statement = (
                select(ConnectedExtension)
                .where(ConnectedExtension.is_deleted.is_(False))
                .offset((page_number - 1) * max_per_page)
                .limit(max_per_page)
                .order_by(ConnectedExtension.created_at.desc())
            )

        else:
            count_stmt = select(func.count(ConnectedExtension.id)).where(
                ConnectedExtension.user_id == x_user_id,
                ConnectedExtension.is_deleted.is_(False),
            )

            statement = (
                select(ConnectedExtension)
                .where(
                    ConnectedExtension.user_id == x_user_id,
                    ConnectedExtension.is_deleted.is_(False),
                )
                .offset((page_number - 1) * max_per_page)
                .limit(max_per_page)
                .order_by(ConnectedExtension.created_at.desc())
            )

        count_result = await session.execute(count_stmt)
        count = count_result.scalar_one()

        if count == 0:
            return ResponseWrapper.wrap(
                status=200,
                data=GetConnectedExtensionsResponse(connected_extensions=[], page_number=page_number, max_per_page=max_per_page, total_page=0),
            )

        total_pages = (count + max_per_page - 1) // max_per_page

        result = await session.execute(statement)
        connected_extensions = result.scalars().all()

        wrapped_connected_extensions = [
            GetConnectedExtensionResponse.model_validate(connected_extension) for connected_extension in connected_extensions
        ]

        return ResponseWrapper.wrap(
            status=200,
            data=GetConnectedExtensionsResponse(
                connected_extensions=wrapped_connected_extensions, page_number=page_number, max_per_page=max_per_page, total_page=total_pages
            ),
        ).to_response()

    except SQLAlchemyError as e:
        # Handle database-specific errors
        logger.error("Database error: %s", str(e), exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Database error occurred").to_response

    except Exception as e:
        # Handle any other exceptions
        logger.error("Has error: %s", str(e), exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.get("/{connected_extension_id}/get-detail", summary="Get detail connection.", response_model=ResponseWrapper[GetConnectedExtensionResponse])
async def aget_detail(
    session: SessionDep,
    connected_extension_id: str,
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
):
    try:
        if x_user_role == "admin" or x_user_role == "super_admin":
            statement = (
                select(ConnectedExtension)
                .where(
                    ConnectedExtension.id == connected_extension_id,
                    ConnectedExtension.is_deleted.is_(False),
                )
                .limit(1)
            )
        else:
            statement = (
                select(ConnectedExtension.connected_account_id)
                .where(
                    ConnectedExtension.user_id == x_user_id,
                    ConnectedExtension.id == connected_extension_id,
                    ConnectedExtension.is_deleted.is_(False),
                )
                .limit(1)
            )

        result = await session.execute(statement)
        connected_extension = result.scalar_one()
        connected_extension_data = GetConnectedExtensionResponse.model_validate(connected_extension)
        return ResponseWrapper.wrap(status=200, data=connected_extension_data).to_response()

    except SQLAlchemyError as e:
        # Handle database-specific errors
        logger.error("Database error: %s", str(e), exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Database error occurred").to_response

    except Exception as e:
        logger.exception("Has error: %s", str(e))
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()
