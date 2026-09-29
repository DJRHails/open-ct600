"""Descriptions of the SIC 2007 codes Companies House uses for a company's nature of business.

``data/SIC07_CH_condensed_list_en.csv`` is Companies House's published condensed list
(https://assets.publishing.service.gov.uk/media/5a7f8639e5274a2e87db65e1/SIC07_CH_condensed_list_en.csv,
from https://www.gov.uk/government/publications/standard-industrial-classification-of-economic-activities-sic),
identical to ``specs/companies-house/SIC07_CH_condensed_list_en.csv``.
"""

import csv
from functools import cache
from pathlib import Path

SIC_LIST = Path(__file__).with_name("data") / "SIC07_CH_condensed_list_en.csv"


@cache
def sic_descriptions() -> dict[str, str]:
    """Description by five-digit SIC code."""
    with SIC_LIST.open(encoding="utf-8-sig", newline="") as file:
        return {row["SIC Code"].strip(): row["Description"].strip() for row in csv.DictReader(file)}


def sic_description(code: str) -> str | None:
    """The description of ``code``, or ``None`` if Companies House's list has no such code."""
    return sic_descriptions().get(code.strip())
