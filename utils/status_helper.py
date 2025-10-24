"""
Status Helper Utilities for Global Status Output

Provides helper functions for managing and formatting status messages
across the entire application UI.
"""

import datetime
from typing import List


def append_status(message: str, current_messages: List[str], level: str = "INFO") -> List[str]:
    """
    Append a status message with timestamp and icon.

    Args:
        message: Status message text
        current_messages: Current list of status messages
        level: Message level - "INFO", "SUCCESS", "ERROR", "WARNING", "PROGRESS"

    Returns:
        Updated list of messages
    """
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")

    # Icon mapping for different levels
    icons = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARNING": "⚠️",
        "PROGRESS": "⏳",
        "READY": "🟢"
    }
    icon = icons.get(level, "ℹ️")

    formatted_msg = f"[{timestamp}] {icon} {message}"
    return current_messages + [formatted_msg]


def format_status_display(messages: List[str], max_lines: int = 100) -> str:
    """
    Convert message list to display string.

    Args:
        messages: List of formatted status messages
        max_lines: Maximum number of lines to display (keeps most recent)

    Returns:
        Formatted string for display
    """
    if not messages:
        return "🟢 Ready"

    # Keep only last max_lines messages
    recent = messages[-max_lines:] if len(messages) > max_lines else messages
    return "\n".join(recent)


def clear_status() -> List[str]:
    """
    Clear all status messages.

    Returns:
        Empty list
    """
    return []


def get_status_summary(messages: List[str]) -> str:
    """
    Get a summary of the current status.

    Returns the last message or "Ready" if no messages.

    Args:
        messages: List of status messages

    Returns:
        Last status message or default
    """
    if not messages:
        return "🟢 Ready"
    return messages[-1] if messages else "🟢 Ready"
