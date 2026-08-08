"""Stream microphone audio to iotype and print the transcript live.

    pip install "iotype-ai[realtime]" sounddevice numpy
    IOTYPE_TOKEN=... python examples/realtime_mic.py

Note the ordering: the session must be connected *before* the microphone is
opened, because the server decides the sample rate and we open the input stream
at that rate.
"""

import queue
import threading

import numpy as np
import sounddevice as sd

from iotype import Iotype
from iotype.realtime import float32_to_pcm16


def main() -> None:
    io = Iotype()
    audio_q: "queue.Queue[bytes | None]" = queue.Queue(maxsize=100)

    with io.realtime(model="io-fa") as session:
        rate = session.sample_rate           # the server decides this
        frame = session.frame_size           # 20 ms worth of samples
        print(f"Server accepted model {session.negotiated_model} at {rate} Hz\n")

        def on_audio(indata, frames, time_info, status) -> None:
            # The capture callback must stay fast — just enqueue and return.
            audio_q.put(float32_to_pcm16(np.asarray(indata[:, 0], dtype=np.float32)))

        def pump() -> None:
            while (chunk := audio_q.get()) is not None:
                session.send_audio(chunk)
            session.end_of_stream()          # flush the decoder before closing

        threading.Thread(target=pump, daemon=True).start()

        stream = sd.InputStream(
            samplerate=rate,                 # open the device at the negotiated rate
            channels=1,
            dtype="float32",
            blocksize=frame,
            callback=on_audio,
        )

        committed = ""
        print("Speak. Ctrl-C to stop.\n")
        with stream:
            try:
                for event in session:
                    if event["type"] == "partial":
                        print(f"\r{committed}{event['text']}", end="", flush=True)
                    elif event["text"].strip():
                        committed += event["text"].strip() + " "
                        print(f"\r{committed}")
            except KeyboardInterrupt:
                audio_q.put(None)

        print("\n\n--- transcript ---")
        print(committed.strip())


if __name__ == "__main__":
    main()
