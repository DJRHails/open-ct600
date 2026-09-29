"""The Arelle harness itself: the research skeletons pass, broken variants fail for the right
reason, and a document made by the builder is valid and carries the intended values."""

from datetime import date
from decimal import Decimal

import pytest
from ixbrl_harness import EXAMPLES, Document, Rules, Validation, validate

from open_ct600.ixbrl.taxonomies import CT_COMP_2024, FRC_2026
from open_ct600.ixbrl.xhtml import (
    Context,
    Duration,
    ExplicitMember,
    InlineDocument,
    Instant,
    TypedMember,
    html,
)

FRC_2025_PACKAGE = "FRC-2025-Taxonomy-v1.0.0_LK4mek8.zip"


def _example(name: str) -> str:
    return (EXAMPLES / name).read_text(encoding="utf-8")


def _mutate(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1, f"mutation target matched {text.count(old)} times: {old!r}"
    return text.replace(old, new)


MICRO = _example("micro-accounts-frc2026.xhtml")
COMPUTATION = _example("computation-ct-comp-2024.xhtml")

SKELETONS = {
    "micro-frc2026": Document(MICRO, FRC_2026.package, Rules.ACCOUNTS),
    "micro-frc2025": Document(
        _example("micro-accounts-frc2025.xhtml"), FRC_2025_PACKAGE, Rules.ACCOUNTS
    ),
    "small-frc2026": Document(
        _example("small-accounts-frs102-1a-frc2026.xhtml"), FRC_2026.package, Rules.ACCOUNTS
    ),
    "computation-ct-comp-2024": Document(COMPUTATION, CT_COMP_2024.package, Rules.COMPUTATIONS),
}

# Each broken variant, and the Arelle code that must report it.
BROKEN = {
    "micro-regime-statement-wording": (
        Document(
            _mutate(MICRO, "in accordance with the micro-entity provisions", "under FRS 105"),
            FRC_2026.package,
            Rules.ACCOUNTS,
        ),
        "Co.Micro",
    ),
    "micro-missing-director-signing": (
        Document(
            _mutate(
                MICRO,
                '<ix:nonNumeric name="core:DirectorSigningFinancialStatements" '
                'contextRef="dur-director1"/>',
                "",
            ),
            FRC_2026.package,
            Rules.ACCOUNTS,
        ),
        "JFCVC.3312",
    ),
    "micro-script-element": (
        Document(
            _mutate(MICRO, "</head>", '<script type="text/javascript">var x = 1;</script></head>'),
            FRC_2026.package,
            Rules.ACCOUNTS,
        ),
        "HMRC.SG.3.3",
    ),
    "computation-missing-tax-reference": (
        Document(
            _mutate(
                COMPUTATION,
                '<ix:nonNumeric name="ct-comp:TaxReference" contextRef="info-end">'
                "1234567890</ix:nonNumeric>",
                "1234567890",
            ),
            CT_COMP_2024.package,
            Rules.COMPUTATIONS,
        ),
        "xbrl.5.2.6.2.4:requiresElementInconsistency",
    ),
    "computation-missing-business-type": (
        Document(
            _mutate(
                COMPUTATION,
                '<xbrldi:explicitMember dimension="ct-comp:BusinessTypeDimension">'
                "ct-comp:Company</xbrldi:explicitMember></xbrli:segment></xbrli:entity>\n"
                "      <xbrli:period><xbrli:startDate>",
                "</xbrli:segment></xbrli:entity>\n      <xbrli:period><xbrli:startDate>",
            ),
            CT_COMP_2024.package,
            Rules.COMPUTATIONS,
        ),
        "xbrldie:PrimaryItemDimensionallyInvalidError",
    ),
}


def _builder_computation() -> str:
    """A small computation made with the builder, using every fact type it offers."""
    start, end = date(2025, 4, 1), date(2026, 3, 31)
    company = ExplicitMember("ct-comp:BusinessTypeDimension", "ct-comp:Company")
    trade = (
        ExplicitMember("ct-comp:BusinessTypeDimension", "ct-comp:Trade"),
        ExplicitMember("ct-comp:TerritoryDimension", "ct-comp:UK"),
        TypedMember("ct-comp:BusinessNameDimension", "ct-comp:BusinessNameDomain", "Widgets"),
    )
    info = Context("info-end", Instant(end), (company,))
    company_duration = Context("company-duration", Duration(start, end), (company,))
    trade_duration = Context("trade-duration", Duration(start, end), trade)
    document = InlineDocument(
        taxonomy=CT_COMP_2024,
        entity_identifier="12345678",
        title="Widgets & Gadgets Ltd: £ computation",
        stylesheet="td { padding: 2px; }",
    )
    document.hide(document.non_numeric("ct-comp:NameOfProductionSoftware", info, "open-ct600"))
    document.append(
        html.h1(document.non_numeric("ct-comp:CompanyName", info, "Widgets & Gadgets Ltd")),
        html.p(document.non_numeric("ct-comp:TaxReference", info, "1234567890")),
        html.p(document.date_fact("ct-comp:PeriodOfAccountStartDate", info, start)),
        html.p(document.date_fact("ct-comp:PeriodOfAccountEndDate", info, end)),
        html.p(document.date_fact("ct-comp:StartOfPeriodCoveredByReturn", info, start)),
        html.p(document.date_fact("ct-comp:EndOfPeriodCoveredByReturn", info, end)),
        html.p(document.boolean("ct-comp:CompanyIsAPartnerInAFirm", company_duration, False)),
        html.p("(", document.money("ct-comp:ProfitLossPerAccounts", trade_duration, -5000), ")"),
        html.p(document.money("ct-comp:AdjustmentsDepreciation", trade_duration, 0)),
        html.p(document.percentage("ct-comp:FY1FirstRateOfTax", company_duration, Decimal("0.19"))),
        html.p(
            document.money(
                "ct-comp:FY1TaxAtFirstRate", company_duration, Decimal("1234.50"), decimals=2
            )
        ),
    )
    return document.serialise()


BUILT = {
    "builder-computation": Document(
        _builder_computation(), CT_COMP_2024.package, Rules.COMPUTATIONS
    )
}


@pytest.fixture(scope="module")
def validations() -> dict[str, Validation]:
    return validate(
        {**SKELETONS, **BUILT, **{name: document for name, (document, _) in BROKEN.items()}}
    )


@pytest.mark.parametrize("name", [*SKELETONS, *BUILT])
def test_valid_documents_pass_with_no_warnings(validations, name):
    assert validations[name].problems == ()
    assert validations[name].facts


@pytest.mark.parametrize("name", BROKEN)
def test_broken_documents_fail_for_the_expected_reason(validations, name):
    _, expected_code = BROKEN[name]
    assert expected_code in validations[name].codes()


def test_builder_values_survive_transformation(validations):
    result = validations["builder-computation"]

    assert result.values("ct-comp:ProfitLossPerAccounts") == {"trade-duration": "-5000"}
    assert result.values("ct-comp:AdjustmentsDepreciation") == {"trade-duration": "0"}
    assert result.values("ct-comp:FY1FirstRateOfTax") == {"company-duration": "0.19"}
    assert result.values("ct-comp:FY1TaxAtFirstRate") == {"company-duration": "1234.50"}
    assert result.values("ct-comp:CompanyIsAPartnerInAFirm") == {"company-duration": "false"}
    assert result.values("ct-comp:PeriodOfAccountStartDate") == {"info-end": "2025-04-01"}
    assert result.values("ct-comp:CompanyName") == {"info-end": "Widgets & Gadgets Ltd"}
