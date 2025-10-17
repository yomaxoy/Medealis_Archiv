"""
External Services für Infrastructure Layer.

Integration mit externen APIs und Services.
"""

from .claude_client import ClaudeClient
from .ocr_client import OCRClient

__all__ = [
    "ClaudeClient",
    "OCRClient"
]