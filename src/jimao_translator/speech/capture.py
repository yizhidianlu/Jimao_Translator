"""T212: Push-to-talk audio capture buffer.

Kept deliberately simple: bytes accumulate in memory; clear() drops them.
We never touch the filesystem. Actual microphone streaming is provided
by `sounddevice` and is wired in the Qt layer.
"""

from __future__ import annotations


class AudioBuffer:
    """Accumulate raw PCM/WAV bytes in memory. `clear()` releases them."""

    def __init__(self) -> None:
        self._chunks: list[bytes] = []

    def append(self, chunk: bytes) -> None:
        if chunk:
            self._chunks.append(chunk)

    def snapshot(self) -> bytes:
        """Return a *copy* of the accumulated bytes (so callers can outlive clear())."""
        return b"".join(self._chunks)

    def clear(self) -> None:
        self._chunks.clear()

    def __len__(self) -> int:
        return sum(len(c) for c in self._chunks)
