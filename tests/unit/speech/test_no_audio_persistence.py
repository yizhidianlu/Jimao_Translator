"""T204: FR-016 — raw audio bytes MUST NOT be written to disk."""

from __future__ import annotations

from pathlib import Path

from jimao_translator.speech.capture import AudioBuffer
from jimao_translator.speech.engines.mock import MockSpeechRecognizer


class TestNoAudioPersistence:
    async def test_mock_recognizer_writes_no_audio_file(self, tmp_path: Path, monkeypatch) -> None:
        """Nothing resembling an audio file appears in tmp_path during recognition."""
        monkeypatch.chdir(tmp_path)
        recognizer = MockSpeechRecognizer()
        audio = b"\x00\x01\x02" * 4096
        await recognizer.recognize(audio)

        leaked = (
            list(tmp_path.rglob("*.wav"))
            + list(tmp_path.rglob("*.mp3"))
            + list(tmp_path.rglob("*.pcm"))
        )
        assert leaked == []

    def test_audio_buffer_clear_releases_bytes(self) -> None:
        buf = AudioBuffer()
        buf.append(b"\x00" * 16_000)
        buf.append(b"\x01" * 16_000)
        assert len(buf.snapshot()) == 32_000
        buf.clear()
        assert buf.snapshot() == b""

    def test_audio_buffer_snapshot_is_copy(self) -> None:
        """snapshot() returns bytes that do not alias the internal buffer."""
        buf = AudioBuffer()
        buf.append(b"hello")
        snap = buf.snapshot()
        buf.clear()
        # Even after clear, the caller still has their copy.
        assert snap == b"hello"
