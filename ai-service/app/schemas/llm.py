from pydantic import Field

from app.schemas.base import BaseRequest, BaseResponse


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class GenerateTitleRequest(BaseRequest):
    content: str = Field(min_length=1, max_length=8000, title="Input", examples=["Hello!"])


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class GenerateTitleResponse(BaseResponse):
    title: str = Field(..., title="Output", examples=["Hello!"])
