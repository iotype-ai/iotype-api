"""Realtime ASR over WebSocket.

Requires the optional dependency::

    pip install iotype[realtime]
"""

from __future__ import annotations

import json
import threading
from typing import Any, Callable, Iterator, Literal

from .errors import RealtimeError

DEFAULT_WS_PATH = "/socket/realtime"

#: Recommended audio format. The declared rate must match the bytes you send.
SAMPLE_RATE = 16000
SAMPLE_WIDTH = 2  # PCM linear 16-bit
CHANNELS = 1      # mono


class RealtimeSession:
    """A streaming speech-recognition session.

    Audio must be **PCM linear 16-bit, mono, little-endian**, sent as raw
    binary frames. Do not base64-encode it. 16 kHz is recommended, and the
    rate you declare must match the bytes you actually send.

    Send small frames continuously (20-100 ms each). Large infrequent frames
    increase latency and reduce accuracy.

    Example::

        with io.realtime(model="io-fa") as session:
            threading.Thread(target=feed_microphone, args=(session,)).start()
            for event in session:
                if event["type"] == "final":
                    print(event["text"])

    Or with a callback::

        session.run(
            audio_source(),
            on_partial=lambda t: print(t, end="\\r"),
            on_final=print,
        )
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
        self._ws: Any = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ session

    def connect(self) -> "RealtimeSession":
        try:
            from websocket import create_connection  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RealtimeError(
                "Realtime ASR needs the websocket-client package. "
                "Install it with:  pip install iotype[realtime]"
            ) from exc

        self._ws = create_connection(self.url, timeout=30)

        # The handshake must be the first message on the socket. Sending audio
        # before it will cause the server to close the connection.
        # Note the "config" envelope — the fields are nested, not top-level.
        self._ws.send(json.dumps({
            "config": {
                "model": self.model,
                "type": self.token_type,
                "token": self.token,
            }
        }))
        return self

    def send_audio(self, chunk: bytes) -> None:
        """Send one frame of raw PCM 16-bit mono little-endian audio."""
        if self._ws is None:
            raise RealtimeError("Session is not connected. Call connect() first.")
        try:
            from websocket import ABNF  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RealtimeError("websocket-client is not installed.") from exc

        with self._lock:
            self._ws.send(chunk, opcode=ABNF.OPCODE_BINARY)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Yield ``{"type": "partial"|"final", "text": ...}`` as they arrive.

        ``partial`` events are interim and may be revised — render them, do not
        persist them. ``final`` events are settled — persist those.
        """
        if self._ws is None:
            raise RealtimeError("Session is not connected. Call connect() first.")

        while True:
            try:
                raw = self._ws.recv()
            except Exception:  # connection closed by either side
                return
            if not raw:
                return
            if isinstance(raw, bytes):
                continue  # server sends JSON text; ignore stray binary
            try:
                yield json.loads(raw)
            except json.JSONDecodeError:
                continue

    def run(
        self,
        audio: Iterator[bytes],
        *,
        on_partial: Callable[[str], None] | None = None,
        on_final: Callable[[str], None] | None = None,
    ) -> str:
        """Stream ``audio`` and dispatch results to callbacks.

        Returns the concatenated final transcript. The audio pump runs on a
        worker thread so a slow network cannot block your capture loop.
        """
        if self._ws is None:
            self.connect()

        finals: list[str] = []

        def pump() -> None:
            try:
                for chunk in audio:
                    self.send_audio(chunk)
            finally:
                self.close_send()

        worker = threading.Thread(target=pump, daemon=True)
        worker.start()

        for event in self:
            kind, text = event.get("type"), event.get("text", "")
            if kind == "partial" and on_partial:
                on_partial(text)
            elif kind == "final":
                finals.append(text)
                if on_final:
                    on_final(text)

        worker.join(timeout=5)
        return " ".join(finals)

    def close_send(self) -> None:
        """Signal that no more audio is coming, without tearing down the socket."""
        # The protocol has no documented end-of-stream message; closing the
        # socket is the only way to end a session.

    def close(self) -> None:
        if self._ws is not None:
            try:
                self._ws.close()
            finally:
                self._ws = None

    def __enter__(self) -> "RealtimeSession":
        return self.connect()

    def __exit__(self, *exc: object) -> None:
        self.close()


def float32_to_pcm16(samples: "Iterator[float] | Any") -> bytes:
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
