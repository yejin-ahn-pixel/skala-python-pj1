"""수집한 API 데이터를 검증하는 Pydantic v2 모델을 정의함."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Latitude = Annotated[float, Field(ge=-90, le=90)]
Longitude = Annotated[float, Field(ge=-180, le=180)]
PrecipitationProbability = Annotated[int, Field(ge=0, le=100)]


class HourlyWeather(BaseModel):
    """Open-Meteo 응답에 포함된 시간대별 배열을 표현함."""

    time: list[datetime]
    temperature_2m: list[float]
    precipitation_probability: list[PrecipitationProbability]

    # 시간·기온·강수확률 배열의 길이가 모두 같은지 검증함.
    @model_validator(mode="after")
    def validate_equal_lengths(self) -> "HourlyWeather":
        # 세 배열의 길이를 집합으로 만들어 서로 같은지 확인함.
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
    """프로젝트에서 사용하는 Open-Meteo 응답 필드를 검증함."""

    latitude: Latitude
    longitude: Longitude
    timezone: Literal["Asia/Seoul"]
    hourly: HourlyWeather


class CountryData(BaseModel):
    """프로젝트에서 사용하는 Countries.dev 응답 필드를 검증함."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=1)
    alpha3_code: str = Field(alias="alpha3Code", min_length=3, max_length=3)
    capital: str = Field(min_length=1)
    region: str = Field(min_length=1)
    subregion: str = Field(min_length=1)
    latlng: tuple[Latitude, Longitude]


class IpData(BaseModel):
    """프로젝트에서 사용하는 ip-api 응답 필드를 검증함."""

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
    """세 원본 API에서 검증을 마친 응답을 하나로 묶음."""

    weather: WeatherData
    country: CountryData
    ip_info: IpData


class PipelineRecord(BaseModel):
    """CSV 또는 Parquet 저장에 사용할 정규화된 한 행을 표현함."""

    forecast_time: datetime
    temperature_2m: float
    precipitation_probability: PrecipitationProbability
    weather_timezone: str
    weather_latitude: Latitude
    weather_longitude: Longitude
    country_name: str
    country_code: str
    country_capital: str
    country_region: str
    source_ip: str
    ip_country: str
    ip_region: str
    ip_city: str
    ip_latitude: Latitude
    ip_longitude: Longitude
    ip_timezone: str
