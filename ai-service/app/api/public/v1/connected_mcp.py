from datetime import datetime

from fastapi import APIRouter, Depends, Header
from sqlalchemy import func, select, update
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import SessionDep
from app.core import logging
from app.db_models.connected_mcp import ConnectedMcp
from app.schemas.base import MessageResponse, PagingRequest, ResponseWrapper
from app.schemas.connected_mcp import (
    CreateConnectedMcpRequest,
    CreateConnectedMcpResponse,
    GetConnectedMcpResponse,
    GetConnectedMcpsResponse,
    UpdateConnectedMcpRequest,
    UpdateConnectedMcpResponse,
)

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/mcp", tags=["Connected MCP"])


@router.get("/get-all", summary="Get all connected mcps of a user.", response_model=ResponseWrapper[GetConnectedMcpsResponse])
async def aget_all(session: SessionDep, paging: PagingRequest = Depends(), x_user_id: str = Header(None), x_user_role: str = Header(None)):
    try:
        page_number = paging.page_number if paging else 1
        max_per_page = paging.max_per_page if paging else 10

        if x_user_role == "admin" or x_user_role == "super_admin":
            # COUNT total connected mcps
            count_stmt = select(func.count(ConnectedMcp.id)).where(
                ConnectedMcp.is_deleted.is_(False),
            )

            statement = (
                select(ConnectedMcp)
                .where(ConnectedMcp.is_deleted.is_(False))
                .offset((page_number - 1) * max_per_page)
                .limit(max_per_page)
                .order_by(ConnectedMcp.created_at.desc())
            )

        else:
            count_stmt = select(func.count(ConnectedMcp.id)).where(
                ConnectedMcp.user_id == x_user_id,
                ConnectedMcp.is_deleted.is_(False),
            )

            statement = (
                select(ConnectedMcp)
                .where(
                    ConnectedMcp.user_id == x_user_id,
                    ConnectedMcp.is_deleted.is_(False),
                )
                .offset((page_number - 1) * max_per_page)
                .limit(max_per_page)
                .order_by(ConnectedMcp.created_at.desc())
            )

        count_result = await session.execute(count_stmt)
        count = count_result.scalar_one()

        if count == 0:
            return ResponseWrapper.wrap(
                status=200,
                data=GetConnectedMcpsResponse(connected_mcps=[], page_number=page_number, max_per_page=max_per_page, total_page=0),
            )

        total_page = (count + max_per_page - 1) // max_per_page

        result = await session.execute(statement)
        connected_mcps = result.scalars().all()
        wrapped_connected_mcps = [GetConnectedMcpResponse.model_validate(connected_mcp) for connected_mcp in connected_mcps]
        return ResponseWrapper.wrap(
            status=200,
            data=GetConnectedMcpsResponse(
                connected_mcps=wrapped_connected_mcps, page_number=page_number, max_per_page=max_per_page, total_page=total_page
            ),
        ).to_response()

    except SQLAlchemyError as e:
        logger.error(f"Error fetching connected mcps: {e}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Database error occurred").to_response()

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.post("/create", summary="Create a new mcp.", response_model=ResponseWrapper[CreateConnectedMcpResponse])
async def acreate(
    session: SessionDep,
    request: CreateConnectedMcpRequest,
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
):
    try:
        connected_mcp = ConnectedMcp(
            user_id=x_user_id,
            mcp_name=request.mcp_name,
            url=request.url,
            transport=request.transport,
            description=request.description,
        )

        session.add(connected_mcp)
        await session.commit()
        await session.refresh(connected_mcp)

        response_data = CreateConnectedMcpResponse.model_validate(connected_mcp)
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except SQLAlchemyError as e:
        logger.error(f"Database error when creating connected mcp: {e}", exc_info=True)
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Database error occurred").to_response()

    except Exception as e:
        logger.error(f"Error creating connected mcp: {e}", exc_info=True)
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.get("/{connected_mcp_id}/get-detail", summary="Get connected mcp details.", response_model=ResponseWrapper[GetConnectedMcpResponse])
async def aget_detail(
    session: SessionDep,
    connected_mcp_id: str,
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
):
    try:
        if x_user_role in ["admin", "super_admin"]:
            statement = (
                select(ConnectedMcp)
                .where(
                    ConnectedMcp.id == connected_mcp_id,
                    ConnectedMcp.is_deleted.is_(False),
                )
                .limit(1)
            )
        else:
            statement = (
                select(ConnectedMcp)
                .where(
                    ConnectedMcp.user_id == x_user_id,
                    ConnectedMcp.id == connected_mcp_id,
                    ConnectedMcp.is_deleted.is_(False),
                )
                .limit(1)
            )

        result = await session.execute(statement)
        connected_mcp = result.scalar_one_or_none()

        if not connected_mcp:
            return ResponseWrapper.wrap(
                status=404,
                message="Connected MCP not found.",
            ).to_response()

        connected_mcp_data = GetConnectedMcpResponse.model_validate(connected_mcp)

        return ResponseWrapper.wrap(status=200, data=connected_mcp_data).to_response()

    except SQLAlchemyError as e:
        logger.error(f"Database error when fetching connected mcp details: {e}", exc_info=True)
        return ResponseWrapper.wrap(
            status=500,
            message="Database error occurred",
        ).to_response()

    except Exception as e:
        logger.error(f"Error fetching connected mcp details: {e}", exc_info=True)
        return ResponseWrapper.wrap(
            status=500,
            message="Internal server error",
        )


