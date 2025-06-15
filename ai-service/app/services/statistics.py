from datetime import datetime

from sqlalchemy import func, select

from app.api.deps import SessionDep
from app.core import logging
from app.core.enums import DateRangeEnum
from app.core.utils.date_range import get_period_range
from app.db_models import (
    ConnectedExtension,
    Thread,
    User,
)
from app.schemas.statistics import (
    ConnectedExtensionStatisticsResponse,
    ThreadStatisticsResponse,
    UserStatisticsResponse,
)

logger = logging.get_logger(__name__)

now = datetime.utcnow()
first_day_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

def get_percentage_change(current: int, previous: int) -> str:
    if previous == 0:
        return "1000.0+" if current > 0 else "0.0%"
    else:
        return f"{((current - previous) / previous) * 100:.1f}%"


async def get_user_statistics(session: SessionDep, period: DateRangeEnum) -> UserStatisticsResponse:
    start_date, end_date = get_period_range(period)
    if start_date is None or end_date is None:
        stmt = select(
            func.count(User.id).filter(User.is_deleted.is_(False)).label("total"),
            func.count(User.id).filter(User.is_deleted.is_(False)).label("previous_total"),
        )
    else:
        stmt = select(
            func.count(User.id).filter(User.is_deleted.is_(False), User.created_at >= start_date, User.created_at < end_date).label("total"),
            func.count(User.id).filter(User.is_deleted.is_(False), User.created_at >= start_date, User.created_at < end_date).label("previous_total"),
        )

    result = await session.execute(stmt)
    row = result.one()
    total_users = row.total
    previous_total = row.previous_total

    # Calculate average per day (over 30 days)
    avg_per_day = total_users / 30 if total_users > 0 else 0

    percentage_change = get_percentage_change(total_users, previous_total)
    return UserStatisticsResponse(total=total_users, avg_per_day=avg_per_day, percentage_change=percentage_change)


async def get_connected_extension_statistics(session: SessionDep, period: str) -> ConnectedExtensionStatisticsResponse:
    stmt = select(
        func.count(ConnectedExtension.id).filter(ConnectedExtension.is_deleted.is_(False)).label("total"),
        func.count(ConnectedExtension.id)
        .filter(ConnectedExtension.is_deleted.is_(False), ConnectedExtension.created_at < first_day_of_this_month)
        .label("last_month_total"),
    )

    result = await session.execute(stmt)
    row = result.one()
    total_extensions = row.total
    last_month_total = row.last_month_total

    # Calculate average per day (over 30 days)
    avg_per_day = total_extensions / 30 if total_extensions > 0 else 0

    # Calculate percentage change compared to last month
    percentage_change = get_percentage_change(total_extensions, last_month_total)
    return ConnectedExtensionStatisticsResponse(total=total_extensions, avg_per_day=avg_per_day, percentage_change=percentage_change)


async def get_thread_statistics(session: SessionDep, period: str) -> ThreadStatisticsResponse:
    """
    Get the total number of threads created in the current month.
    """
    stmt = select(
        func.count(Thread.id).filter(Thread.is_deleted.is_(False)).label("total"),
        func.count(Thread.id).filter(Thread.is_deleted.is_(False), Thread.created_at < first_day_of_this_month).label("last_month_total"),
    )

    result = await session.execute(stmt)
    row = result.one()
    total_threads = row.total
    last_month_total = row.last_month_total

    # Calculate average per day (over 30 days)
    avg_per_day = total_threads / 30 if total_threads > 0 else 0

    # Calculate percentage change compared to last month
    percentage_change = get_percentage_change(total_threads, last_month_total)
    return ThreadStatisticsResponse(total=total_threads, avg_per_day=avg_per_day, percentage_change=percentage_change)