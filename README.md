# 데이터 수집 미니 파이프라인

Open-Meteo, Countries.dev, ip-api의 데이터를 비동기로 수집하고 Pydantic으로
검증한 뒤 CSV와 Parquet으로 저장·비교하는 실습 프로젝트입니다.

## 환경 설정

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 실행

```bash
python main.py
```

현재 실행 명령은 다음 세 API를 `asyncio.gather()`로 동시에 호출하고, 이후
검증에 사용할 필드와 전체 수집 시간을 요약해서 출력합니다.

- Open-Meteo: 서울의 3일 시간대별 기온 및 강수확률
- Countries.dev: 대한민국 국가 정보
- ip-api: `8.8.8.8`의 IP 기반 지역 정보

수집된 응답은 Pydantic v2 모델로 변환하며, 다음 조건을 검증합니다.

- 날씨 시간·기온·강수확률 배열의 길이 일치
- 강수확률 `0~100`, 위도 `-90~90`, 경도 `-180~180`
- 국가 코드 길이와 ip-api 성공 상태
- 날짜, 숫자, 문자열 필드의 타입

검증이 끝난 데이터는 시간대별 날씨 한 건을 한 행으로 만들고, 국가 및 IP
정보를 각 행에 결합한 17개 필드의 Pydantic 레코드 목록으로 정규화합니다.
이 목록은 다음 단계에서 CSV와 Parquet으로 저장됩니다.

## 저장 및 성능 비교

실행 시 `data/pipeline_data.csv`와 `data/pipeline_data.parquet`을 생성합니다.
각 형식을 5회 저장하고 다시 읽은 평균 시간과 최종 파일 크기를 출력하며,
두 파일의 행 수가 원본 레코드 수와 같은지도 확인합니다.

## 품질 검사

```bash
pytest
ruff check .
```

## 프로젝트 구조

```text
.
├── data/              # 생성된 CSV 및 Parquet 파일
├── reports/           # 제출용 보고서
├── src/
│   ├── collectors.py  # API 수집
│   ├── models.py      # Pydantic 스키마
│   ├── pipeline.py    # 전체 흐름 제어
│   └── storage.py     # 저장 및 성능 측정
├── tests/             # pytest 테스트
├── main.py            # 실행 진입점
└── requirements.txt   # 고정된 의존성 목록
```
