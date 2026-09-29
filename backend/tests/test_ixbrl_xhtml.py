from datetime import date
from decimal import Decimal

import pytest
from lxml import etree

from open_ct600.ixbrl.taxonomies import CT_COMP_2024, FRC_2026, computations_taxonomy_for
from open_ct600.ixbrl.xhtml import (
    IX,
    XBRLI,
    XHTML,
    Context,
    Duration,
    ExplicitMember,
    InlineDocument,
    InlineXbrlError,
    Instant,
    TypedMember,
    Unit,
    html,
)

END = Instant(date(2026, 3, 31))
YEAR = Duration(date(2025, 4, 1), date(2026, 3, 31))
NS = {"ix": IX, "xbrli": XBRLI, "h": XHTML}


def new_document() -> InlineDocument:
    return InlineDocument(taxonomy=FRC_2026, entity_identifier="12345678", title="Accounts")


def attributes(element: etree._Element) -> dict[str, str]:
    return {str(key): str(value) for key, value in element.attrib.items()}


def parse(document: InlineDocument) -> etree._Element:
    return etree.fromstring(document.serialise().encode("ascii"))


def test_money_is_shown_with_thousands_separators():
    fact = new_document().money("core:TurnoverRevenue", Context("dur", YEAR), 120_000)

    assert fact.text == "120,000"
    assert attributes(fact) == {
        "name": "core:TurnoverRevenue",
        "contextRef": "dur",
        "unitRef": "GBP",
        "decimals": "0",
        "format": "ixt:numdotdecimal",
    }


def test_negative_values_are_shown_unsigned_and_tagged_with_sign():
    fact = new_document().money("core:ProfitLoss", Context("dur", YEAR), -5_000)

    assert fact.text == "5,000"
    assert fact.get("sign") == "-"


def test_positive_values_carry_no_sign():
    fact = new_document().money("core:ProfitLoss", Context("dur", YEAR), 5_000)

    assert fact.get("sign") is None


def test_zero_is_shown_as_a_dash():
    fact = new_document().money("core:FixedAssets", Context("end", END), 0)

    assert fact.text == "-"
    assert fact.get("format") == "ixt:zerodash"


def test_pence_are_shown_to_two_places():
    fact = new_document().money(
        "core:TaxTaxCreditOnProfitOrLossOnOrdinaryActivities",
        Context("dur", YEAR),
        Decimal("5415.5"),
        decimals=2,
    )

    assert fact.text == "5,415.50"
    assert fact.get("decimals") == "2"


def test_values_more_precise_than_decimals_are_rejected():
    with pytest.raises(InlineXbrlError, match="more decimal places"):
        new_document().money("core:ProfitLoss", Context("dur", YEAR), Decimal("10.5"))


@pytest.mark.parametrize(
    ("fraction", "shown", "decimals"),
    [(Decimal("0.19"), "19", "2"), (Decimal("0.3375"), "33.75", "4"), (Decimal("0.1"), "10", "2")],
)
def test_percentages_are_scaled(fraction, shown, decimals):
    document = InlineDocument(taxonomy=CT_COMP_2024, entity_identifier="12345678", title="C")

    fact = document.percentage("ct-comp:FY1FirstRateOfTax", Context("dur", YEAR), fraction)

    assert fact.text == shown
    assert fact.get("scale") == "-2"
    assert fact.get("decimals") == decimals
    assert fact.get("unitRef") == "pure"


def test_dates_use_the_day_month_year_transformation():
    fact = new_document().date_fact("bus:BalanceSheetDate", Context("end", END), date(2026, 3, 1))

    assert fact.text == "1 March 2026"
    assert fact.get("format") == "ixt:datedaymonthyearen"


@pytest.mark.parametrize(
    ("value", "format_"), [(True, "ixt:booleantrue"), (False, "ixt:booleanfalse")]
)
def test_booleans(value, format_):
    fact = new_document().boolean("bus:EntityDormantTruefalse", Context("dur", YEAR), value)

    assert fact.get("format") == format_
    assert fact.text == ("Yes" if value else "No")


def test_serialised_document_declares_used_contexts_and_units_only():
    document = new_document()
    director = Context(
        "dur-director1", YEAR, (ExplicitMember("bus:EntityOfficersDimension", "bus:Director1"),)
    )
    document.append(
        html.p(document.money("core:FixedAssets", Context("end", END), 10)),
        html.p(document.non_numeric("bus:NameEntityOfficer", director, "Jane Smith")),
    )
    root = parse(document)

    contexts = root.findall(".//xbrli:context", NS)
    assert [context.get("id") for context in contexts] == ["end", "dur-director1"]
    assert [unit.get("id") for unit in root.findall(".//xbrli:unit", NS)] == ["GBP"]
    identifier = root.find(".//xbrli:identifier", NS)
    assert identifier is not None
    assert identifier.get("scheme") == "http://www.companieshouse.gov.uk/"
    assert identifier.text == "12345678"
    member = root.find(".//xbrli:segment/*", NS)
    assert member is not None
    assert (member.get("dimension"), member.text) == (
        "bus:EntityOfficersDimension",
        "bus:Director1",
    )
    schema_ref = root.find(".//ix:references/*", NS)
    assert schema_ref is not None
    assert schema_ref.get("{http://www.w3.org/1999/xlink}href") == FRC_2026.schema_ref


