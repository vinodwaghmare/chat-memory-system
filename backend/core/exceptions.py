"""Base exceptions for the memory system. Every module raises from this hierarchy."""

from __future__ import annotations


class MemorySystemError(Exception):
    """Root exception. All project-specific errors inherit from this."""


class MemoryNotFoundError(MemorySystemError):
    def __init__(self, memory_id: str, user_id: str | None = None):
        self.memory_id = memory_id
        self.user_id = user_id
        super().__init__(f"Memory {memory_id} not found")


class MemoryAccessDeniedError(MemorySystemError):
    def __init__(self, memory_id: str, user_id: str):
        self.memory_id = memory_id
        self.user_id = user_id
        super().__init__(f"User {user_id} cannot access memory {memory_id}")


class ExtractionError(MemorySystemError):
    pass


class EvaluationError(MemorySystemError):
    pass


class RetrievalError(MemorySystemError):
    pass


class StorageError(MemorySystemError):
    pass


class WorkflowError(MemorySystemError):
    def __init__(self, workflow_id: str, message: str):
        self.workflow_id = workflow_id
        super().__init__(f"Workflow {workflow_id}: {message}")


class WorkflowTimeoutError(WorkflowError):
    pass


class LLMClientError(MemorySystemError):
    def __init__(self, provider: str, message: str):
        self.provider = provider
        super().__init__(f"LLM [{provider}]: {message}")


class PIIDetectedError(MemorySystemError):
    def __init__(self, detected_types: list[str]):
        self.detected_types = detected_types
        super().__init__(f"PII detected: {', '.join(detected_types)}")


class ConfigurationError(MemorySystemError):
    pass
