from app.api.deps import SessionDep
from app.core.enums import DateRangeEnum, StatisticsEntity
from app.schemas.statistics import RankingStatisticsResponse


class RankingStatisticsService:
    """
    Service for handling ranking statistics.
    """

    @staticmethod
    async def get_ranking_statistics(entity: StatisticsEntity, session: SessionDep, period: DateRangeEnum) -> list[RankingStatisticsResponse]:
        """
        Get ranking statistics for a specific entity and period.
        """

        return [RankingStatisticsResponse(id="example_id", name="Example Name", rank=1)]