def test_typed_members_use_the_domain_element():
    document = InlineDocument(taxonomy=CT_COMP_2024, entity_identifier="12345678", title="C")
    trade = Context(
        "trade",
        YEAR,
        (TypedMember("ct-comp:BusinessNameDimension", "ct-comp:BusinessNameDomain", "Widgets"),),
    )
    document.append(html.p(document.money("ct-comp:ProfitLossPerAccounts", trade, 1)))

    domain = parse(document).find(".//xbrli:segment/*/*", NS)

    assert domain is not None
    assert domain.tag == "{http://www.hmrc.gov.uk/schemas/ct/comp/2024-01-01}BusinessNameDomain"
    assert domain.text == "Widgets"


def test_hidden_facts_go_in_ix_hidden_and_empty_hidden_is_omitted():
    document = new_document()
    assert parse(document).find(".//ix:hidden", NS) is None

    document.hide(document.non_numeric("bus:AccountsType", Context("dur", YEAR)))

    hidden = parse(document).find(".//ix:hidden", NS)
    assert hidden is not None
    assert [fact.get("name") for fact in hidden] == ["bus:AccountsType"]


def test_output_is_ascii_with_numeric_character_references_and_escaped_markup():
    document = InlineDocument(taxonomy=FRC_2026, entity_identifier="12345678", title="Café & Co £")
    document.append(html.p("<script>alert(1)</script>"))

    text = document.serialise()

    assert text.isascii()
    assert "&#163;" in text
    assert "&amp; Co" in text
    assert "<script>" not in text
    assert "&lt;script&gt;" in text
    assert text.startswith('<?xml version="1.0" encoding="UTF-8"?>')


def test_head_embeds_the_stylesheet():
    document = InlineDocument(
        taxonomy=FRC_2026, entity_identifier="12345678", title="A", stylesheet="td { color: red; }"
    )

    style = parse(document).find(".//h:head/h:style", NS)

    assert style is not None
    assert style.text == "td { color: red; }"


def test_undeclared_prefixes_are_rejected():
    with pytest.raises(InlineXbrlError, match="does not declare"):
        new_document().money("ct-comp:TaxPayable", Context("dur", YEAR), 1)


def test_unprefixed_names_are_rejected():
    with pytest.raises(InlineXbrlError, match="prefixed name"):
        new_document().money("TurnoverRevenue", Context("dur", YEAR), 1)


def test_one_context_id_cannot_name_two_contexts():
    document = new_document()
    document.money("core:FixedAssets", Context("c", END), 1)

    with pytest.raises(InlineXbrlError, match="two different contexts"):
        document.money("core:TurnoverRevenue", Context("c", YEAR), 1)


def test_inconsistent_duplicate_facts_are_rejected():
    document = new_document()
    document.money("core:FixedAssets", Context("end", END), 100)
    document.money("core:FixedAssets", Context("end", END), Decimal("100.00"), decimals=2)

    with pytest.raises(InlineXbrlError, match="3314"):
        document.money("core:FixedAssets", Context("end", END), 99)


def test_invalid_context_ids_and_reversed_periods_are_rejected():
    with pytest.raises(InlineXbrlError, match="valid XML name"):
        Context("1st", END)
    with pytest.raises(InlineXbrlError, match="before it starts"):
        Duration(date(2026, 3, 31), date(2025, 4, 1))


def test_control_characters_in_text_are_rejected():
    with pytest.raises(ValueError, match="XML compatible"):
        new_document().non_numeric(
            "bus:DescriptionPrincipalActivities", Context("dur", YEAR), "a\x00b"
        )


def test_unit_ids():
    assert [unit.value for unit in Unit] == ["GBP", "pure"]


@pytest.mark.parametrize(
    ("start", "end", "accepted"),
    [
        (date(2025, 4, 1), date(2026, 3, 31), True),
        (date(2024, 1, 1), date(2024, 12, 31), True),
        (date(2025, 4, 2), date(2026, 4, 1), False),
        (date(2015, 3, 31), date(2016, 3, 30), False),
    ],
)
def test_computations_taxonomy_window(start, end, accepted):
    assert (computations_taxonomy_for(start, end) is CT_COMP_2024) is accepted


def test_frc_2026_has_no_end_date():
    assert FRC_2026.accepts(date(2030, 1, 1), date(2030, 12, 31))
