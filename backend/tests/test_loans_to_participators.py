"""CT600A: s455 tax on loans to participators, and its relief (research worked example)."""

from datetime import date
from decimal import Decimal

import pytest
from answers import boxes, compute, page_of, period, problems

from open_ct600.reliefs import loans_to_participators
from open_ct600.reliefs.loans_to_participators import (
    filed_s455_rate,
    nine_months_after,
    s455_rate,
)

CALENDAR_2025 = period("2025-01-01", "2025-12-31", "2026-08-15")
TAX_YEAR_2026 = period("2026-04-06", "2027-03-31", "2027-06-01")


def loans_page(*loans: tuple[str, int], repaid=(), later=()) -> dict:
    page: dict = {
        "BeforeEndPeriod": "no",
        "LoansInformation": {
            "Loan": [{"Name": name, "AmountOfLoan": str(amount)} for name, amount in loans]
        },
    }
    if repaid:
        page["ReliefEarlierThan"] = {"Loan": list(repaid)}
    if later:
        page["LoanLaterReliefNow"] = {"Loan": list(later)}
    return page


def repayment(amount: int, when: str, released: int = 0) -> dict:
    row = {"Name": "J Smith", "Date": when}
    if amount:
        row["AmountRepaid"] = str(amount)
    if released:
        row["AmountReleasedOrWrittenOff"] = str(released)
    return row


def test_research_worked_example():
    # Loans of £40,000 in 2025; £15,000 repaid on 30 June 2026, within nine months.
    page = loans_page(("J Smith", 40_000), repaid=[repayment(15_000, "2026-06-30")])
    page["TotalLoansOutstanding"] = "25000"
    computation = compute(**CALENDAR_2025, supplementary_pages={"A": page})

    completed = page_of(computation, "A")
    # A20 = 40,000 x 33.75% = 13,500.00; A45 = 15,000 x 33.75% = 5,062.50
    assert completed["LoansInformation"]["TotalLoans"] == "40000"
    assert completed["LoansInformation"]["TaxChargeable"] == "13500.00"
    relief = completed["ReliefEarlierThan"]
    assert (relief["TotalAmountRepaid"], relief["TotalLoans"]) == ("15000", "15000")
    assert "TotalAmountReleasedOrWritten" not in relief
    assert relief["ReliefDue"] == "5062.50"
    # A80 = 13,500.00 - 5,062.50 = 8,437.50, carried to box 480
    assert completed["TaxPayable"] == "8437.50"
    result = boxes(computation)
    assert (result["95"], result["480"]) == (1, Decimal("8437.50"))
    assert "485" not in result
    # 510 = 475 + 480
    assert result["510"] == result["475"] + Decimal("8437.50")
    loans = computation.reliefs.loans_to_participators
    assert loans is not None
    assert loans.amendment_due == 0


def test_loans_from_6_april_2026_are_filed_at_33_75_until_hmrc_accepts_35_75(monkeypatch):
    on(monkeypatch, "2027-07-01")
    page = loans_page(("J Smith", 40_000), repaid=[repayment(15_000, "2027-06-30")])
    computation = compute(**TAX_YEAR_2026, supplementary_pages={"A": page})

    completed = page_of(computation, "A")
    assert completed["LoansInformation"]["TaxChargeable"] == "13500.00"
    assert completed["TaxPayable"] == "8437.50"
    loans = computation.reliefs.loans_to_participators
    assert loans is not None
    # At 35.75%: 14,300.00 - 5,362.50 = 8,937.50, so 500.00 more once HMRC takes the rate
    assert loans.statutory_tax_payable == Decimal("8937.50")
    assert loans.amendment_due == Decimal("500.00")


def test_a_period_straddling_a_rate_change_needs_each_loans_date():
    straddling = period("2026-01-01", "2026-12-31", "2027-03-01")
    page = loans_page(("J Smith", 10_000), ("A Jones", 20_000))

    found = problems(**straddling, supplementary_pages={"A": page})

    assert list(found) == [("participator_loan_dates", "loans")]
    assert "one for each of its 2 rows" in found[("participator_loan_dates", "loans")]


