from pydantic import Field

from app.schemas.base import BaseResponse

##################################################
########### RESPONSE SCHEMAS #####################
##################################################


class OverviewStatisticsResponse(BaseResponse):
    total: int = Field(..., description="Total numbers of entities")
    avg_per_day: float = Field(..., description="Average number of entities per day over the selected period")
    percentage_change: str = Field(..., description="Percentage change in entity count compared to the previous period")


class BaseOverviewStatisticsResponse(BaseResponse):
    users: OverviewStatisticsResponse = Field(..., description="User statistics")
    connected_extensions: OverviewStatisticsResponse = Field(..., description="Connected extensions statistics")
    threads: OverviewStatisticsResponse = Field(..., description="Thread statistics")
    assistants: OverviewStatisticsResponse = Field(..., description="Assistants statistics")

class RankingStatisticsResponse(BaseResponse):
    id: str = Field(..., description="Entity ID")
    name: str = Field(..., description="Entity name")
    rank: int = Field(..., description="Rank of the entity based on the statistics")


class BaseRankingStatisticsResponse(BaseResponse):
    users: list[RankingStatisticsResponse] = Field(..., description="User ranking statistics")
    connected_extensions: list[RankingStatisticsResponse] = Field(..., description="Connected extensions ranking statistics")