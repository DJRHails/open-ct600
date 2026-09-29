"""Presentation shared by the iXBRL accounts and computations: styles, tables and wording."""

from datetime import date
from decimal import Decimal
from importlib.metadata import version

from lxml import etree

from open_ct600.ixbrl.xhtml import html, long_date
from open_ct600.tax import twelve_month_period_end

SOFTWARE_NAME = "open-ct600"
SOFTWARE_VERSION = version("open-ct600")

STYLESHEET = """
body { font-family: Arial, sans-serif; color: #0b0c0c; max-width: 760px; margin: 2em auto;
       padding: 0 1em; line-height: 1.4; }
h1 { font-size: 1.8em; margin-bottom: 0.2em; }
h2 { font-size: 1.3em; margin-top: 2em; border-bottom: 2px solid #0b0c0c; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; }
td, th { padding: 4px 8px; vertical-align: top; text-align: left; }
th.n, td.n { text-align: right; width: 9em; white-space: nowrap; }
tr.total td { border-top: 1px solid #0b0c0c; font-weight: bold; }
p.note { color: #505a5f; font-size: 0.9em; }
"""


class IxbrlRenderError(ValueError):
    """Raised when a return cannot be rendered as iXBRL that HMRC would accept."""


def period_noun(start: date, end: date) -> str:
    """The word for the accounting period: "year" if it is twelve months, else "period"."""
    return "year" if end == twelve_month_period_end(start) else "period"


def period_ended(start: date, end: date) -> str:
    """E.g. "year ended 31 March 2026"."""
    return f"{period_noun(start, end)} ended {long_date(end)}"


def amount_cell(fact: etree._Element, *, deduction: bool = False) -> etree._Element:
    """A right-aligned cell for a tagged amount.

    Deductions and genuine negatives are shown in brackets; a nil amount is shown as a dash
    without brackets.
    """
    is_nil = fact.text == "-"
    bracketed = not is_nil and (deduction or fact.get("sign") == "-")
    content = ["(", fact, ")"] if bracketed else [fact]
    return html.td(*content, {"class": "n"})


def amount_row(
    label: str, fact: etree._Element, *, deduction: bool = False, total: bool = False
) -> etree._Element:
    """A table row: a label and a tagged amount."""
    row = html.tr(html.td(label), amount_cell(fact, deduction=deduction))
    if total:
        row.set("class", "total")
    return row


def untagged_row(
    label: str,
    amount: int | Decimal,
    *,
    decimals: int | None = None,
    deduction: bool = False,
    total: bool = False,
) -> etree._Element:
    """A table row for an amount no taxonomy element describes, formatted like tagged ones.

    Args:
        label: The row's label.
        amount: The amount.
        decimals: Decimal places to show; by default none for whole pounds, else two.
        deduction: Show the amount in brackets.
        total: Style the row as a total.
    """
    value = Decimal(amount)
    places = decimals if decimals is not None else (0 if value == value.to_integral_value() else 2)
    shown = f"{abs(value):,.{places}f}"
    if value == 0:
        shown = "-"
    elif deduction or value < 0:
        shown = f"({shown})"
    row = html.tr(html.td(label), html.td(shown, {"class": "n"}))
    if total:
        row.set("class", "total")
    return row


def text_row(label: str, *content: str | etree._Element) -> etree._Element:
    """A table row: a label and text or tagged facts."""
    return html.tr(html.td(label), html.td(*content))


def table(*rows: etree._Element) -> etree._Element:
    """A table of rows with a heading row for the amount column."""
    heading = html.tr(html.th(""), html.th("\N{POUND SIGN}", {"class": "n"}))
    return html.table(heading, *rows)
