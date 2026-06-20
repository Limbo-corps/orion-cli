import pytest

from core.singleton import SingletonMeta


@pytest.fixture(autouse=True)
def reset_singletons():
    SingletonMeta._instances.clear()
    yield
    SingletonMeta._instances.clear()