def test_loan_dates_decide_each_loans_rate():
    straddling = period("2026-01-01", "2026-12-31", "2027-03-01")
    page = loans_page(("J Smith", 10_000), ("A Jones", 20_000))
    dates = {"loans": ["2026-02-01", "2026-05-01"]}

    computation = compute(
        **straddling, supplementary_pages={"A": page}, participator_loan_dates=dates
    )

    # Filed at 33.75% for both: 30,000 x 33.75% = 10,125.00
    assert page_of(computation, "A")["TaxPayable"] == "10125.00"
    loans = computation.reliefs.loans_to_participators
    assert loans is not None
    # Statutory: 10,000 x 33.75% + 20,000 x 35.75% = 3,375 + 7,150 = 10,525.00
    assert loans.statutory_tax_payable == Decimal("10525.00")


def test_loans_either_side_of_6_april_2022_are_taxed_at_their_own_rates():
    straddling = period("2022-01-01", "2022-12-31", "2023-06-01")
    page = loans_page(("J Smith", 10_000), ("A Jones", 10_000))
    dates = {"loans": ["2022-02-01", "2022-07-01"]}

    computation = compute(
        **straddling, supplementary_pages={"A": page}, participator_loan_dates=dates
    )

    # 10,000 x 32.5% + 10,000 x 33.75% = 3,250 + 3,375 = 6,625.00
    assert page_of(computation, "A")["LoansInformation"]["TaxChargeable"] == "6625.00"


def test_loan_dates_must_be_in_the_period():
    straddling = period("2026-01-01", "2026-12-31", "2027-03-01")
    page = loans_page(("J Smith", 10_000))

    found = problems(
        **straddling,
        supplementary_pages={"A": page},
        participator_loan_dates={"loans": ["2025-12-31"]},
    )

    assert list(found) == [("participator_loan_dates", "loans", 0)]


def on(monkeypatch: pytest.MonkeyPatch, day: str) -> None:
    """File the return on ``day``: the clock the date rules compare against."""
    monkeypatch.setattr(loans_to_participators, "today", lambda: date.fromisoformat(day))


def test_later_relief_ticks_box_485(monkeypatch):
    # Written off 15 January 2027, in the period to 31 December 2027: relief is due from
    # 1 October 2028 (s458(5)), so a return filed then can claim it in part 3.
    on(monkeypatch, "2028-10-01")
    page = loans_page(("J Smith", 40_000), later=[repayment(0, "2027-01-15", released=5_000)])
    computation = compute(**CALENDAR_2025, supplementary_pages={"A": page})

    completed = page_of(computation, "A")["LoanLaterReliefNow"]
    # A70 = 5,000 x 33.75% = 1,687.50
    assert (completed["TotalAmountReleasedOrWritten"], completed["ReliefDue"]) == (
        "5000",
        "1687.50",
    )
    result = boxes(computation)
    assert result["485"] == 1
    assert result["480"] == Decimal("11812.50")


def test_everything_repaid_gives_nil_tax():
    page = loans_page(("J Smith", 6_000), repaid=[repayment(6_000, "2025-06-30")])

    computation = compute(supplementary_pages={"A": page})

    assert page_of(computation, "A")["TaxPayable"] == "0.00"
    assert boxes(computation)["480"] == 0


def test_a_page_with_no_loans_outstanding_has_nil_tax():
    computation = compute(supplementary_pages={"A": {"BeforeEndPeriod": "yes"}})

    assert page_of(computation, "A") == {"BeforeEndPeriod": "yes", "TaxPayable": "0.00"}


@pytest.mark.parametrize(
    ("when", "part"),
    [("2025-03-31", "ReliefEarlierThan"), ("2026-01-01", "ReliefEarlierThan")],
)
def test_part_2_repayments_are_after_the_period_and_within_nine_months(when, part):
    page = loans_page(("J Smith", 6_000), repaid=[repayment(1_000, when)])

    found = problems(supplementary_pages={"A": page})

    assert list(found) == [("supplementary_pages", "A", part, "Loan", 0, "Date")]


