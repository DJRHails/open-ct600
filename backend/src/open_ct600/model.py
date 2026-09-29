"""Shared building blocks for the answers a company gives."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

MAX_POUNDS = 99_999_999_999
Pounds = Annotated[int, Field(ge=0, le=MAX_POUNDS)]


class StrictModel(BaseModel):
    """A set of answers: unknown fields are rejected and text is trimmed."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
