from fastapi import APIRouter

from app.api.deps import SessionDep
from app.core import logging
from app.schemas.base import ResponseWrapper
from app.services.statistics import get_user_statistics

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/statistics", tags=["Statistics"])


@router.get("/overview", summary="Get Statistics Overview.", response_model=dict)
async def get_statistics_overview(session: SessionDep):
    """
    Endpoint to retrieve an overview of statistics.
    This is a placeholder implementation.
    """

    # Placeholder for actual statistics data
    statistics_data = {}

    # USER STATISTICS
    try:
        user_statistics = await get_user_statistics(session)
        if user_statistics is None or not isinstance(user_statistics, dict):
            raise ValueError("Invalid user statistics data")

        statistics_data["users"] = user_statistics
    except Exception as e:
        logger.error(f"Error fetching user statistics: {e}")
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()

    return statistics_data
