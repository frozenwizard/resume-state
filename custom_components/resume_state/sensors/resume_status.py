"""Resume Status Enum."""

from enum import StrEnum


class ResumeStatus(StrEnum):
    """Status options for the resume state integration."""

    CLEARED = "cleared"
    STORED = "stored"
    RESUMING = "resuming"
    ERRORED = "errored"
