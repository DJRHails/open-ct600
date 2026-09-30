"""Reading real filed accounts: 15 iXBRL filings from Companies House's bulk accounts file.

The fixtures are public records from ``Accounts_Bulk_Data-2026-09-26.zip`` (Companies House's
daily bulk file), chosen to cover micro-entity and small layouts, dormant companies, FRC
taxonomy years 2022 to 2026, Inline XBRL 1.0 and 1.1, net liabilities, figures in thousands,
and filers who show lines without tagging them. Every figure was checked against the rendered
document; the ``checked`` notes quote the lines for the ones whose layout exercises a mapping.
"""

from datetime import date
from pathlib import Path

import pytest

from open_ct600.companies_house.filed_accounts import (
    AccountsNotReadableError,
    FiledAccounts,
    net_assets_from_lines,
    read_filed_accounts,
)

FIXTURES = Path(__file__).parent / "fixtures/companies_house/accounts"


def sheet(**lines: int) -> dict[str, int]:
    fields = [
        "fixed_assets",
        "current_assets",
        "called_up_share_capital_not_paid",
        "prepayments_and_accrued_income",
        "creditors_within_one_year",
        "creditors_after_one_year",
        "provisions",
        "accruals_and_deferred_income",
        "called_up_share_capital",
        "net_assets",
    ]
    return {field: lines.get(field, 0) for field in fields}


def pnl(**lines: int | None) -> dict[str, int | None]:
    fields = [
        "turnover",
        "interest_income",
        "cost_of_sales",
        "staff_costs",
        "depreciation",
        "other_expenses",
        "tax",
        "profit_after_tax",
    ]
    return {field: lines.get(field, 0) for field in fields}


