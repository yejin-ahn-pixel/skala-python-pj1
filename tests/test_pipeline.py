"""파이프라인의 동시 실행 흐름을 테스트함."""

import asyncio
from functools import partial
from typing import Any

import pytest

from src import pipeline
from src.pipeline import CollectedData


# 세 가짜 API 함수가 모두 시작되어야 완료되는 동시 수집 시나리오를 실행함.
async def run_concurrent_collection_test(
    monkeypatch: pytest.MonkeyPatch,
) -> CollectedData:
    started_sources: set[str] = set()
    all_started = asyncio.Event()

    # 호출된 API 이름을 기록하고 세 함수가 모두 시작될 때까지 기다림.
    async def fake_fetch(
        source_name: str,
        response_data: dict[str, Any],
        _client: object,
    ) -> dict[str, Any]:
        started_sources.add(source_name)
        if len(started_sources) == 3:
            all_started.set()

        await asyncio.wait_for(all_started.wait(), timeout=1.0)
        return response_data

    monkeypatch.setattr(
        pipeline,
        "fetch_weather",
        partial(fake_fetch, "weather", {"source": "weather"}),
    )
    monkeypatch.setattr(
        pipeline,
        "fetch_country",
        partial(fake_fetch, "country", {"source": "country"}),
    )
    monkeypatch.setattr(
        pipeline,
        "fetch_ip_info",
        partial(fake_fetch, "ip", {"source": "ip"}),
    )

    collected = await pipeline.collect_all()
    assert started_sources == {"weather", "country", "ip"}
    return collected


# collect_all이 세 API 함수를 순차 실행하지 않고 동시에 실행하는지 확인함.
def test_collect_all_starts_every_fetch_concurrently(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    collected = asyncio.run(run_concurrent_collection_test(monkeypatch))

    assert collected.weather == {"source": "weather"}
    assert collected.country == {"source": "country"}
    assert collected.ip_info == {"source": "ip"}
