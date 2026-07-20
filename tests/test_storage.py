"""정규화 레코드 생성과 파일 저장을 테스트함."""

from pathlib import Path

from src.models import PipelineRecord, ValidatedData
from src.storage import (
    benchmark_storage,
    build_tabular_records,
    read_csv,
    read_parquet,
    write_csv,
    write_parquet,
)


# 저장 변환 테스트에 사용할 검증 완료 데이터를 만듦.
def make_validated_data() -> ValidatedData:
    return ValidatedData.model_validate(
        {
            "weather": {
                "latitude": 37.55,
                "longitude": 127.0,
                "timezone": "Asia/Seoul",
                "hourly": {
                    "time": ["2026-07-20T00:00", "2026-07-20T01:00"],
                    "temperature_2m": [23.2, 22.8],
                    "precipitation_probability": [6, 10],
                },
            },
            "country": {
                "name": "Korea (Republic of)",
                "alpha3Code": "KOR",
                "capital": "Seoul",
                "region": "Asia",
                "subregion": "Eastern Asia",
                "latlng": [37, 127.5],
            },
            "ip_info": {
                "status": "success",
                "query": "8.8.8.8",
                "country": "United States",
                "countryCode": "US",
                "regionName": "Virginia",
                "city": "Ashburn",
                "lat": 39.03,
                "lon": -77.5,
                "timezone": "America/New_York",
            },
        }
    )


# 시간대별 날씨 행마다 동일한 국가와 IP 정보가 결합되는지 확인함.
def test_build_tabular_records_combines_sources() -> None:
    records = build_tabular_records(make_validated_data())

    assert len(records) == 2
    assert records[0].temperature_2m == 23.2
    assert records[0].country_code == "KOR"
    assert records[1].source_ip == "8.8.8.8"


# CSV 저장 후 원본과 같은 행 수를 읽을 수 있는지 확인함.
def test_csv_round_trip(tmp_path: Path) -> None:
    records = build_tabular_records(make_validated_data())
    path = tmp_path / "records.csv"

    write_csv(records, path)

    assert path.exists()
    assert len(read_csv(path)) == len(records)


# Parquet 저장 후 원본의 행 수와 열 수가 보존되는지 확인함.
def test_parquet_round_trip(tmp_path: Path) -> None:
    records = build_tabular_records(make_validated_data())
    path = tmp_path / "records.parquet"

    write_parquet(records, path)
    table = read_parquet(path)

    assert path.exists()
    assert table.num_rows == len(records)
    assert table.num_columns == len(PipelineRecord.model_fields)


# 두 저장 형식의 측정 결과와 파일이 모두 생성되는지 확인함.
def test_benchmark_storage_creates_both_formats(tmp_path: Path) -> None:
    records = build_tabular_records(make_validated_data())

    results = benchmark_storage(records, tmp_path, iterations=2)

    assert [result.format_name for result in results] == ["CSV", "Parquet"]
    assert all(result.rows == len(records) for result in results)
    assert all(result.size_bytes > 0 for result in results)
    assert all(result.path.exists() for result in results)