NO_ACTIVITY = "No description of principal activity"
FILINGS = {
    # checked: "Turnover 162,336 / Cost of sales (44,981) / Administrative expenses (91,940) /
    # Profit before tax 25,415 / Tax on profit (7,208) / Profit for the financial year 18,207";
    # "Tangible assets 244,762 / Current assets 72,543 / Creditors within one year (36,995) /
    # Called up share capital 2,260 / Shareholders funds 280,310". Depreciation 26,438 is from
    # the notes; administrative expenses less depreciation is other_expenses. FRC 2026.
    "Prod223_4316_02014751_20260331.html": (
        ("2025-04-01", "2026-03-31", "small", False, 0),
        pnl(
            turnover=162336,
            cost_of_sales=44981,
            depreciation=26438,
            other_expenses=65502,
            tax=7208,
            profit_after_tax=18207,
        ),
        sheet(
            fixed_assets=244762,
            current_assets=72543,
            creditors_within_one_year=36995,
            called_up_share_capital=2260,
            net_assets=280310,
        ),
        [
            "S Durbin-Wood",
            "B Fairbrother",
            "K Phillips",
            "A Wallace",
            "D Pickavance",
            "D Stafford",
            "I Wallace",
        ],
    ),
    # checked: micro format with "Turnover 33461.00 / Cost of sales 2815.00 / Administrative
    # expenses 46162.00 / Profit before tax (15516.00)"; "Current assets 46.00 / Net assets
    # 46.00 / Share capital 1.00". FRC 2024.
    "Prod223_4316_11579512_20260919.html": (
        ("2025-09-20", "2026-09-19", "micro", False, 2),
        # Only the profit before tax is shown: without a tax line, tax and profit after tax
        # are unknown.
        pnl(
            turnover=33461,
            cost_of_sales=2815,
            other_expenses=46162,
            tax=None,
            profit_after_tax=None,
        ),
        sheet(current_assets=46, called_up_share_capital=1, net_assets=46),
        ["Georgi Chukovski"],
    ),
    # checked: format 1 with staff costs (1,643,344) and depreciation (54,435) from the notes
    # inside "Administrative expenses (1,994,158)", and "Other interest receivable and similar
    # income 255,560" as other income. FRC 2024; 423 KB.
    "Prod223_4316_03611735_20250731.html": (
        ("2024-08-01", "2025-07-31", "small", False, 50),
        pnl(
            turnover=4523609,
            interest_income=255560,
            cost_of_sales=2779296,
            staff_costs=1643344,
            depreciation=54435,
            other_expenses=296379,
            tax=93,
            profit_after_tax=5622,
        ),
        sheet(
            fixed_assets=231064,
            current_assets=15244960,
            creditors_within_one_year=607914,
            provisions=52445,
            net_assets=14815665,
        ),
        ["Dr A Janbey", "Dr A Rojeab", "Dr T F Frank", "M T Yousif", "J Rose"],
    ),
    # checked: turnover shown but not tagged; cost of sales 4,605, administrative expenses
    # 15,422 and profit before tax 50,540 are, so turnover is 70,567.
    "Prod223_4316_10959369_20250930.html": (
        ("2024-10-01", "2025-09-30", "small", False, 0),
        pnl(
            turnover=70567,
            cost_of_sales=4605,
            other_expenses=15422,
            tax=12666,
            profit_after_tax=37874,
        ),
        sheet(
            current_assets=128525,
            creditors_within_one_year=36031,
            called_up_share_capital=100,
            net_assets=92494,
        ),
        ["Mr M Thompson", "Mrs K Thompson"],
    ),
    # checked: "Provisions for liabilities (96,378)" is shown but not tagged; the tax note
    # alone does not make a profit and loss account ("elected not to include ... the income
    # statement").
    "Prod223_4316_00089315_20251231.html": (
        ("2025-01-01", "2025-12-31", "small", False, 0),
        None,
        sheet(
            fixed_assets=1704216,
            current_assets=2098864,
            creditors_within_one_year=2285566,
            provisions=96378,
            called_up_share_capital=25000,
            net_assets=1421136,
        ),
        [
            "Luanne Fresco (Executive director)",
            "Michael B Rose",
            "Carlos Fresco",
            "Pamela A Rose",
            "Joshua Fresco",
            "Sophie Fresco",
        ],
    ),
    # checked: tagged in thousands (scale 3): "Tangible assets 107 / Current assets 2,299 /
    # Creditors (984) / Provisions for liabilities (23) / Net assets 1,399 / Called up share
    # capital 1". FRC 2026.
    "Prod223_4316_02207885_20251231.html": (
        ("2025-01-01", "2025-12-31", "small", False, 0),
        None,
        sheet(
            fixed_assets=107000,
            current_assets=2299000,
            creditors_within_one_year=984000,
            provisions=23000,
            called_up_share_capital=1000,
            net_assets=1399000,
        ),
        ["Mr M Green", "Mr P W Chadwick", "Mr T E Elliott", "Mr D A Barrett", "Mr M Shaffer"],
    ),
    # checked: net liabilities "Fixed assets 700 / Current Assets 840 / Creditors (5,185) /
    # Total net assets (liabilities) (3,644)"; the filer's own total is £1 off its lines.
    "Prod223_4316_16890562_20260831.html": (
        ("2025-12-04", "2026-08-31", "micro", False, 0),
        None,
        sheet(
            fixed_assets=700,
            current_assets=840,
            creditors_within_one_year=5185,
            net_assets=-3644,
        ),
        [],
    ),
    # checked: FRS 102 section 1A with creditors tagged without maturity:
    # "NET CURRENT ASSETS 70,129 / NET ASSETS 273,195 / Called up share capital 450".
    "Prod223_4316_00162738_20251231.html": (
        ("2025-01-01", "2025-12-31", "small", False, 10),
        None,
        sheet(
            fixed_assets=203066,
            current_assets=1399401,
            creditors_within_one_year=1329272,
            called_up_share_capital=450,
            net_assets=273195,
        ),
        ["J A Sheth", "M D Patel"],
    ),
    # checked: Inline XBRL 1.0, "NET CURRENT ASSETS 9,354,326 / CREDITORS after more than one
    # year (9,372,074) / NET (LIABILITIES) (17,748)". FRC 2023, filleted.
    "Prod223_4316_02210289_20251230.html": (
        ("2024-12-31", "2025-12-30", "small", False, 0),
        None,
        sheet(
            current_assets=11011247,
            creditors_within_one_year=1656921,
            creditors_after_one_year=9372074,
            called_up_share_capital=100,
            net_assets=-17748,
        ),
        ["R M Murray"],
    ),
    # checked: dormant with net liabilities "Creditors (25,417) / Called up share capital
    # 50,000 / Total equity (25,417)". FRC 2026.
    "Prod223_4316_06004507_20251231.html": (
        ("2025-01-01", "2025-12-31", "small", True, None),
        None,
        sheet(creditors_within_one_year=25417, called_up_share_capital=50000, net_assets=-25417),
        ["G.C. Morris"],
    ),
    # checked: nil lines shown as dashes (ixt:zerodash); "Current Assets 192,741 / Creditors
    # (183,129) / Total net assets 9,612". FRC 2023.
    "Prod223_4316_15983441_20250930.html": (
        ("2024-09-27", "2025-09-30", "micro", False, 0),
        None,
        sheet(current_assets=192741, creditors_within_one_year=183129, net_assets=9612),
        ["Adel Saber-Bohlouli"],
    ),
    # checked: Inline XBRL 1.0 micro with fixed assets untagged: "Current assets 1,854 /
    # Creditors (2,547) / Net current liabilities (693) / Net liabilities (543)", so fixed
    # assets are 150. FRC 2024.
    "Prod223_4316_16202563_20260131.html": (
        ("2025-02-01", "2026-01-31", "micro", False, 1),
        None,
        sheet(
            fixed_assets=150,
            current_assets=1854,
            creditors_within_one_year=2547,
            net_assets=-543,
        ),
        ["Mrs S Arar"],
    ),
    # checked: dormant, FRC 2022 taxonomy, only net current assets of 100 tagged.
    "Prod223_4316_16186885_20260331.html": (
        ("2025-01-15", "2026-03-31", "small", True, None),
        None,
        sheet(current_assets=100, net_assets=100),
        ["Richard David HASSELL"],
    ),
    # checked: Inline XBRL 1.0 dormant, current assets only as debtors of 100.
    "Prod223_4316_00551150_20251231.html": (
        ("2025-01-01", "2025-12-31", "small", True, 0),
        None,
        sheet(current_assets=100, called_up_share_capital=100, net_assets=100),
        ["A G Miller"],
    ),
    # checked: Northern Ireland company, short first period: "Net current assets 1,000 /
    # Called up share capital 1,000 / Shareholders funds 1,000".
    "Prod223_4316_NI731272_20251231.html": (
        ("2025-07-10", "2025-12-31", "small", False, 0),
        None,
        sheet(current_assets=1000, called_up_share_capital=1000, net_assets=1000),
        ["Mr P Hannan", "Mr P Clarke"],
    ),
}


