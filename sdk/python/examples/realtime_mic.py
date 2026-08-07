"""Stream microphone audio to iotype and print the transcript live.

    pip install "iotype[realtime]" sounddevice numpy
    python examples/realtime_mic.py
"""
import queue
import threading

import numpy as np
import sounddevice as sd

from iotype import Iotype
from iotype.realtime import SAMPLE_RATE, float32_to_pcm16

def main() -> None:
    io = Iotype()
    audio_q: "queue.Queue[bytes | None]" = queue.Queue(maxsize=100)

    def on_audio(indata, frames, time_info, status) -> None:
        # Capture callback must stay fast — just enqueue and return.
        audio_q.put(float32_to_pcm16(np.asarray(indata[:, 0], dtype=np.float32)))

    with io.realtime(model="io-fa") as session:
        def pump() -> None:
            while (chunk := audio_q.get()) is not None:
                session.send_audio(chunk)

        threading.Thread(target=pump, daemon=True).start()

        stream = sd.InputStream(
            samplerate=SAMPLE_RATE, channels=1, dtype="float32",
            blocksize=1600,            # 100 ms frames
            callback=on_audio,
        )

        committed = ""
        print("Speak. Ctrl-C to stop.\n")
        with stream:
            try:
                for event in session:
                    if event.get("type") == "partial":
                        print(f"\r{committed}{event.get('text','')}", end="", flush=True)
                    elif event.get("type") == "final":
                        committed += event.get("text", "") + " "
                        print(f"\r{committed}")
            except KeyboardInterrupt:
                audio_q.put(None)

        print("\n\n--- transcript ---")
        print(committed.strip())

if __name__ == "__main__":
    main()
