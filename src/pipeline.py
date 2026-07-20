"""API 수집과 스키마 검증을 연결하는 파이프라인 로직임."""

import asyncio
from typing import Any, NamedTuple

import httpx

from src.collectors import fetch_country, fetch_ip_info, fetch_weather
from src.models import CountryData, IpData, ValidatedData, WeatherData


class CollectedData(NamedTuple):
    """세 원본 API가 반환한 검증 전 응답을 묶음."""

    weather: dict[str, Any]
    country: dict[str, Any]
    ip_info: dict[str, Any]


# 세 API를 asyncio.gather로 동시에 호출하고 결과를 묶어 반환함.
async def collect_all(timeout_seconds: float = 15.0) -> CollectedData:
    """날씨·국가·IP 데이터를 동시에 수집함."""
    # 모든 요청에 동일한 제한 시간과 HTTP 클라이언트를 사용함.
    timeout = httpx.Timeout(timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        # 세 코루틴을 한 번에 예약해 네트워크 대기 시간을 겹침.
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


# 세 API의 원본 응답을 Pydantic 모델로 변환하여 타입과 범위를 검증함.
def validate_collected_data(collected: CollectedData) -> ValidatedData:
    """수집한 세 API 응답을 Pydantic v2 모델로 검증함."""
    # 각 원본 JSON을 해당 API 전용 모델로 변환한 뒤 통합함.
    return ValidatedData(
        weather=WeatherData.model_validate(collected.weather),
        country=CountryData.model_validate(collected.country),
        ip_info=IpData.model_validate(collected.ip_info),
    )
