"""T421: Global error dialog helper.

Map domain exceptions to user-friendly Chinese messages with actionable hints.
"""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget

from ..exceptions import (
    AuthenticationError,
    ContentPolicyViolationError,
    JimaoError,
    LlmUnavailableError,
    NoSpeechDetectedError,
    RecognitionError,
    TranslationError,
    TtsError,
    UnsupportedLanguageError,
)


def format_error(err: Exception) -> tuple[str, str]:
    """Return (title, body) text for a user-friendly error dialog."""
    if isinstance(err, AuthenticationError):
        return (
            "API 认证失败",
            "Anthropic API 密钥无效或缺失。请在“偏好设置”中更新密钥后重试。",
        )
    if isinstance(err, ContentPolicyViolationError):
        return (
            "内容被策略过滤",
            "你的请求被 LLM 内容策略拒绝。请换一种表达或调整内容后再试。",
        )
    if isinstance(err, LlmUnavailableError):
        return (
            "LLM 不可用",
            f"无法连接到 LLM 服务。基础翻译功能仍可使用。\n\n详情: {err}",
        )
    if isinstance(err, NoSpeechDetectedError):
        return ("未识别到语音", "请确认麦克风权限并重试；说话音量可适当加大。")
    if isinstance(err, RecognitionError):
        return ("语音识别失败", f"语音识别出错: {err}")
    if isinstance(err, TtsError):
        return ("语音合成失败", f"TTS 合成出错: {err}")
    if isinstance(err, UnsupportedLanguageError):
        return ("不支持的语言", f"所选语言暂不支持: {err}")
    if isinstance(err, TranslationError):
        return ("翻译失败", f"翻译出错: {err}")
    if isinstance(err, JimaoError):
        return ("出错了", str(err) or err.__class__.__name__)
    return ("意外错误", f"{err.__class__.__name__}: {err}")


def show_error(err: Exception, parent: QWidget | None = None) -> None:
    """Display an error dialog mapped from a domain exception."""
    title, body = format_error(err)
    QMessageBox.warning(parent, title, body)
