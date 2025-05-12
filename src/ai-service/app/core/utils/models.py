from openai import BaseModel
from pydantic import Field


class Action(BaseModel):
    name: str = Field(..., description="Action name", examples=["name"])
    description: str = Field(..., description="Action description", examples=["description"])
