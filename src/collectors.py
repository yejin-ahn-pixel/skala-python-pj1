"""Independent API collection functions used by the pipeline."""

from typing import Any

import httpx

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
COUNTRY_URL = "https://countries.dev/alpha/KOR"
IP_URL = "http://ip-api.com/json/8.8.8.8"

WEATHER_PARAMS = {
    "latitude": 37.5665,
    "longitude": 126.9780,
    "hourly": "temperature_2m,precipitation_probability",
    "forecast_days": 3,
    "timezone": "Asia/Seoul",
}


# 서울의 3일 시간대별 날씨 예보를 가져옵니다.
async def fetch_weather(client: httpx.AsyncClient) -> dict[str, Any]:
    """Fetch Seoul's three-day hourly weather forecast."""
    response = await client.get(WEATHER_URL, params=WEATHER_PARAMS)
    response.raise_for_status()
    return response.json()


# 대한민국의 국가 정보를 가져옵니다.
async def fetch_country(client: httpx.AsyncClient) -> dict[str, Any]:
    """Fetch country information for South Korea."""
    response = await client.get(COUNTRY_URL)
    response.raise_for_status()
    return response.json()


# 8.8.8.8의 IP 기반 지역 정보를 가져옵니다.
async def fetch_ip_info(client: httpx.AsyncClient) -> dict[str, Any]:
    """Fetch location information for the public IP address 8.8.8.8."""
    response = await client.get(IP_URL)
    response.raise_for_status()
    data: dict[str, Any] = response.json()
    if data.get("status") != "success":
        message = data.get("message", "unknown ip-api error")
        raise ValueError(f"ip-api request failed: {message}")
    return data
