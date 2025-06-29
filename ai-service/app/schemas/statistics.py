
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
    score: float = Field(..., description="Score of the entity based on the statistics")
    rank: int = Field(..., description="Rank of the entity based on the statistics")
    display_info: dict[str, str] = Field(default_factory=dict, description="Additional display information")

class BaseRankingEntityStatisticsResponse(BaseResponse):
    data: list[RankingStatisticsResponse] = Field(..., description="List of ranking statistics for the entity")
    weights: dict[str, float] = Field(..., description="Weights for the ranking statistics, used for calculating scores")

class BaseRankingStatisticsResponse(BaseResponse):
    users: BaseRankingEntityStatisticsResponse = Field(..., description="User ranking statistics")
    # connected_extensions: BaseRankingEntityStatisticsResponse = Field(..., description="Connected extensions ranking statistics")