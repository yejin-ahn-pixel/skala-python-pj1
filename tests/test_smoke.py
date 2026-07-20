"""Initial smoke test for the project scaffold."""

from src import __doc__ as package_doc


# 프로젝트 패키지를 정상적으로 가져올 수 있는지 확인합니다.
def test_package_is_importable() -> None:
    assert package_doc == "Data collection mini pipeline package."
