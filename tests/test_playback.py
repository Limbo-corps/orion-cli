# tests/test_playback.py

import sounddevice as sd
import soundfile as sf


def main():
    data, sample_rate = sf.read(
        "data/audio/output.wav"
    )

    print(
        f"Playing audio "
        f"({len(data)} samples @ {sample_rate}Hz)"
    )

    sd.play(
        data,
        sample_rate,
    )

    sd.wait()

    print("Playback complete")


if __name__ == "__main__":
    main()