@router.patch("/{connected_mcp_id}/update", summary="Update connected mcp information.", response_model=ResponseWrapper[UpdateConnectedMcpResponse])
async def aupdate(
    session: SessionDep,
    connected_mcp_id: str,
    request: UpdateConnectedMcpRequest,
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
):
    try:
        if x_user_role in ["admin", "super_admin"]:
            statement = (
                update(ConnectedMcp)
                .where(
                    ConnectedMcp.id == connected_mcp_id,
                    ConnectedMcp.is_deleted.is_(False),
                )
                .values(**request.model_dump(exclude_unset=True))
            )
        else:
            statement = (
                update(ConnectedMcp)
                .where(
                    ConnectedMcp.user_id == x_user_id,
                    ConnectedMcp.id == connected_mcp_id,
                    ConnectedMcp.is_deleted.is_(False),
                )
                .values(**request.model_dump(exclude_unset=True))
            )

        result = await session.execute(statement)
        connecte_mcp = result.scalar_one_or_none()
        if not connecte_mcp:
            return ResponseWrapper.wrap(status=404, message="Thread not found")

        await session.commit()
        await session.refresh(connecte_mcp)

        response_data = UpdateConnectedMcpResponse.model_validate(connecte_mcp)
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except SQLAlchemyError as e:
        logger.error(f"Database error when updating connected mcp: {e}", exc_info=True)
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Database error occurred").to_response()

    except Exception as e:
        logger.error(f"Error updating connected mcp: {e}", exc_info=True)
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.delete("/{connected_mcp_id}/delete", summary="Delete a connected mcp.", response_model=ResponseWrapper[MessageResponse])
async def adelete(
    session: SessionDep,
    connected_mcp_id: str,
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
):
    try:
        if x_user_role in ["admin", "super_admin"]:
            statement = (
                update(ConnectedMcp)
                .where(
                    ConnectedMcp.id == connected_mcp_id,
                    ConnectedMcp.is_deleted.is_(False),
                )
                .values(
                    is_deleted=True,
                    deleted_at=datetime.now(),
                )
            )
        else:
            statement = (
                update(ConnectedMcp)
                .where(
                    ConnectedMcp.user_id == x_user_id,
                    ConnectedMcp.id == connected_mcp_id,
                    ConnectedMcp.is_deleted.is_(False),
                )
                .values(
                    is_deleted=True,
                    deleted_at=datetime.now(),
                )
            )

        # Execute the update statement
        await session.execute(statement)
        await session.commit()

        response_data = MessageResponse(message="Connected MCP deleted successfully")
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except SQLAlchemyError as e:
        logger.error(f"Database error when deleting connected mcp: {e}", exc_info=True)
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Database error occurred").to_response()

    except Exception as e:
        logger.error(f"Error deleting connected mcp: {e}", exc_info=True)
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()
