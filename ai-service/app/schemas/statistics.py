from pydantic import Field

from app.schemas.base import BaseResponse


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class UserStatisticsResponse(BaseResponse):
    total: int = Field(..., description="Total number of users")
    avg_per_day: float = Field(..., description="Average number of users per day over the last 30 days")
    percentage_change: str = Field(..., description="Percentage change in user count compared to last month")
