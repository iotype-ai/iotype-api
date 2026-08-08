"""Response models."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Process:
    """One unit of work running on an uploaded file.

    ``result`` is ``None`` until the process finishes. Treat a non-``None``
    ``result`` as the completion signal — the exact ``status`` strings are not
    published upstream, so branching on them is brittle.
    """

    type: str | None = None
    status: str | None = None
    result: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def done(self) -> bool:
        return self.result is not None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Process:
        return cls(
            type=data.get("type"),
            status=data.get("status"),
            result=data.get("result"),
            raw=data,
        )


@dataclass
class File:
    """An uploaded file and the processes running on it."""

    uuid: str | None = None
    name: str | None = None
    filename: str | None = None
    processes: list[Process] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> File:
        return cls(
            uuid=data.get("uuid"),
            name=data.get("name"),
            filename=data.get("filename"),
            processes=[Process.from_dict(p) for p in (data.get("processes") or [])],
            raw=data,
        )

    def __iter__(self) -> Iterator[Process]:
        return iter(self.processes)

    def result(self, process_type: str | None = None) -> str | None:
        """Return the first finished result, optionally filtered by type.

        Always match by ``type`` rather than by list position — when
        ``should_summarize`` is set there is more than one process and the
        order is not guaranteed.
        """
        for process in self.processes:
            if process_type and process.type != process_type:
                continue
            if process.done:
                return process.result
        return None

    def results(self) -> dict[str, str]:
        """Every finished result, keyed by process type."""
        return {
            p.type or f"process_{i}": p.result
            for i, p in enumerate(self.processes)
            if p.done and p.result is not None
        }

    @property
    def done(self) -> bool:
        """True when every process has produced a result."""
        return bool(self.processes) and all(p.done for p in self.processes)
