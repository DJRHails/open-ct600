"""Shared building blocks for the answers a company gives."""

import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

MAX_POUNDS = 99_999_999_999
Pounds = Annotated[int, Field(ge=0, le=MAX_POUNDS)]

_NOT_XML_TEXT = re.compile(
    r"""(?x)
    [\x00-\x08\x0b\x0c\x0e-\x1f]   # C0 control characters other than tab, line feed, return
    | [\ud800-\udfff]              # unpaired surrogates, which JSON can smuggle in
    | [\ufffe\uffff]               # the two Unicode non-characters XML 1.0 excludes
    """
)


def reject_non_xml_text(value: object) -> None:
    """Refuse text XML cannot carry, anywhere in an answer (lists and page trees included).

    Everything a company answers ends up in HMRC's XML or the iXBRL documents, which cannot
    hold control characters, so they are a validation error here rather than a crash later.

    Raises:
        ValueError: If any text in ``value`` holds such a character.
    """
    if isinstance(value, SecretStr):
        value = value.get_secret_value()
    if isinstance(value, str):
        if _NOT_XML_TEXT.search(value):
            raise ValueError(
                "Remove the invisible control characters, which can come from copying and pasting"
            )
    elif isinstance(value, list | tuple):
        for item in value:
            reject_non_xml_text(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            reject_non_xml_text(key)
            reject_non_xml_text(item)


class XmlTextModel(BaseModel):
    """Answers whose text must be representable in XML (see ``reject_non_xml_text``)."""

    @field_validator("*", mode="after")
    @classmethod
    def _xml_text(cls, value: object) -> object:
        reject_non_xml_text(value)
        return value


class StrictModel(XmlTextModel):
    """A set of answers: unknown fields are rejected and text is trimmed."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
