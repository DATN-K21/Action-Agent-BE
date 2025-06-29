import json

import aiohttp
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from app.core.tools.utils import aget_credential_value


class WeatherSearchInput(BaseModel):
    """Input for the weather search tool."""

    city: str = Field(
        description="city name,please provide city name in English,for example: Beijing"
    )


async def open_weather_qry(city: str) -> str:
    """
    invoke tools
    """
    appid = await aget_credential_value("Open Weather", "OPEN_WEATHER_API_KEY")

    if not appid:
        return "Error: OpenWeather API Key is not set."

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": appid,
            "units": "metric",
            "lang": "en",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    error_message = {
                        "error": f"failed:{response.status}",
                        "data": await response.text(),
                    }
                    return json.dumps(error_message)

    except Exception as e:
        return json.dumps(f"OpenWeather API request failed. {e}")


openweather = StructuredTool.from_function(
    func=open_weather_qry,
    name="Open Weather",
    description="Useful for when you need to get weather information. Please provide city name in English.",
    args_schema=WeatherSearchInput,
    return_direct=False,
)
