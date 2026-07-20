# ============================================================================
# 작성자: 안예진
# 작성목적: 공개 API 데이터를 비동기로 수집·검증하고 저장 성능을 비교하는 실습
# 작성일: 2026-07-20
#
# 변경사항 내역 (날짜, 변경목적, 변경내용 순으로 기입)
# 2026-07-20: 과제 구현, API 수집·Pydantic 검증·CSV/Parquet 비교 기능 작성
# ============================================================================

"""비동기 데이터 수집 파이프라인"""

import asyncio
from pathlib import Path
from time import perf_counter

import httpx
from pydantic import ValidationError

from src.models import CountryData, IpData, PipelineRecord, WeatherData
from src.pipeline import collect_all, validate_collected_data
from src.storage import StorageBenchmark, benchmark_storage, build_tabular_records


# 날씨 응답에서 이후 검증에 사용할 필드를 요약 출력함.
def print_weather_summary(data: WeatherData) -> None:
    """검증된 날씨 데이터의 주요 필드를 요약 출력함."""
    hourly = data.hourly
    print("\n[Open-Meteo]")
    print(f"timezone: {data.timezone}")
    print(f"hourly records: {len(hourly.time)}")
    print(f"first time: {hourly.time[0].isoformat()}")
    print(f"first temperature: {hourly.temperature_2m[0]} °C")
    print(f"first precipitation probability: {hourly.precipitation_probability[0]} %")


# 국가 응답에서 이후 검증에 사용할 필드를 요약 출력함.
def print_country_summary(data: CountryData) -> None:
    """검증된 국가 데이터의 주요 필드를 요약 출력함."""
    print("\n[Countries.dev]")
    print(f"name: {data.name}")
    print(f"country code: {data.alpha3_code}")
    print(f"capital: {data.capital}")
    print(f"region: {data.region} / {data.subregion}")
    print(f"latitude/longitude: {data.latlng}")


# IP 응답에서 이후 검증에 사용할 필드를 요약 출력함.
def print_ip_summary(data: IpData) -> None:
    """검증된 IP 지역 데이터의 주요 필드를 요약 출력함."""
    print("\n[ip-api]")
    print(f"ip: {data.ip}")
    print(f"location: {data.country}, {data.region_name}, {data.city}")
    print(f"latitude/longitude: {data.latitude}, {data.longitude}")
    print(f"timezone: {data.timezone}")


# CSV와 Parquet의 저장 성능 비교 결과를 표 형태로 출력함.
def print_storage_benchmarks(results: list[StorageBenchmark]) -> None:
    """저장 성능 측정 결과를 정렬된 표로 출력함."""
    print("\nStorage performance comparison (5-run average)")
    print(f"{'Format':<10}{'Rows':>8}{'Write(ms)':>14}{'Read(ms)':>12}{'Bytes':>12}")
    for result in results:
        print(
            f"{result.format_name:<10}{result.rows:>8}"
            f"{result.write_ms:>14.3f}{result.read_ms:>12.3f}"
            f"{result.size_bytes:>12}"
        )
        print(f"  saved: {result.path}")


# 세 API를 동시에 수집하고 결과와 소요 시간을 출력함.
async def main() -> None:
    """전체 비동기 수집 파이프라인을 실행하고 결과를 출력함."""
    started_at = perf_counter()

    try:
        # 원본 수집 후 스키마 검증과 저장용 레코드 변환을 차례로 수행함.
        collected = await collect_all()
        validated = validate_collected_data(collected)
        records = build_tabular_records(validated)
        # 동일한 레코드로 CSV와 Parquet의 저장 성능을 비교함.
        benchmarks = benchmark_storage(records, Path("data"), iterations=5)
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
        print(f"Pipeline data processing failed: {exc}")
        return

    # 처리에 성공한 경우에만 검증 결과와 성능 정보를 출력함.
    elapsed = perf_counter() - started_at
    print_weather_summary(validated.weather)
    print_country_summary(validated.country)
    print_ip_summary(validated.ip_info)
    print("\nPydantic schema validation passed for all API responses.")
    print(
        f"Normalized records created: {len(records)} rows x "
        f"{len(PipelineRecord.model_fields)} fields"
    )
    print("Fields:")
    print(", ".join(PipelineRecord.model_fields))
    print("First normalized row:")
    print(records[0].model_dump(mode="json"))
    print_storage_benchmarks(benchmarks)
    print(f"\nFull pipeline completed in {elapsed:.3f} seconds.")


if __name__ == "__main__":
    asyncio.run(main())
