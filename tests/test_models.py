"""Pydantic API 응답 검증 모델을 테스트함."""

import pytest
from pydantic import ValidationError

from src.models import CountryData, HourlyWeather, IpData


# 올바른 시간대별 날씨 배열이 정상적으로 검증되는지 확인함.
def test_hourly_weather_accepts_valid_values() -> None:
    weather = HourlyWeather.model_validate(
        {
            "time": ["2026-07-20T00:00", "2026-07-20T01:00"],
            "temperature_2m": [23.2, 22.8],
            "precipitation_probability": [6, 10],
        }
    )

    assert len(weather.time) == 2
    assert weather.temperature_2m[0] == 23.2


# 강수확률이 0~100 범위를 벗어나면 검증에 실패하는지 확인함.
def test_hourly_weather_rejects_invalid_probability() -> None:
    with pytest.raises(ValidationError):
        HourlyWeather.model_validate(
            {
                "time": ["2026-07-20T00:00"],
                "temperature_2m": [23.2],
                "precipitation_probability": [101],
            }
        )


# 시간·기온·강수확률 배열 길이가 다르면 검증에 실패하는지 확인함.
def test_hourly_weather_rejects_different_lengths() -> None:
    with pytest.raises(ValidationError):
        HourlyWeather.model_validate(
            {
                "time": ["2026-07-20T00:00", "2026-07-20T01:00"],
                "temperature_2m": [23.2],
                "precipitation_probability": [6, 10],
            }
        )


# 국가 코드와 좌표가 올바른 국가 응답을 검증함.
def test_country_data_accepts_api_aliases() -> None:
    country = CountryData.model_validate(
        {
            "name": "Korea (Republic of)",
            "alpha3Code": "KOR",
            "capital": "Seoul",
            "region": "Asia",
            "subregion": "Eastern Asia",
            "latlng": [37, 127.5],
        }
    )

    assert country.alpha3_code == "KOR"


# IP 좌표가 허용 범위를 벗어나면 검증에 실패하는지 확인함.
def test_ip_data_rejects_invalid_latitude() -> None:
    with pytest.raises(ValidationError):
        IpData.model_validate(
            {
                "status": "success",
                "query": "8.8.8.8",
                "country": "United States",
                "countryCode": "US",
                "regionName": "Virginia",
                "city": "Ashburn",
                "lat": 91,
                "lon": -77.5,
                "timezone": "America/New_York",
            }
        )