def test_every_fixture_is_listed():
    assert sorted(path.name for path in FIXTURES.glob("*.html")) == sorted(FILINGS)


@pytest.mark.parametrize(("name", "expected"), FILINGS.items(), ids=FILINGS.keys())
def test_reads_the_filings_own_period(name, expected):
    (start, end, standard, dormant, employees), profit_and_loss, balance_sheet, directors = expected

    accounts = read_filed_accounts((FIXTURES / name).read_bytes())

    assert accounts.period.start == date.fromisoformat(start)
    assert accounts.period.end == date.fromisoformat(end)
    assert (accounts.standard, accounts.dormant, accounts.average_employees) == (
        standard,
        dormant,
        employees,
    )
    assert accounts.balance_sheet.model_dump() == balance_sheet
    assert (
        accounts.profit_and_loss.model_dump() if accounts.profit_and_loss else None
    ) == profit_and_loss
    assert accounts.directors == directors


@pytest.mark.parametrize(
    "name", [n for n, e in FILINGS.items() if e[1] is not None and e[1]["tax"] is not None]
)
def test_profit_and_loss_reproduces_the_filed_profit(name):
    accounts = read_filed_accounts((FIXTURES / name).read_bytes())
    lines = accounts.profit_and_loss
    assert lines is not None
    assert lines.tax is not None
    assert lines.profit_after_tax is not None

    before_tax = (
        lines.turnover
        + lines.interest_income
        - lines.cost_of_sales
        - lines.staff_costs
        - lines.depreciation
        - lines.other_expenses
    )

    assert before_tax - lines.tax == lines.profit_after_tax


def test_the_filings_comparatives_are_not_read():
    # The prior year of Ashday (1986) Limited: turnover 144,405 and net assets 262,103.
    accounts = read_filed_accounts((FIXTURES / "Prod223_4316_02014751_20260331.html").read_bytes())

    assert accounts.profit_and_loss is not None
    assert accounts.profit_and_loss.turnover != 144405
    assert accounts.balance_sheet.net_assets != 262103


def test_principal_activity_is_the_filers_text():
    accounts = read_filed_accounts((FIXTURES / "Prod223_4316_11579512_20260919.html").read_bytes())
    unstated = read_filed_accounts((FIXTURES / "Prod223_4316_02014751_20260331.html").read_bytes())

    assert accounts.principal_activity == "General commercial trading."
    assert unstated.principal_activity == NO_ACTIVITY


