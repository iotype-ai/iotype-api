"""Synchronous HTTP client for the iotype API."""

from __future__ import annotations

import os
import random
import time
from pathlib import Path
from typing import Any, Literal

import requests

from .errors import IotypeError, ProcessingTimeout, raise_for_status
from .models import File

Language = Literal["fa", "en", "ar"]
Tone = Literal["general", "formal"]
Model = Literal["io-fa", "io-en", "io-ar"]

SPEAKERS: tuple[str, ...] = (
    "behrooz", "mehran", "farshid", "sara", "mitra", "siavash",
    "shirin", "kaveh", "amir", "tanaz", "mahsa",
)

DEFAULT_BASE_URL = "https://iotype.com"
DEFAULT_TIMEOUT = 120.0

_RETRY_STATUSES = frozenset({408, 429, 500, 502, 503, 504})


class Iotype:
    """Client for the iotype HTTP API.

    Args:
        token: Your iotype token. Falls back to ``$IOTYPE_TOKEN``.
        base_url: Override the API host. Falls back to ``$IOTYPE_BASE_URL``.
        timeout: Per-request timeout in seconds.
        max_retries: Attempts for transient failures (429, 5xx, network).

    Example::

        io = Iotype()
        io.translate("سلام دنیا", "fa", "en")
    """

    def __init__(
        self,
        token: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 3,
        session: requests.Session | None = None,
    ) -> None:
        self.token = token or os.environ.get("IOTYPE_TOKEN", "")
        if not self.token:
            raise IotypeError(
                "No token. Pass token=... or set the IOTYPE_TOKEN environment "
                "variable. Generate one at "
                "https://iotype.com/api-service/authentication"
            )

        self.base_url = (base_url or os.environ.get("IOTYPE_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._session = session or requests.Session()

    # ---------------------------------------------------------------- internals

    def _headers(self, *, json_body: bool) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
        }
        if json_body:
            headers["Content-Type"] = "application/json"
        # Never set Content-Type for multipart — requests must add the boundary.
        return headers

    def _request(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        headers = self._headers(json_body=json is not None)
        last: Exception | None = None

        for attempt in range(self.max_retries):
            # A file handle is consumed by a failed attempt; rewind before retrying.
            if files and attempt:
                for value in files.values():
                    handle = value[1] if isinstance(value, tuple) else value
                    if hasattr(handle, "seek"):
                        handle.seek(0)

            try:
                response = self._session.post(
                    url,
                    headers=headers,
                    json=json,
                    data=data,
                    files=files,
                    timeout=timeout or self.timeout,
                )
            except requests.RequestException as exc:
                last = exc
                if attempt == self.max_retries - 1:
                    raise IotypeError(f"Request to {path} failed: {exc}") from exc
                self._sleep_backoff(attempt)
                continue

            if response.status_code in _RETRY_STATUSES and attempt < self.max_retries - 1:
                self._sleep_backoff(attempt)
                continue

            try:
                body = response.json()
            except ValueError:
                body = None

            raise_for_status(response.status_code, body, response.text)

            if body is None:
                raise IotypeError(
                    f"{path} returned a non-JSON body: {response.text[:200]}",
                    status=response.status_code,
                )
            return body

        raise IotypeError(f"Request to {path} failed after {self.max_retries} attempts: {last}")

    @staticmethod
    def _sleep_backoff(attempt: int) -> None:
        time.sleep(min(2**attempt, 8) + random.uniform(0, 0.25))

    @staticmethod
    def _open(path: str | Path) -> tuple[str, Any]:
        p = Path(path)
        if not p.is_file():
            raise IotypeError(f"File not found: {p}")
        return (p.name, p.open("rb"))

    # ------------------------------------------------------------- synchronous

    def translate(self, text: str, source_lang: Language, destination_lang: Language) -> str:
        """Translate text between ``fa``, ``en`` and ``ar``. Returns the translation."""
        body = self._request(
            "/io/v1/translate",
            json={
                "source_lang": source_lang,
                "destination_lang": destination_lang,
                "text": text,
            },
            timeout=30,
        )
        return body.get("result", "")

    def synthesize(
        self,
        text: str,
        *,
        speaker: str = "tanaz",
        tone: Tone = "general",
    ) -> str:
        """Generate speech from text. Returns the URL of the resulting MP3.

        The retention period of generated files is not published — download
        the file if you need it long-term.
        """
        if speaker not in SPEAKERS:
            raise IotypeError(f"Unknown speaker {speaker!r}. Valid: {', '.join(SPEAKERS)}")
        body = self._request(
            "/io/v1/synthesis",
            json={"tone": tone, "speaker": speaker, "text": text},
            timeout=60,
        )
        return body.get("url", "")

    def transcribe_instant(self, path: str | Path) -> str:
        """Transcribe a short MP3 synchronously. Returns the transcript.

        For long recordings use :meth:`transcribe`, which is slower but more
        accurate.
        """
        name, handle = self._open(path)
        try:
            body = self._request(
                "/io/v1/transcribe/instant",
                files={"file": (name, handle, "audio/mpeg")},
            )
        finally:
            handle.close()
        return body.get("result", "")

    # ------------------------------------------------------------ asynchronous

    def transcribe(
        self,
        path: str | Path,
        *,
        summarize: bool = False,
        source_lang: Language | None = None,
        wait: bool = False,
        timeout: float = 1800.0,
    ) -> File | str:
        """Transcribe an MP3 with high accuracy. **Asynchronous.**

        Returns a :class:`File` immediately. Pass ``wait=True`` to poll until
        the transcript is ready and receive the text directly.
        """
        data: dict[str, Any] = {"should_summarize": str(bool(summarize)).lower()}
        if source_lang:
            data["source_lang"] = source_lang

        name, handle = self._open(path)
        try:
            body = self._request(
                "/io/v1/transcribe",
                data=data,
                files={"file": (name, handle, "audio/mpeg")},
            )
        finally:
            handle.close()

        file = File.from_dict(body.get("file") or {})
        if not wait:
            return file
        return self.wait_for(file.uuid, process_type="transcribe", timeout=timeout)

    def ocr(
        self,
        path: str | Path,
        *,
        summarize: bool = False,
        wait: bool = False,
        timeout: float = 1800.0,
    ) -> File | str:
        """Extract text from a PDF or JPG. **Asynchronous.**

        Returns a :class:`File` immediately. Pass ``wait=True`` to poll until
        the text is ready and receive it directly.
        """
        name, handle = self._open(path)
        try:
            body = self._request(
                "/io/v1/ocr",
                data={"should_summarize": str(bool(summarize)).lower()},
                files={"file": (name, handle)},
            )
        finally:
            handle.close()

        file = File.from_dict(body.get("file") or {})
        if not wait:
            return file
        return self.wait_for(file.uuid, process_type="ocr", timeout=timeout)

    # -------------------------------------------------------------------- files

    def files(self) -> list[File]:
        """List every file submitted with this token."""
        body = self._request("/io/v1/files", json={}, timeout=30)
        return [File.from_dict(f) for f in (body.get("files") or [])]

    def track(self, uuid: str) -> File:
        """Fetch the current state of one file."""
        body = self._request("/io/v1/file/track", json={"uuid": uuid}, timeout=30)
        return File.from_dict(body.get("file") or {})

    def wait_for(
        self,
        uuid: str | None,
        *,
        process_type: str | None = None,
        timeout: float = 1800.0,
        initial_interval: float = 5.0,
        max_interval: float = 60.0,
    ) -> str:
        """Poll ``uuid`` until a process carries a result, then return it.

        Backoff starts at ``initial_interval`` and doubles to ``max_interval``.
        Completion is detected by ``result != None``, not by ``status`` — the
        status vocabulary is not published upstream.

        Raises:
            ProcessingTimeout: if the deadline passes. The job keeps running
                server-side; keep the uuid and resume later rather than
                re-uploading, which would be billed again.
        """
        if not uuid:
            raise IotypeError("No uuid to track — the upload response had no file.uuid.")

        deadline = time.monotonic() + timeout
        interval = initial_interval

        while True:
            file = self.track(uuid)
            result = file.result(process_type)
            if result is not None:
                return result

            if time.monotonic() >= deadline:
                raise ProcessingTimeout(
                    f"File {uuid} did not finish within {timeout:.0f}s. "
                    "It is still processing — resume with wait_for(uuid) rather "
                    "than re-uploading.",
                    uuid=uuid,
                )

            time.sleep(min(interval, max(0.0, deadline - time.monotonic())))
            interval = min(interval * 2, max_interval)

    # ------------------------------------------------------------------ helpers

    def download(self, url: str, dest: str | Path) -> Path:
        """Download a generated file, e.g. the MP3 returned by :meth:`synthesize`."""
        dest = Path(dest)
        with self._session.get(url, stream=True, timeout=self.timeout) as response:
            response.raise_for_status()
            with dest.open("wb") as fh:
                for chunk in response.iter_content(65536):
                    fh.write(chunk)
        return dest

    def realtime(
        self,
        *,
        model: Model = "io-fa",
        token: str | None = None,
        token_type: Literal["access_token", "flash_token"] = "access_token",
    ):
        """Open a realtime ASR session. See :class:`~iotype.realtime.RealtimeSession`.

        Defaults to ``access_token`` because this SDK runs server-side. Never
        ship an access token to a browser or mobile client — mint a Flash Token
        for those.
        """
        from .realtime import RealtimeSession

        return RealtimeSession(
            token=token or self.token,
            token_type=token_type,
            model=model,
            base_url=self.base_url,
        )

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> Iotype:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
