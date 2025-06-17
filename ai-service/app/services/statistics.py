from sqlalchemy import func, select

from app.api.deps import SessionDep
from app.core import logging
from app.core.enums import DateRangeEnum
from app.core.utils.date_range import get_period_days, get_period_range, get_previous_period_range
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


def get_percentage_change(current: int, previous: int) -> str:
    if previous == 0:
        return "1000.0+" if current > 0 else "0.0%"
    else:
        return f"{((current - previous) / previous) * 100:.1f}$"


async def get_user_statistics(session: SessionDep, period: DateRangeEnum) -> UserStatisticsResponse:
    # Get current period range
    start_date, end_date = get_period_range(period)

    # Get actual number of days in the period
    period_days = get_period_days(period)

    if start_date is None or end_date is None:
        # For "all time" period, count all users
        stmt = select(func.count(User.id).filter(User.is_deleted.is_(False)).label("total"))
        result = await session.execute(stmt)
        total_users = result.scalar() or 0

        # For all time, there's no meaningful previous period comparison
        previous_total = 0
        avg_per_day = 0.0  # Can't calculate meaningful average for all time
    else:
        # Get previous period range for comparison
        prev_start_date, prev_end_date = get_previous_period_range(period)

        # Count users in current period
        current_stmt = select(
            func.count(User.id).filter(User.is_deleted.is_(False), User.created_at >= start_date, User.created_at < end_date).label("total")
        )
        current_result = await session.execute(current_stmt)
        total_users = current_result.scalar() or 0

        # Count users in previous period
        if prev_start_date is not None and prev_end_date is not None:
            previous_stmt = select(
                func.count(User.id)
                .filter(User.is_deleted.is_(False), User.created_at >= prev_start_date, User.created_at < prev_end_date)
                .label("previous_total")
            )
            previous_result = await session.execute(previous_stmt)
            previous_total = previous_result.scalar() or 0
        else:
            previous_total = 0

        # Calculate average per day based on actual period days
        avg_per_day = total_users / period_days if period_days and period_days > 0 else 0.0

    percentage_change = get_percentage_change(total_users, previous_total)
    return UserStatisticsResponse(total=total_users, avg_per_day=avg_per_day, percentage_change=percentage_change)


async def get_connected_extension_statistics(session: SessionDep, period: DateRangeEnum) -> ConnectedExtensionStatisticsResponse:
    # Get current period range
    start_date, end_date = get_period_range(period)

    # Get actual number of days in the period
    period_days = get_period_days(period)

    if start_date is None or end_date is None:
        # For "all time" period, count all extensions
        stmt = select(func.count(ConnectedExtension.id).filter(ConnectedExtension.is_deleted.is_(False)).label("total"))
        result = await session.execute(stmt)
        total_extensions = result.scalar() or 0

        # For all time, there's no meaningful previous period comparison
        previous_total = 0
        avg_per_day = 0.0  # Can't calculate meaningful average for all time
    else:
        # Get previous period range for comparison
        prev_start_date, prev_end_date = get_previous_period_range(period)

        # Count extensions in current period
        current_stmt = select(
            func.count(ConnectedExtension.id)
            .filter(ConnectedExtension.is_deleted.is_(False), ConnectedExtension.created_at >= start_date, ConnectedExtension.created_at < end_date)
            .label("total")
        )
        current_result = await session.execute(current_stmt)
        total_extensions = current_result.scalar() or 0

        # Count extensions in previous period
        if prev_start_date is not None and prev_end_date is not None:
            previous_stmt = select(
                func.count(ConnectedExtension.id)
                .filter(
                    ConnectedExtension.is_deleted.is_(False),
                    ConnectedExtension.created_at >= prev_start_date,
                    ConnectedExtension.created_at < prev_end_date,
                )
                .label("previous_total")
            )
            previous_result = await session.execute(previous_stmt)
            previous_total = previous_result.scalar() or 0
        else:
            previous_total = 0

        # Calculate average per day based on actual period days
        avg_per_day = total_extensions / period_days if period_days and period_days > 0 else 0.0

    percentage_change = get_percentage_change(total_extensions, previous_total)
    return ConnectedExtensionStatisticsResponse(total=total_extensions, avg_per_day=avg_per_day, percentage_change=percentage_change)


async def get_thread_statistics(session: SessionDep, period: DateRangeEnum) -> ThreadStatisticsResponse:
    """
    Get the total number of threads created in the specified period.
    """
    # Get current period range
    start_date, end_date = get_period_range(period)

    # Get actual number of days in the period
    period_days = get_period_days(period)

    if start_date is None or end_date is None:
        # For "all time" period, count all threads
        stmt = select(func.count(Thread.id).filter(Thread.is_deleted.is_(False)).label("total"))
        result = await session.execute(stmt)
        total_threads = result.scalar() or 0

        # For all time, there's no meaningful previous period comparison
        previous_total = 0
        avg_per_day = 0.0  # Can't calculate meaningful average for all time
    else:
        # Get previous period range for comparison
        prev_start_date, prev_end_date = get_previous_period_range(period)

        # Count threads in current period
        current_stmt = select(
            func.count(Thread.id).filter(Thread.is_deleted.is_(False), Thread.created_at >= start_date, Thread.created_at < end_date).label("total")
        )
        current_result = await session.execute(current_stmt)
        total_threads = current_result.scalar() or 0

        # Count threads in previous period
        if prev_start_date is not None and prev_end_date is not None:
            previous_stmt = select(
                func.count(Thread.id)
                .filter(Thread.is_deleted.is_(False), Thread.created_at >= prev_start_date, Thread.created_at < prev_end_date)
                .label("previous_total")
            )
            previous_result = await session.execute(previous_stmt)
            previous_total = previous_result.scalar() or 0
        else:
            previous_total = 0

        # Calculate average per day based on actual period days
        avg_per_day = total_threads / period_days if period_days and period_days > 0 else 0.0

    percentage_change = get_percentage_change(total_threads, previous_total)
    return ThreadStatisticsResponse(total=total_threads, avg_per_day=avg_per_day, percentage_change=percentage_change)