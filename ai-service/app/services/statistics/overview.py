from sqlalchemy import func, select

from app.api.deps import SessionDep
from app.core.enums import DateRangeEnum, StatisticsEntity
from app.core.utils.date_range import get_period_days, get_period_range, get_previous_period_range
from app.schemas.statistics import OverviewStatisticsResponse
from app.services.statistics.base import BaseStatisticsService


class OverviewStatisticsService(BaseStatisticsService):
    """
    Service class to handle overview statistics operations.
    """

    @staticmethod
    def get_percentage_change(current: int, previous: int) -> str:
        if previous == 0:
            return "1000.0+" if current > 0 else "0.0%"
        else:
            return f"{((current - previous) / previous) * 100:.1f}%"

    @staticmethod
    async def get_statistics_response(entity: StatisticsEntity, session: SessionDep, period: DateRangeEnum) -> OverviewStatisticsResponse:
        # Get current period range
        start_date, end_date = get_period_range(period)
        # Get actual number of days in the period
        period_days = get_period_days(period)

        # Get the appropriate model for the entity
        EntityModel = BaseStatisticsService.get_entity_statistics_model(entity)

        if start_date is None or end_date is None:
            # For "all time" period, count all users
            stmt = select(func.count(EntityModel.id).filter(EntityModel.is_deleted.is_(False)).label("total"))
            result = await session.execute(stmt)
            total_entities = result.scalar() or 0

            # For all time, there's no meaningful previous period comparison
            previous_total = 0
            avg_per_day = 0.0  # Can't calculate meaningful average for all time
        else:
            # Get previous period range for comparison
            prev_start_date, prev_end_date = get_previous_period_range(period)

            # Count users in current period
            current_stmt = select(
                func.count(EntityModel.id)
                .filter(EntityModel.is_deleted.is_(False), EntityModel.created_at >= start_date, EntityModel.created_at < end_date)
                .label("total")
            )
            current_result = await session.execute(current_stmt)
            total_entities = current_result.scalar() or 0

            # Count users in previous period
            if prev_start_date is not None and prev_end_date is not None:
                previous_stmt = select(
                    func.count(EntityModel.id)
                    .filter(EntityModel.is_deleted.is_(False), EntityModel.created_at >= prev_start_date, EntityModel.created_at < prev_end_date)
                    .label("previous_total")
                )
                previous_result = await session.execute(previous_stmt)
                previous_total = previous_result.scalar() or 0
            else:
                previous_total = 0

        # Calculate average per day based on actual period days
        avg_per_day = total_entities / period_days if period_days and period_days > 0 else 0.0

        percentage_change = OverviewStatisticsService.get_percentage_change(total_entities, previous_total)
        return OverviewStatisticsResponse(total=total_entities, avg_per_day=avg_per_day, percentage_change=percentage_change)
