from datetime import datetime
from typing import Optional

import dateparser
import pytz
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool


# class DateParserInput(BaseModel):
#     query: str = Field(description="The natural language date string to parse.")
#
#
# class DateParserTool(BaseTool):
#     name: str = "date_parser"  # Added type annotation
#     description: str = "Parses a natural language date string into an absolute timezone-aware datetime object."
#     args_schema: Type[BaseModel] = DateParserInput
#
#     timezone: str = Field(default="Asia/Ho_Chi_Minh", description="Timezone for parsing dates.")
#
#     def _run(self, query: str) -> Optional[datetime]:
#         """Parses the date and returns an absolute timezone-aware datetime object."""
#         parsed_date = dateparser.parse(query, settings={"TIMEZONE": self.timezone, "RETURN_AS_TIMEZONE_AWARE": True})
#         if parsed_date:
#             tz = pytz.timezone(self.timezone)
#             return parsed_date.astimezone(tz)  # Return timezone-aware datetime object
#         return None  # Return None if parsing fails
#
#     async def _arun(self, query: str) -> Optional[datetime]:
#         """Asynchronous version of _run."""
#         return self._run(query)

@tool
def parser_date(
        query: str,
        config: RunnableConfig
) -> Optional[datetime]:
    """Parses a natural language date string into an absolute timezone-aware datetime object.
    Args:
        query (str): The natural language date string to parse.
        config (RunnableConfig): The configuration for the tool.
    Returns:
        Optional[datetime]: The timezone-aware datetime object.
    """
    timezone = config.get("configurable", {}).get("timezone", "Asia/Ho_Chi_Minh")
    parsed_date = dateparser.parse(query, settings={"TIMEZONE": timezone, "RETURN_AS_TIMEZONE_AWARE": True})
    if parsed_date:
        tz = pytz.timezone(timezone)
        return parsed_date.astimezone(tz)
