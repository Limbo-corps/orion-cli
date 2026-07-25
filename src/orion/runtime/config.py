from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class RuntimeConfig:
    socket_path: Path
    database_path: Path

    model: str = "openai/gpt-oss-120b"
    temperature: float = 0.0