from datetime import datetime, timedelta

from sqlalchemy import func, select

from app.api.deps import SessionDep
from app.core.enums import DateRangeEnum, StatisticsEntity
from app.core.utils.date_range import get_period_days
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
    def get_correct_period_range(period: DateRangeEnum, reference_date: datetime = datetime.now()) -> tuple[datetime | None, datetime | None]:
        """
        Get the correct current period range without the broken logic.
        """
        if reference_date is None:
            reference_date = datetime.utcnow()

        if period == DateRangeEnum.ALL_TIME:
            return None, None
        elif period == DateRangeEnum.DAY:
            day_start = datetime(reference_date.year, reference_date.month, reference_date.day)
            return day_start, day_start + timedelta(days=1)
        elif period == DateRangeEnum.YESTERDAY:
            day_start = datetime(reference_date.year, reference_date.month, reference_date.day)
            yesterday = day_start - timedelta(days=1)
            return yesterday, day_start
        elif period == DateRangeEnum.WEEK:
            day_start = datetime(reference_date.year, reference_date.month, reference_date.day)
            week_start = day_start - timedelta(days=reference_date.weekday())
            return week_start, week_start + timedelta(days=7)
        elif period == DateRangeEnum.MONTH:
            # THIS MONTH - from first day of current month to first day of next month
            month_start = datetime(reference_date.year, reference_date.month, 1)
            if reference_date.month == 12:
                month_end = datetime(reference_date.year + 1, 1, 1)
            else:
                month_end = datetime(reference_date.year, reference_date.month + 1, 1)
            return month_start, month_end
        elif period == DateRangeEnum.QUARTER:
            month = reference_date.month
            quarter_start_month = ((month - 1) // 3) * 3 + 1
            quarter_start = datetime(reference_date.year, quarter_start_month, 1)
            if quarter_start_month == 10:
                quarter_end = datetime(reference_date.year + 1, 1, 1)
            else:
                quarter_end = datetime(reference_date.year, quarter_start_month + 3, 1)
            return quarter_start, quarter_end
        elif period == DateRangeEnum.YEAR:
            year_start = datetime(reference_date.year, 1, 1)
            year_end = datetime(reference_date.year + 1, 1, 1)
            return year_start, year_end
        elif period == DateRangeEnum.LAST_7_DAYS:
            day_start = datetime(reference_date.year, reference_date.month, reference_date.day)
            return day_start - timedelta(days=6), day_start + timedelta(days=1)
        elif period == DateRangeEnum.LAST_30_DAYS:
            day_start = datetime(reference_date.year, reference_date.month, reference_date.day)
            return day_start - timedelta(days=29), day_start + timedelta(days=1)
        else:
            return None, None

    @staticmethod
    def get_correct_previous_period_range(
        period: DateRangeEnum, reference_date: datetime = datetime.now()
    ) -> tuple[datetime | None, datetime | None]:
        """
        Get the correct previous period range.
        """
        if reference_date is None:
            reference_date = datetime.utcnow()

        if period == DateRangeEnum.ALL_TIME:
            return None, None
        elif period == DateRangeEnum.MONTH:
            # LAST MONTH
            if reference_date.month == 1:
                prev_month_start = datetime(reference_date.year - 1, 12, 1)
                prev_month_end = datetime(reference_date.year, 1, 1)
            else:
                prev_month_start = datetime(reference_date.year, reference_date.month - 1, 1)
                prev_month_end = datetime(reference_date.year, reference_date.month, 1)
            return prev_month_start, prev_month_end
        # Add other periods as needed...
        else:
            # For other periods, use a simple offset approach
            current_start, current_end = OverviewStatisticsService.get_correct_period_range(period, reference_date)
            if current_start and current_end:
                period_length = current_end - current_start
                return current_start - period_length, current_end - period_length
            return None, None

    @staticmethod
    async def get_statistics_response(entity: StatisticsEntity, session: SessionDep, period: DateRangeEnum) -> OverviewStatisticsResponse:
        # Use our corrected date range functions
        current_reference = datetime.utcnow()
        start_date, end_date = OverviewStatisticsService.get_correct_period_range(period, current_reference)

        # Get actual number of days in the period
        period_days = get_period_days(period, current_reference)

        # Get the appropriate model for the entity
        EntityModel = BaseStatisticsService.get_entity_statistics_model(entity)

        if start_date is None or end_date is None:
            # For "all time" period, count all entities
            stmt = select(func.count(EntityModel.id)).where(EntityModel.is_deleted.is_(False))
            result = await session.execute(stmt)
            total_entities = result.scalar() or 0

            previous_total = 0
            avg_per_day = 0.0
        else:
            # Count entities in current period
            current_stmt = select(func.count(EntityModel.id)).where(
                EntityModel.is_deleted.is_(False), EntityModel.created_at >= start_date, EntityModel.created_at < end_date
            )
            current_result = await session.execute(current_stmt)
            total_entities = current_result.scalar() or 0

            # Get previous period range for comparison
            prev_start_date, prev_end_date = OverviewStatisticsService.get_correct_previous_period_range(period, current_reference)
            # Count entities in previous period
            if prev_start_date is not None and prev_end_date is not None:
                previous_stmt = select(func.count(EntityModel.id)).where(
                    EntityModel.is_deleted.is_(False), EntityModel.created_at >= prev_start_date, EntityModel.created_at < prev_end_date
                )
                previous_result = await session.execute(previous_stmt)
                previous_total = previous_result.scalar() or 0
            else:
                previous_total = 0

        # Calculate average per day based on actual period days
        avg_per_day = total_entities / period_days if period_days and period_days > 0 else 0.0

        percentage_change = OverviewStatisticsService.get_percentage_change(total_entities, previous_total)
        return OverviewStatisticsResponse(total=total_entities, avg_per_day=avg_per_day, percentage_change=percentage_change)