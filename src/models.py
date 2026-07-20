"""Pydantic v2 models for validating collected API data."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Latitude = Annotated[float, Field(ge=-90, le=90)]
Longitude = Annotated[float, Field(ge=-180, le=180)]
PrecipitationProbability = Annotated[int, Field(ge=0, le=100)]


class HourlyWeather(BaseModel):
    """Hourly arrays returned inside an Open-Meteo response."""

    time: list[datetime]
    temperature_2m: list[float]
    precipitation_probability: list[PrecipitationProbability]

    # 시간·기온·강수확률 배열의 길이가 모두 같은지 검증합니다.
    @model_validator(mode="after")
    def validate_equal_lengths(self) -> "HourlyWeather":
        lengths = {
            len(self.time),
            len(self.temperature_2m),
            len(self.precipitation_probability),
        }
        if len(lengths) != 1:
            raise ValueError("weather hourly arrays must have equal lengths")
        if not self.time:
            raise ValueError("weather hourly arrays must not be empty")
        return self


class WeatherData(BaseModel):
    """Validated Open-Meteo response fields used by this project."""

    latitude: Latitude
    longitude: Longitude
    timezone: Literal["Asia/Seoul"]
    hourly: HourlyWeather


class CountryData(BaseModel):
    """Validated Countries.dev response fields used by this project."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=1)
    alpha3_code: str = Field(alias="alpha3Code", min_length=3, max_length=3)
    capital: str = Field(min_length=1)
    region: str = Field(min_length=1)
    subregion: str = Field(min_length=1)
    latlng: tuple[Latitude, Longitude]


class IpData(BaseModel):
    """Validated ip-api response fields used by this project."""

    model_config = ConfigDict(populate_by_name=True)

    status: Literal["success"]
    ip: str = Field(alias="query", min_length=1)
    country: str = Field(min_length=1)
    country_code: str = Field(alias="countryCode", min_length=2, max_length=2)
    region_name: str = Field(alias="regionName", min_length=1)
    city: str = Field(min_length=1)
    latitude: Latitude = Field(alias="lat")
    longitude: Longitude = Field(alias="lon")
    timezone: str = Field(min_length=1)


class ValidatedData(BaseModel):
    """Validated responses from every source API."""

    weather: WeatherData
    country: CountryData
    ip_info: IpData
