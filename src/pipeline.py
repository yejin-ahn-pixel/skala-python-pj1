"""Pipeline orchestration logic."""

import asyncio
from typing import Any, NamedTuple

import httpx

from src.collectors import fetch_country, fetch_ip_info, fetch_weather
from src.models import CountryData, IpData, ValidatedData, WeatherData


class CollectedData(NamedTuple):
    """Raw responses returned by the three source APIs."""

    weather: dict[str, Any]
    country: dict[str, Any]
    ip_info: dict[str, Any]


# 세 API를 asyncio.gather로 동시에 호출하고 결과를 묶어 반환합니다.
async def collect_all(timeout_seconds: float = 15.0) -> CollectedData:
    """Collect weather, country, and IP data concurrently."""
    timeout = httpx.Timeout(timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        weather, country, ip_info = await asyncio.gather(
            fetch_weather(client),
            fetch_country(client),
            fetch_ip_info(client),
        )

    return CollectedData(
        weather=weather,
        country=country,
        ip_info=ip_info,
    )


# 세 API의 원본 응답을 Pydantic 모델로 변환하여 타입과 범위를 검증합니다.
def validate_collected_data(collected: CollectedData) -> ValidatedData:
    """Validate all collected API responses with Pydantic v2 models."""
    return ValidatedData(
        weather=WeatherData.model_validate(collected.weather),
        country=CountryData.model_validate(collected.country),
        ip_info=IpData.model_validate(collected.ip_info),
    )
