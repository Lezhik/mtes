"""Workflow coordinator types."""

from enum import StrEnum


class WorkflowState(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EMERGENCY_STOPPED = "EMERGENCY_STOPPED"
