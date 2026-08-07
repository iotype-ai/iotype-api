"""Exception hierarchy for the iotype SDK.

Only ``401`` is documented upstream. The other mappings are inferred and may
change; catch :class:`IotypeError` if you want to be safe.
"""

from __future__ import annotations

from typing import Any


class IotypeError(Exception):
    """Base class for every error raised by this SDK."""

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        body: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.body = body

    def __str__(self) -> str:  # pragma: no cover - trivial
        if self.status is not None:
            return f"[{self.status}] {self.message}"
        return self.message


class AuthenticationError(IotypeError):
    """HTTP 401.

    The upstream docs list four causes for this single status: a missing
    ``Authorization`` header, a malformed token, an expired token, **or an
    exhausted token balance**. Mention the balance case when you surface this
    to a user.
    """


class InsufficientTokensError(IotypeError):
    """Token balance exhausted. Status code inferred, not documented."""


class ValidationError(IotypeError):
    """HTTP 422 — a field failed validation. Status code inferred."""


class NotFoundError(IotypeError):
    """HTTP 404 — unknown uuid. Status code inferred."""


class PayloadTooLargeError(IotypeError):
    """HTTP 413 — upload exceeds the size limit. Status code inferred."""


class RateLimitError(IotypeError):
    """HTTP 429 — too many requests. Status code inferred."""


class ServerError(IotypeError):
    """HTTP 5xx — safe to retry with backoff."""


class ProcessingTimeout(IotypeError):
    """An asynchronous job did not finish within the deadline.

    The job is still running server-side. Keep the ``uuid`` and resume
    tracking later rather than re-uploading, which would be billed again.
    """

    def __init__(self, message: str, *, uuid: str | None = None) -> None:
        super().__init__(message)
        self.uuid = uuid


class RealtimeError(IotypeError):
    """The realtime ASR WebSocket session failed."""


_STATUS_MAP: dict[int, type[IotypeError]] = {
    401: AuthenticationError,
    402: InsufficientTokensError,
    404: NotFoundError,
    413: PayloadTooLargeError,
    422: ValidationError,
    429: RateLimitError,
}


def raise_for_status(status: int, body: Any, text: str) -> None:
    """Translate an HTTP status into the matching exception."""
    if 200 <= status < 300:
        return

    message = text[:500]
    if isinstance(body, dict):
        message = body.get("message") or body.get("error") or message

    if status == 401:
        message = (
            f"{message} — the token is missing, malformed, expired, "
            "or its balance is exhausted."
        )

    if status >= 500:
        raise ServerError(message, status=status, body=body)

    raise _STATUS_MAP.get(status, IotypeError)(message, status=status, body=body)
