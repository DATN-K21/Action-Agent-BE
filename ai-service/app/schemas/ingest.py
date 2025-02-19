from pydantic import Field

from app.schemas.base import BaseResponse

##################################################
########### REQUEST SCHEMAS ######################
##################################################


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class IngestResponse(BaseResponse):
    threadId: str = Field(..., title="Thread ID", examples=["abcdef"])
    isSuccess: bool = Field(..., title="Is Success", examples=[True])
    output: str = Field(..., title="Output", examples=["Ingested successfully."])
