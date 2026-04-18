"""T213: TTS playback helper.

Streams in-memory audio bytes to the system audio device via `QMediaPlayer`.
We collect chunks into a QBuffer — no file is written to disk.
"""

from __future__ import annotations

import logging
from typing import AsyncIterator

logger = logging.getLogger(__name__)


async def play_stream(audio_stream: AsyncIterator[bytes]) -> bytes:
    """Consume an async stream of audio chunks and play them in-memory.

    Returns the concatenated bytes (handy for tests; callers may discard).

    Playback requires PySide6 + a functioning audio output device. On headless
    CI we simply buffer; audible playback is exercised manually and in GUI tests.
    """
    buffer = bytearray()
    async for chunk in audio_stream:
        buffer.extend(chunk)

    try:
        from PySide6.QtCore import QBuffer, QByteArray, QIODevice
        from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
    except ImportError:  # pragma: no cover — multimedia optional at test time
        logger.debug("PySide6 QtMultimedia not available; skipping playback")
        return bytes(buffer)

    qba = QByteArray(bytes(buffer))
    qbuf = QBuffer()
    qbuf.setData(qba)
    qbuf.open(QIODevice.OpenModeFlag.ReadOnly)

    player = QMediaPlayer()
    output = QAudioOutput()
    player.setAudioOutput(output)
    player.setSourceDevice(qbuf)
    player.play()
    # Fire-and-forget: keep references alive via attributes
    player._jimao_buffer = qbuf  # type: ignore[attr-defined]
    player._jimao_output = output  # type: ignore[attr-defined]
    return bytes(buffer)
