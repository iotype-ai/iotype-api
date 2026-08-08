"""Realtime ASR over WebSocket.

Requires the optional dependency::

    pip install iotype-ai[realtime]

The protocol implemented here is taken from a tested browser client
(``examples/browser-asr/`` in the repository), not from prose.
"""

from __future__ import annotations

import contextlib
import json
import threading
from collections.abc import Iterator
from typing import Any, Callable, Literal

from .errors import RealtimeError

DEFAULT_WS_PATH = "/socket/realtime"

#: Audio format constants. Note that the *sample rate* is negotiated — the
#: server tells you which one to use in its authorization reply.
SAMPLE_WIDTH = 2  # PCM linear 16-bit
CHANNELS = 1      # mono

#: Frame duration used when slicing audio, in seconds. 20 ms is the value the
#: reference client uses.
FRAME_SECONDS = 0.02


class RealtimeSession:
    """A streaming speech-recognition session.

    The protocol has four steps and skipping any of them breaks the session:

    1. Send the handshake, nested inside a ``config`` object.
    2. **Wait for the reply.** It carries :attr:`sample_rate`, the rate you must
       resample audio to. Sending audio before this arrives closes the socket.
    3. Stream PCM 16-bit mono little-endian audio as binary frames, 20 ms each.
    4. Send ``{"eof": 1}`` and wait a few seconds before closing, or the final
       utterance is lost.

    Audio must never be base64-encoded.

    Example::

        with io.realtime(model="io-fa") as session:
            print("server wants", session.sample_rate, "Hz")

            threading.Thread(target=feed_audio, args=(session,), daemon=True).start()

            for event in session:
                if event["type"] == "final":
                    print(event["text"])

    Or with callbacks::

        session.run(audio_source(), on_partial=..., on_final=print)
    """

    def __init__(
        self,
        *,
        token: str,
        token_type: Literal["access_token", "flash_token"] = "access_token",
        model: Literal["io-fa", "io-en", "io-ar"] = "io-fa",
        base_url: str = "https://iotype.com",
    ) -> None:
        self.token = token
        self.token_type = token_type
        self.model = model
        self.url = base_url.replace("https://", "wss://").replace("http://", "ws://") + DEFAULT_WS_PATH

        #: Sample rate the server expects, in Hz. Populated by :meth:`connect`.
        #: **Resample your audio to this value — it is not a fixed constant.**
        self.sample_rate: int | None = None
        #: Model the server selected, echoed back in the authorization reply.
        self.negotiated_model: str | None = None

        self._ws: Any = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ session

    def connect(self, timeout: float = 30.0) -> RealtimeSession:
        """Open the socket, send the handshake, and wait for authorization.

        Returns once the server has accepted the token. :attr:`sample_rate` is
        set before this returns.

        Raises:
            RealtimeError: if the server rejects the token or does not reply.
        """
        try:
            from websocket import create_connection  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RealtimeError(
                "Realtime ASR needs the websocket-client package. "
                'Install it with:  pip install "iotype-ai[realtime]"'
            ) from exc

        self._ws = create_connection(self.url, timeout=timeout)

        # Step 1. The handshake must be the first message, and the three fields
        # live inside a "config" envelope.
        self._ws.send(json.dumps({
            "config": {
                "model": self.model,
                "type": self.token_type,
                "token": self.token,
            }
        }))

        # Step 2. Wait for the reply before any audio is sent.
        raw = self._ws.recv()
        try:
            reply = json.loads(raw)
        except (TypeError, json.JSONDecodeError) as exc:
            self.close()
            raise RealtimeError(f"Unparseable authorization reply: {raw!r}") from exc

        if reply.get("error"):
            self.close()
            raise RealtimeError(f"Authorization rejected: {reply['error']}")

        if reply.get("status") != "authorized":
            self.close()
            raise RealtimeError(f"Unexpected authorization reply: {reply!r}")

        self.sample_rate = reply.get("sample_rate")
        self.negotiated_model = reply.get("model")

        if not self.sample_rate:
            self.close()
            raise RealtimeError(
                "Server did not return a sample_rate. Audio cannot be sent "
                "without knowing the rate to resample to."
            )

        return self

    @property
    def frame_size(self) -> int:
        """Samples per 20 ms frame at the negotiated rate."""
        if not self.sample_rate:
            raise RealtimeError("Not connected — sample_rate is unknown.")
        return round(self.sample_rate * FRAME_SECONDS)

    def send_audio(self, chunk: bytes) -> None:
        """Send one frame of raw PCM 16-bit mono little-endian audio.

        The audio must already be at :attr:`sample_rate`.
        """
        if self._ws is None:
            raise RealtimeError("Session is not connected. Call connect() first.")
        try:
            from websocket import ABNF  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RealtimeError("websocket-client is not installed.") from exc

        with self._lock:
            self._ws.send(chunk, opcode=ABNF.OPCODE_BINARY)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Yield normalised events until the socket closes.

        Each event is ``{"type": "partial" | "final", "text": str}``.

        The wire format uses two different keys rather than a ``type`` field —
        ``{"partial": "..."}`` for interim text and ``{"text": "..."}`` for
        settled text. This iterator normalises both into one shape.

        ``partial`` events may be revised; render them but never persist them.
        ``final`` events are settled; persist those.
        """
        if self._ws is None:
            raise RealtimeError("Session is not connected. Call connect() first.")

        while True:
            try:
                raw = self._ws.recv()
            except Exception:  # any failure here means the socket is gone
                return
            if not raw:
                return
            if isinstance(raw, bytes):
                continue  # server sends JSON text; ignore stray binary
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if isinstance(data.get("partial"), str):
                yield {"type": "partial", "text": data["partial"]}
            if isinstance(data.get("text"), str):
                yield {"type": "final", "text": data["text"]}

    def run(
        self,
        audio: Iterator[bytes],
        *,
        on_partial: Callable[[str], None] | None = None,
        on_final: Callable[[str], None] | None = None,
    ) -> str:
        """Stream ``audio`` and dispatch results to callbacks.

        Returns the concatenated final transcript. The audio pump runs on a
        worker thread so a slow network cannot block your capture loop. Sends
        ``eof`` automatically once the iterator is exhausted.
        """
        if self._ws is None:
            self.connect()

        finals: list[str] = []

        def pump() -> None:
            try:
                for chunk in audio:
                    self.send_audio(chunk)
            finally:
                self.end_of_stream()

        worker = threading.Thread(target=pump, daemon=True)
        worker.start()

        for event in self:
            text = event.get("text", "")
            if event["type"] == "partial":
                if on_partial:
                    on_partial(text)
            elif text.strip():
                finals.append(text.strip())
                if on_final:
                    on_final(text)

        worker.join(timeout=5)
        return " ".join(finals)

    def end_of_stream(self) -> None:
        """Tell the server no more audio is coming and to flush its decoder.

        The last ``final`` result arrives shortly afterwards. Do not close the
        socket immediately — wait a few seconds, or iterate until it closes.
        """
        if self._ws is None:
            return
        # Best effort — the socket may already be closed by the server.
        with self._lock, contextlib.suppress(Exception):
            self._ws.send(json.dumps({"eof": 1}))

    def close(self) -> None:
        if self._ws is not None:
            try:
                self._ws.close()
            finally:
                self._ws = None

    def __enter__(self) -> RealtimeSession:
        return self.connect()

    def __exit__(self, *exc: object) -> None:
        self.close()


def float32_to_pcm16(samples: Iterator[float] | Any) -> bytes:
    """Convert normalised float samples in [-1, 1] to PCM 16-bit little-endian.

    Accepts a numpy array or any iterable of floats.
    """
    try:
        import numpy as np  # type: ignore

        if isinstance(samples, np.ndarray):
            clipped = np.clip(samples, -1.0, 1.0)
            return (clipped * 32767.0).astype("<i2").tobytes()
    except ImportError:
        pass

    import struct

    out = bytearray()
    for sample in samples:
        s = max(-1.0, min(1.0, float(sample)))
        out += struct.pack("<h", int(s * 32767))
    return bytes(out)


def resample_linear(samples: Any, input_rate: int, output_rate: int) -> Any:
    """Resample float samples with linear interpolation.

    A convenience for the common case where your capture device runs at one
    rate and the server asked for another. Requires numpy.

    For production audio quality prefer a proper resampler such as
    ``soxr`` or ``scipy.signal.resample_poly``; linear interpolation is what the
    reference browser client uses and is adequate for speech.
    """
    try:
        import numpy as np  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RealtimeError("resample_linear requires numpy.") from exc

    if input_rate == output_rate:
        return samples

    data = np.asarray(samples, dtype=np.float32)
    if data.size == 0:
        return data

    duration = data.size / input_rate
    target = round(duration * output_rate)
    positions = np.linspace(0, data.size - 1, target, dtype=np.float64)
    return np.interp(positions, np.arange(data.size), data).astype(np.float32)