def minimal_filing(facts: str) -> bytes:
    """A tiny Inline XBRL 1.1 document with a 2025 period and the given facts."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
 xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:xbrldi="http://xbrl.org/2006/xbrldi"
 xmlns:core="http://xbrl.frc.org.uk/fr/2025-01-01/core"
 xmlns:ixt="http://www.xbrl.org/inlineXBRL/transformation/2010-04-20"
 xmlns:ixt4="http://www.xbrl.org/inlineXBRL/transformation/2020-02-12"><body>
<ix:header><ix:resources>
<xbrli:context id="d"><xbrli:entity><xbrli:identifier scheme="x">1</xbrli:identifier>
</xbrli:entity><xbrli:period><xbrli:startDate>2025-01-01</xbrli:startDate>
<xbrli:endDate>2025-12-31</xbrli:endDate></xbrli:period></xbrli:context>
<xbrli:context id="e"><xbrli:entity><xbrli:identifier scheme="x">1</xbrli:identifier>
</xbrli:entity><xbrli:period><xbrli:instant>2025-12-31</xbrli:instant></xbrli:period>
</xbrli:context>
</ix:resources></ix:header>
<ix:nonNumeric name="bus:DescriptionPrincipalActivities" contextRef="d">Widgets</ix:nonNumeric>
{facts}</body></html>""".encode()


@pytest.mark.parametrize(
    ("fact", "net_assets"),
    [
        (
            '<ix:nonFraction name="core:NetAssetsLiabilities" contextRef="e" unitRef="u" '
            'format="ixt4:num-comma-decimal" decimals="0">1.234.567,00</ix:nonFraction>',
            1234567,
        ),
        (
            '<ix:nonFraction name="core:NetAssetsLiabilities" contextRef="e" unitRef="u" '
            'format="ixt:numdotdecimal" decimals="0" scale="3" sign="-">1,234</ix:nonFraction>',
            -1234000,
        ),
        (
            '<ix:nonFraction name="core:NetAssetsLiabilities" contextRef="e" unitRef="u" '
            'format="ixt4:fixed-zero" decimals="0">-</ix:nonFraction>',
            0,
        ),
        (
            '<ix:nonFraction name="core:NetAssetsLiabilities" contextRef="e" unitRef="u" '
            'decimals="0">12 345</ix:nonFraction>',
            12345,
        ),
    ],
    ids=["num-comma-decimal", "thousands and sign", "fixed-zero", "plain with space"],
)
def test_number_formats(fact, net_assets):
    assert read_filed_accounts(minimal_filing(fact)).balance_sheet.net_assets == net_assets


def test_unsupported_number_format_makes_the_filing_unreadable():
    fact = (
        '<ix:nonFraction name="core:NetAssetsLiabilities" contextRef="e" unitRef="u" '
        'format="ixt4:num-word-en" decimals="0">twelve</ix:nonFraction>'
    )

    with pytest.raises(AccountsNotReadableError, match="unsupported format 'num-word-en'"):
        read_filed_accounts(minimal_filing(fact))


@pytest.mark.parametrize(
    ("document", "reason"),
    [
        (b"%PDF-1.4 not xhtml", "not valid XHTML"),
        (b"<html xmlns='http://www.w3.org/1999/xhtml'><body/></html>", "no Inline XBRL facts"),
    ],
)
def test_unreadable_documents(document, reason):
    with pytest.raises(AccountsNotReadableError, match=reason):
        read_filed_accounts(document)


SAMPLE = (FIXTURES / "Prod223_4316_02014751_20260331.html").read_bytes()


@pytest.mark.parametrize(
    ("document", "reason"),
    [
        (
            minimal_filing(
                '<ix:nonFraction name="core:NetAssetsLiabilities" contextRef="e" unitRef="u" '
                'decimals="0" scale="0.0">5</ix:nonFraction>'
            ),
            "malformed",
        ),
        (
            minimal_filing(
                '<ix:nonFraction name="core:NetAssetsLiabilities" contextRef="e" unitRef="u" '
                'decimals="0" scale="999999999">5</ix:nonFraction>'
            ),
            "malformed",
        ),
        (
            SAMPLE.replace(b"<xbrli:startDate>2025-", b"<xbrli:startDate>x2025-", 1),
            "malformed",
        ),
        (
            SAMPLE.replace(b"<xbrli:endDate>2026-", b"<xbrli:endDate>2026-13", 1),
            "malformed",
        ),
    ],
    ids=["non-integer scale", "huge scale", "bad context start", "bad context end"],
)
def test_malformed_figures_and_dates_make_the_filing_unreadable(document, reason):
    with pytest.raises(AccountsNotReadableError, match=reason):
        read_filed_accounts(document)


