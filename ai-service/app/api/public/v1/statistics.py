from fastapi import APIRouter

from app.api.deps import SessionDep
from app.core import logging
from app.core.enums import DateRangeEnum
from app.schemas.base import ResponseWrapper
from app.schemas.statistics import BaseStatisticsResponse
from app.services.statistics import (
    get_connected_extension_statistics,
    get_thread_statistics,
    get_user_statistics,
)

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/statistics", tags=["Statistics"])


@router.get("/overview", summary="Get Statistics Overview.", response_model=dict)
async def get_statistics_overview(session: SessionDep, period: DateRangeEnum = DateRangeEnum.ALL_TIME):
    """
    Endpoint to retrieve an overview of statistics.
    This is a placeholder implementation.
    """

    # The result data for statistics
    statistics_data = {}

    # USER STATISTICS
    try:
        user_statistics = await get_user_statistics(session=session, period=period)
        if user_statistics is None:
            raise ValueError("Invalid user statistics data")

        statistics_data["users"] = user_statistics
    except Exception as e:
        logger.error(f"Error fetching user statistics: {e}")
        return ResponseWrapper.wrap(status=500, message=f"Internal server error: {e}").to_response()

    # CONNECTED EXTENSION STATISTICS
    try:
        extension_statistics = await get_connected_extension_statistics(
            session=session, period=period
        )  # Assuming a similar function exists for extensions
        if extension_statistics is None:
            raise ValueError("Invalid extension statistics data")

        statistics_data["connected_extensions"] = extension_statistics
    except Exception as e:
        logger.error(f"Error fetching extension statistics: {e}")
        return ResponseWrapper.wrap(status=500, message=f"Internal server error: {e}").to_response()

    # THREAD STATISTICS
    try:
        thread_statistics = await get_thread_statistics(session=session, period=period)
        if thread_statistics is None:
            raise ValueError("Invalid thread statistics data")

        statistics_data["threads"] = thread_statistics
    except Exception as e:
        logger.error(f"Error fetching thread statistics: {e}")
        return ResponseWrapper.wrap(status=500, message=f"Internal server error: {e}").to_response()

    # Construct the response object
    result = BaseStatisticsResponse(
        users=statistics_data["users"], connected_extensions=statistics_data["connected_extensions"], threads=statistics_data["threads"]
    )
    return ResponseWrapper.wrap(status=200, data=result).to_response()
