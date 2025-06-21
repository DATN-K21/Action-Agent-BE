from fastapi import APIRouter

from app.api.deps import SessionDep
from app.core import logging
from app.core.enums import DateRangeEnum, StatisticsEntity
from app.schemas.base import ResponseWrapper
from app.schemas.statistics import BaseStatisticsResponse
from app.services.statistics import OverviewStatisticsService

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
        user_statistics = await OverviewStatisticsService.get_statistics_response(entity=StatisticsEntity.USERS, session=session, period=period)
        if user_statistics is None:
            raise ValueError("Invalid user statistics data")

        statistics_data["users"] = user_statistics
    except Exception as e:
        logger.error(f"Error fetching user statistics: {e}")
        return ResponseWrapper.wrap(status=500, message=f"Internal server error: {e}").to_response()

    # CONNECTED EXTENSION STATISTICS
    try:
        extension_statistics = await OverviewStatisticsService.get_statistics_response(
            entity=StatisticsEntity.CONNECTED_EXTENSIONS, session=session, period=period
        )
        if extension_statistics is None:
            raise ValueError("Invalid extension statistics data")

        statistics_data["connected_extensions"] = extension_statistics
    except Exception as e:
        logger.error(f"Error fetching extension statistics: {e}")
        return ResponseWrapper.wrap(status=500, message=f"Internal server error: {e}").to_response()

    # THREAD STATISTICS
    try:
        thread_statistics = await OverviewStatisticsService.get_statistics_response(entity=StatisticsEntity.THREADS, session=session, period=period)
        if thread_statistics is None:
            raise ValueError("Invalid thread statistics data")

        statistics_data["threads"] = thread_statistics
    except Exception as e:
        logger.error(f"Error fetching thread statistics: {e}")
        return ResponseWrapper.wrap(status=500, message=f"Internal server error: {e}").to_response()

    # ASSISTANTS STATISTICS
    try:
        assistant_statistics = await OverviewStatisticsService.get_statistics_response(
            entity=StatisticsEntity.ASSISTANTS, session=session, period=period
        )
        if assistant_statistics is None:
            raise ValueError("Invalid assistant statistics data")

        statistics_data["assistants"] = assistant_statistics
    except Exception as e:
        logger.error(f"Error fetching assistant statistics: {e}")
        return ResponseWrapper.wrap(status=500, message=f"Internal server error: {e}").to_response()

    # Construct the response object
    result = BaseStatisticsResponse(
        users=statistics_data["users"],
        connected_extensions=statistics_data["connected_extensions"],
        threads=statistics_data["threads"],
        assistants=statistics_data["assistants"],
    )
    return ResponseWrapper.wrap(status=200, data=result, message="Success").to_response()