@pytest.mark.parametrize(
    ("start", "readable"),
    [("2024-07-01", True), ("2024-06-30", False), ("2022-01-01", False), ("2026-01-01", False)],
    ids=["18 months", "a day over 18 months", "four years", "ends before it starts"],
)
def test_a_filings_period_must_be_a_period_of_account(start, readable):
    document = minimal_filing(
        '<ix:nonFraction name="core:NetAssetsLiabilities" contextRef="e" unitRef="u" '
        'decimals="0">5</ix:nonFraction>'
    ).replace(b"<xbrli:startDate>2025-01-01", f"<xbrli:startDate>{start}".encode())

    if readable:
        assert read_filed_accounts(document).period.start == date.fromisoformat(start)
    else:
        with pytest.raises(AccountsNotReadableError, match="isn't a period of account"):
            read_filed_accounts(document)


def duration_fact(concept: str, value: int, sign: str = "") -> str:
    signed = ' sign="-"' if sign else ""
    return (
        f'<ix:nonFraction name="core:{concept}" contextRef="d" unitRef="u" decimals="0"'
        f"{signed}>{value}</ix:nonFraction>"
    )


TURNOVER = duration_fact("TurnoverRevenue", 1000)


@pytest.mark.parametrize(
    ("facts", "tax", "profit_after_tax"),
    [
        (
            [
                duration_fact("ProfitLossOnOrdinaryActivitiesBeforeTax", 100),
                duration_fact("TaxTaxCreditOnProfitOrLossOnOrdinaryActivities", 20),
                duration_fact("ProfitLoss", 80),
            ],
            20,
            80,
        ),
        (
            [
                duration_fact("ProfitLossOnOrdinaryActivitiesBeforeTax", 100),
                duration_fact("ProfitLoss", 80),
            ],
            20,
            80,
        ),
        ([duration_fact("ProfitLossOnOrdinaryActivitiesBeforeTax", 100)], None, None),
        ([duration_fact("ProfitLoss", 80)], None, 80),
        (
            [
                duration_fact("ProfitLossOnOrdinaryActivitiesBeforeTax", 100),
                duration_fact("TaxTaxCreditOnProfitOrLossOnOrdinaryActivities", 20, sign="-"),
                duration_fact("ProfitLoss", 80),
            ],
            20,
            80,
        ),
        (
            [
                duration_fact("ProfitLossOnOrdinaryActivitiesBeforeTax", 100),
                duration_fact("TaxTaxCreditOnProfitOrLossOnOrdinaryActivities", 20),
                duration_fact("ProfitLoss", 120),
            ],
            -20,
            120,
        ),
        (
            [
                duration_fact("ProfitLossOnOrdinaryActivitiesBeforeTax", 100),
                duration_fact("TaxTaxCreditOnProfitOrLossOnOrdinaryActivities", 20, sign="-"),
                duration_fact("ProfitLoss", 120),
            ],
            -20,
            120,
        ),
        (
            [
                duration_fact("ProfitLossOnOrdinaryActivitiesBeforeTax", 100),
                duration_fact("TaxTaxCreditOnProfitOrLossOnOrdinaryActivities", 30),
                duration_fact("ProfitLoss", 80),
            ],
            30,
            80,
        ),
    ],
    ids=[
        "tagged",
        "untagged, from before and after tax",
        "untagged, only before tax",
        "untagged, only after tax",
        "charge tagged with a minus sign",
        "credit tagged without a sign",
        "credit tagged with a minus sign",
        "inconsistent either way: as tagged",
    ],
)
def test_tax_is_unknown_when_untagged_and_its_sign_follows_the_profits(
    facts, tax, profit_after_tax
):
    accounts = read_filed_accounts(minimal_filing(TURNOVER + "".join(facts)))

    assert accounts.profit_and_loss is not None
    assert accounts.profit_and_loss.tax == tax
    assert accounts.profit_and_loss.profit_after_tax == profit_after_tax


def test_balance_sheets_add_up_where_the_filer_tagged_consistently():
    consistent = [name for name in FILINGS if name != "Prod223_4316_16890562_20260831.html"]
    for name in consistent:
        accounts: FiledAccounts = read_filed_accounts((FIXTURES / name).read_bytes())
        assert net_assets_from_lines(accounts.balance_sheet) == accounts.balance_sheet.net_assets
