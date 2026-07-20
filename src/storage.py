"""정규화된 데이터를 변환·저장하고 성능을 측정함."""

import csv
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from time import perf_counter

import pyarrow as pa
import pyarrow.parquet as pq

from src.models import PipelineRecord, ValidatedData


@dataclass(frozen=True, slots=True)
class StorageBenchmark:
    """저장 형식별 평균 성능과 최종 파일 정보를 보관함."""

    format_name: str
    rows: int
    write_ms: float
    read_ms: float
    size_bytes: int
    path: Path


# 검증된 API 데이터를 시간대별 행으로 결합해 저장용 레코드를 만듦.
def build_tabular_records(data: ValidatedData) -> list[PipelineRecord]:
    """날씨 행마다 공통 국가·IP 정보를 결합함."""
    records: list[PipelineRecord] = []

    # 같은 위치의 시간·기온·강수확률을 하나의 예보 행으로 순회함.
    for forecast_time, temperature, probability in zip(
        data.weather.hourly.time,
        data.weather.hourly.temperature_2m,
        data.weather.hourly.precipitation_probability,
        strict=True,
    ):
        records.append(
            PipelineRecord(
                forecast_time=forecast_time,
                temperature_2m=temperature,
                precipitation_probability=probability,
                weather_timezone=data.weather.timezone,
                weather_latitude=data.weather.latitude,
                weather_longitude=data.weather.longitude,
                country_name=data.country.name,
                country_code=data.country.alpha3_code,
                country_capital=data.country.capital,
                country_region=data.country.region,
                source_ip=data.ip_info.ip,
                ip_country=data.ip_info.country,
                ip_region=data.ip_info.region_name,
                ip_city=data.ip_info.city,
                ip_latitude=data.ip_info.latitude,
                ip_longitude=data.ip_info.longitude,
                ip_timezone=data.ip_info.timezone,
            )
        )

    return records


# Pydantic 레코드를 UTF-8 CSV 파일로 저장함.
def write_csv(records: list[PipelineRecord], path: Path) -> None:
    """정규화된 레코드를 UTF-8 CSV 파일로 저장함."""
    if not records:
        raise ValueError("at least one pipeline record is required")

    path.parent.mkdir(parents=True, exist_ok=True)
    field_names = list(PipelineRecord.model_fields)
    # 모델 필드 순서를 CSV 헤더 순서로 그대로 사용함.
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=field_names,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(record.model_dump(mode="json") for record in records)


# CSV 파일을 다시 읽어 행 목록으로 반환함.
def read_csv(path: Path) -> list[dict[str, str]]:
    """UTF-8 CSV 파일의 모든 행을 문자열 사전 목록으로 읽음."""
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


# Pydantic 레코드를 타입이 보존되는 Parquet 파일로 저장함.
def write_parquet(records: list[PipelineRecord], path: Path) -> None:
    """정규화된 레코드를 PyArrow Parquet 파일로 저장함."""
    if not records:
        raise ValueError("at least one pipeline record is required")

    path.parent.mkdir(parents=True, exist_ok=True)
    # Python 타입을 유지한 사전 목록으로 Arrow 테이블을 구성함.
    rows = [record.model_dump(mode="python") for record in records]
    table = pa.Table.from_pylist(rows)
    pq.write_table(table, path)


# Parquet 파일을 다시 읽어 PyArrow 테이블로 반환함.
def read_parquet(path: Path) -> pa.Table:
    """Parquet 파일을 PyArrow 테이블로 읽음."""
    return pq.read_table(path)


# CSV와 Parquet의 읽기·쓰기 평균 시간 및 파일 크기를 측정함.
def benchmark_storage(
    records: list[PipelineRecord],
    output_dir: Path,
    iterations: int = 5,
) -> list[StorageBenchmark]:
    """CSV와 Parquet을 반복 저장·재읽기하여 성능을 비교함."""
    if not records:
        raise ValueError("at least one pipeline record is required")
    if iterations < 1:
        raise ValueError("iterations must be at least 1")

    csv_path = output_dir / "pipeline_data.csv"
    parquet_path = output_dir / "pipeline_data.parquet"
    csv_write_times: list[float] = []
    csv_read_times: list[float] = []
    parquet_write_times: list[float] = []
    parquet_read_times: list[float] = []

    # 같은 원본 데이터로 각 형식의 쓰기와 읽기 시간을 반복 측정함.
    for _ in range(iterations):
        started_at = perf_counter()
        write_csv(records, csv_path)
        csv_write_times.append((perf_counter() - started_at) * 1_000)

        started_at = perf_counter()
        csv_rows = read_csv(csv_path)
        csv_read_times.append((perf_counter() - started_at) * 1_000)

        started_at = perf_counter()
        write_parquet(records, parquet_path)
        parquet_write_times.append((perf_counter() - started_at) * 1_000)

        started_at = perf_counter()
        parquet_table = read_parquet(parquet_path)
        parquet_read_times.append((perf_counter() - started_at) * 1_000)

        # 저장 과정에서 행이 누락되지 않았는지 매 반복마다 확인함.
        if len(csv_rows) != len(records) or parquet_table.num_rows != len(records):
            raise ValueError("stored row count does not match source records")

    # 밀리초 평균과 마지막으로 생성된 파일 크기를 결과로 정리함.
    return [
        StorageBenchmark(
            format_name="CSV",
            rows=len(records),
            write_ms=mean(csv_write_times),
            read_ms=mean(csv_read_times),
            size_bytes=csv_path.stat().st_size,
            path=csv_path,
        ),
        StorageBenchmark(
            format_name="Parquet",
            rows=len(records),
            write_ms=mean(parquet_write_times),
            read_ms=mean(parquet_read_times),
            size_bytes=parquet_path.stat().st_size,
            path=parquet_path,
        ),
    ]
