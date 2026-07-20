"""Entry point for the concurrent data collection pipeline."""

import asyncio
from time import perf_counter

import httpx
from pydantic import ValidationError

from src.models import CountryData, IpData, WeatherData
from src.pipeline import collect_all, validate_collected_data


# 날씨 응답에서 이후 검증에 사용할 필드를 요약 출력합니다.
def print_weather_summary(data: WeatherData) -> None:
    """Print the weather fields selected for later validation."""
    hourly = data.hourly
    print("\n[Open-Meteo]")
    print(f"timezone: {data.timezone}")
    print(f"hourly records: {len(hourly.time)}")
    print(f"first time: {hourly.time[0].isoformat()}")
    print(f"first temperature: {hourly.temperature_2m[0]} °C")
    print(
        "first precipitation probability: "
        f"{hourly.precipitation_probability[0]} %"
    )


# 국가 응답에서 이후 검증에 사용할 필드를 요약 출력합니다.
def print_country_summary(data: CountryData) -> None:
    """Print the country fields selected for later validation."""
    print("\n[Countries.dev]")
    print(f"name: {data.name}")
    print(f"country code: {data.alpha3_code}")
    print(f"capital: {data.capital}")
    print(f"region: {data.region} / {data.subregion}")
    print(f"latitude/longitude: {data.latlng}")


# IP 응답에서 이후 검증에 사용할 필드를 요약 출력합니다.
def print_ip_summary(data: IpData) -> None:
    """Print the IP location fields selected for later validation."""
    print("\n[ip-api]")
    print(f"ip: {data.ip}")
    print(f"location: {data.country}, {data.region_name}, {data.city}")
    print(f"latitude/longitude: {data.latitude}, {data.longitude}")
    print(f"timezone: {data.timezone}")


# 세 API를 동시에 수집하고 결과와 소요 시간을 출력합니다.
async def main() -> None:
    """Run the concurrent collection pipeline and display its results."""
    started_at = perf_counter()

    try:
        collected = await collect_all()
        validated = validate_collected_data(collected)
    except httpx.HTTPStatusError as exc:
        print(
            "API returned an error response: "
            f"{exc.request.url} ({exc.response.status_code})"
        )
        return
    except httpx.RequestError as exc:
        print(f"API connection failed: {exc.request.url} ({exc})")
        return
    except ValidationError as exc:
        print(f"API schema validation failed:\n{exc}")
        return
    except ValueError as exc:
        print(f"API data collection failed: {exc}")
        return

    elapsed = perf_counter() - started_at
    print_weather_summary(validated.weather)
    print_country_summary(validated.country)
    print_ip_summary(validated.ip_info)
    print("\nPydantic schema validation passed for all API responses.")
    print(f"\nConcurrent collection completed in {elapsed:.3f} seconds.")


if __name__ == "__main__":
    asyncio.run(main())
