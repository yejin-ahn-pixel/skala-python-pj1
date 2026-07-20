"""프로젝트 기본 구조가 정상인지 확인하는 스모크 테스트임."""

from src import __doc__ as package_doc


# 프로젝트 패키지를 정상적으로 가져올 수 있는지 확인함.
def test_package_is_importable() -> None:
    assert package_doc == "데이터 수집 미니 파이프라인 패키지임."
