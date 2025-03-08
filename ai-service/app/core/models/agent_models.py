from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field


class AgentExecutionResult(BaseModel):
    interrupted: Optional[bool] = Field(None, description="Whether the agent was interrupted")
    output: Optional[Union[Dict[str, Any], str]] = Field(None, description="Result data")


class AgentInterruptHandlingResult(BaseModel):
    output: Optional[Union[Dict[str, Any], str]] = Field(None, description="Result data")
