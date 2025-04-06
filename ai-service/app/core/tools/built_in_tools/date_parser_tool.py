from datetime import datetime
from typing import Optional

import dateparser
import pytz
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool


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
