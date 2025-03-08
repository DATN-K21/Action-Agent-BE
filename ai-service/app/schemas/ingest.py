from pydantic import Field

from app.schemas.base import BaseResponse

##################################################
########### REQUEST SCHEMAS ######################
##################################################


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class IngestResponse(BaseResponse):
    user_id: str = Field(..., title="User ID", examples=["abcdef"])
    thread_id: str = Field(..., title="Thread ID", examples=["abcdef"])
    is_success: bool = Field(..., title="Is Success", examples=[True])
    output: str = Field(..., title="Output", examples=["Ingested successfully."])
