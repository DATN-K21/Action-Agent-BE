from pydantic import Field

from app.schemas.base import BaseResponse

##################################################
########### RESPONSE SCHEMAS #####################
##################################################


class UserStatisticsResponse(BaseResponse):
    total: int = Field(..., description="Total number of users")
    avg_per_day: float = Field(..., description="Average number of users per day over the last 30 days")
    percentage_change: str = Field(..., description="Percentage change in user count compared to last month")

class ConnectedExtensionStatisticsResponse(BaseResponse):
    total: int = Field(..., description="Total number of connected extensions")
    avg_per_day: float = Field(..., description="Average number of connected extensions per day over the last 30 days")
    percentage_change: str = Field(..., description="Percentage change in connected extensions count compared to last month")


class ThreadStatisticsResponse(BaseResponse):
    total: int = Field(..., description="Total number of threads created in the current month")
    avg_per_day: float = Field(..., description="Average number of threads created per day over the last 30 days")
    percentage_change: str = Field(..., description="Percentage change in thread count compared to last month")


class BaseStatisticsResponse(BaseResponse):
    users: UserStatisticsResponse = Field(..., description="User statistics")
    connected_extensions: ConnectedExtensionStatisticsResponse = Field(..., description="Connected extensions statistics")
    threads: ThreadStatisticsResponse = Field(..., description="Thread statistics")