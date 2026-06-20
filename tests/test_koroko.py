from pathlib import Path

import soundfile as sf
from kokoro import KPipeline

output_dir = Path("data/audio")
output_dir.mkdir(
    parents=True,
    exist_ok=True,
)

pipeline = KPipeline(lang_code="a")

generator = pipeline(
    "Hello, I am ORION.",
    voice="af_heart",
)

for _, _, audio in generator:
    sf.write(
        output_dir / "output.wav",
        audio,
        24000,
    )
    break