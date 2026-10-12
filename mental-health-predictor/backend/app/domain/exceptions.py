from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FieldIssue:
    field: str
    message: str


class InvalidInputError(Exception):
    """The request was well-formed JSON but one or more values are not acceptable to the model."""

    def __init__(self, issues: list[FieldIssue]) -> None:
        super().__init__("; ".join(f"{i.field}: {i.message}" for i in issues))
        self.issues = issues
