from pydantic import Field

from app.schemas.base import BaseResponse


##################################################
########### REQUEST SCHEMAS ######################
##################################################


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class IngestFileResponse(BaseResponse):
    user_id: str = Field(..., examples=["abcdef"])
    thread_id: str = Field(..., examples=["abcdef"])
    is_success: bool = Field(..., examples=[True])
    output: str = Field(..., examples=["Ingested successfully."])
