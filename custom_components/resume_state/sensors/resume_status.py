"""Resume Status Enum."""

from enum import StrEnum


class ResumeStatus(StrEnum):
    """Status options for the resume state integration."""

    IDLE = "idle"
    STORED = "stored"
    RESUMING = "resuming"
    ERRORED = "errored"
    DISABLED = "disabled"