def test_part_3_repayments_are_more_than_nine_months_after_the_period():
    page = loans_page(("J Smith", 6_000), later=[repayment(1_000, "2025-12-31")])

    found = problems(supplementary_pages={"A": page})

    assert list(found) == [("supplementary_pages", "A", "LoanLaterReliefNow", "Loan", 0, "Date")]


def test_relief_rows_need_an_amount():
    page = loans_page(("J Smith", 6_000), repaid=[{"Name": "J Smith", "Date": "2025-06-30"}])

    found = problems(supplementary_pages={"A": page})

    location = ("supplementary_pages", "A", "ReliefEarlierThan", "Loan", 0, "AmountRepaid")
    assert found == {location: "Enter the amount repaid, or the amount released or written off"}


def test_relief_needs_the_loans_in_part_1():
    page = {"BeforeEndPeriod": "no", "ReliefEarlierThan": {"Loan": [repayment(1, "2025-06-30")]}}

    found = problems(supplementary_pages={"A": page})

    assert ("supplementary_pages", "A", "LoansInformation", "TotalLoans") in found


def test_rates_by_the_date_the_loan_was_made():
    assert s455_rate(date(2016, 4, 5)) == Decimal("0.25")
    assert s455_rate(date(2016, 4, 6)) == Decimal("0.325")
    assert s455_rate(date(2022, 4, 6)) == Decimal("0.3375")
    assert s455_rate(date(2026, 4, 5)) == Decimal("0.3375")
    assert s455_rate(date(2026, 4, 6)) == Decimal("0.3575")
    assert filed_s455_rate(date(2026, 4, 6)) == Decimal("0.3375")
    assert filed_s455_rate(date(2020, 1, 1)) == Decimal("0.325")


@pytest.mark.parametrize(
    ("period_end", "last_day"),
    [
        (date(2025, 12, 31), date(2026, 9, 30)),
        (date(2025, 6, 30), date(2026, 3, 31)),
        (date(2025, 5, 15), date(2026, 2, 15)),
        (date(2025, 5, 31), date(2026, 2, 28)),
    ],
)
def test_nine_months_after_keeps_month_ends(period_end, last_day):
    assert nine_months_after(period_end) == last_day


def test_later_relief_is_refused_until_it_is_due(monkeypatch):
    # Review M5. CTA 2010 s458(5), CTM61610: relief for a repayment more than nine months
    # after the period end is due nine months and a day after the end of the accounting
    # period of the repayment. Repaid 1 November 2025, in the period to 31 December 2025
    # (periods taken to run for 12 months): due 1 October 2026.
    page = loans_page(("J Smith", 40_000), later=[repayment(40_000, "2025-11-01")])
    calendar_2024 = period("2024-01-01", "2024-12-31", "2025-06-01")

    on(monkeypatch, "2026-09-30")
    found = problems(**calendar_2024, supplementary_pages={"A": page})
    ((location, message),) = found.items()
    assert location == ("supplementary_pages", "A", "LoanLaterReliefNow", "Loan", 0, "Date")
    assert "1 October 2026" in message

    on(monkeypatch, "2026-10-01")
    computation = compute(**calendar_2024, supplementary_pages={"A": page})
    assert boxes(computation)["480"] == 0


def test_repayment_dates_cannot_be_in_the_future(monkeypatch):
    # Rules 9884 and 9431: the date of repayment must not be later than today.
    on(monkeypatch, "2025-05-31")
    page = loans_page(("J Smith", 6_000), repaid=[repayment(1_000, "2025-06-30")])

    found = problems(supplementary_pages={"A": page})

    assert (
        "cannot be in the future"
        in found[("supplementary_pages", "A", "ReliefEarlierThan", "Loan", 0, "Date")]
    )
