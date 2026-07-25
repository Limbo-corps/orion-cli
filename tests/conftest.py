import pytest
from orion.core.singleton import SingletonMeta
from pathlib import Path
import sys

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(autouse=True)
def reset_singletons():
    SingletonMeta._instances.clear()
    yield
    SingletonMeta._instances.clear()
