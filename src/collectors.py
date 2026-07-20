"""파이프라인에서 사용하는 API별 독립 수집 함수를 제공함."""

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


# 서울의 3일 시간대별 날씨 예보를 가져옴.
async def fetch_weather(client: httpx.AsyncClient) -> dict[str, Any]:
    """서울의 3일 시간대별 날씨 예보를 JSON으로 반환함."""
    # 서울 좌표와 예보 조건을 쿼리 파라미터로 전달함.
    response = await client.get(WEATHER_URL, params=WEATHER_PARAMS)
    # 정상 응답이 아니면 HTTP 예외를 발생시킴.
    response.raise_for_status()
    return response.json()


# 대한민국의 국가 정보를 가져옴.
async def fetch_country(client: httpx.AsyncClient) -> dict[str, Any]:
    """대한민국의 국가 정보를 JSON으로 반환함."""
    response = await client.get(COUNTRY_URL)
    # 국가 API의 상태 코드를 확인한 후 응답 본문을 변환함.
    response.raise_for_status()
    return response.json()


# 8.8.8.8의 IP 기반 지역 정보를 가져옴.
async def fetch_ip_info(client: httpx.AsyncClient) -> dict[str, Any]:
    """공개 IP 주소 8.8.8.8의 지역 정보를 JSON으로 반환함."""
    response = await client.get(IP_URL)
    response.raise_for_status()
    data: dict[str, Any] = response.json()
    # HTTP 성공과 별개로 응답 본문의 API 처리 상태도 확인함.
    if data.get("status") != "success":
        message = data.get("message", "unknown ip-api error")
        raise ValueError(f"ip-api request failed: {message}")
    return data
