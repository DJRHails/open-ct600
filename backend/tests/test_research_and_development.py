"""R&D relief and CT600L (research worked examples R1 to R4, and the scheme edges)."""

from decimal import Decimal

import pytest
from answers import PAYE_REFERENCE, RD_FORMS, boxes, compute, page_of, period, problems

CALENDAR_2025 = period("2025-01-01", "2025-12-31", "2026-06-01")
YEAR_TO_MARCH_2024 = period("2023-04-01", "2024-03-31", "2024-06-01")
CALENDAR_2023 = period("2023-01-01", "2023-12-31", "2024-06-01")


def rd(scheme: str, expenditure: int, **answers) -> dict:
    return {**RD_FORMS, "scheme": scheme, "qualifying_expenditure": expenditure, **answers}


def paye(amount: int, section: str = "SME") -> dict:
    if section == "SME":
        return {
            "SME": {
                "PAYENICforWhichTheCompanyIsLiableInThisAccountingPeriod": str(amount),
                "EmployerPAYEreference": PAYE_REFERENCE,
            }
        }
    return {
        "Step3": {
            "PAYENICsForWhichTheCompanyIsLiableInThisAP": str(amount),
            "EmployerPAYEreference": PAYE_REFERENCE,
        }
    }


def test_r1_merged_rdec_for_a_profit_making_company_is_set_against_its_tax():
    computation = compute(
        profit_and_loss={"turnover": 1_000_000},
        research_and_development=rd("rdec", 500_000),
        supplementary_pages={"L": {}},
    )

    result = boxes(computation)
    # RDEC 20% x 500,000 = 100,000 is taxable: 155 = 1,100,000; tax 25% = 275,000
    assert result["155"] == 1_100_000
    assert result["475"] == Decimal("275000.00")
    page = page_of(computation, "L")
    assert page["Step1"] == {
        "RandDExpenditureOnWhichRDECisClaimedInThisAccountingPeriod": "500000.00",
        "RDECclaimForThisAccountingPeriod": "100000.00",
        "TotalRDECforTheAccountingPeriod": "100000.00",
        "CorporationTaxLiability": "275000.00",
        "MaximumAmountAvailableForStep1SetOff": "275000.00",
        "AmountOfRDECusedToDischargeCorporationTaxAtStep1": "100000.00",
    }
    assert "Step2" not in page
    assert page["TotalRandDSetOffAgainstLiabilities"] == {
        "RDECstep1DischargeAmount": "100000.00",
        "Total": "100000.00",
    }
    # 530 = L210; 545 = 530; 570 = 0; 600 = 525 - 545 = 175,000
    assert (result["530"], result["545"], result["570"], result["600"]) == (
        Decimal("100000.00"),
        Decimal("100000.00"),
        0,
        Decimal("175000.00"),
    )
    assert (result["142"], result["655"], result["657"]) == (1, 1, 1)
    assert "650" not in result
    relief = computation.reliefs.research_and_development
    assert relief is not None
    assert (relief.scheme, relief.rdec, relief.set_off) == (
        "merged_rdec",
        Decimal("100000.00"),
        Decimal("100000.00"),
    )


def test_r2_merged_rdec_for_a_loss_maker_is_paid_after_notional_tax_at_19_percent():
    computation = compute(
        **CALENDAR_2025,
        profit_and_loss={"turnover": 10_000, "other_expenses": 100_000},
        research_and_development=rd("rdec", 200_000, company_is_sme=True),
        supplementary_pages={"L": paye(30_000, "Step3")},
    )

    page = page_of(computation, "L")
    # L15 = 40,000; no CT, so step 2: L55 = 19% x 40,000 = 7,600; L60 = 32,400;
    # L62 = 40,000 - 0 = 40,000; L65 = 40,000 - 32,400 = 7,600
    assert page["Step2"] == {
        "Step1BalanceCarriedForwardToStep2": "40000.00",
        "CorporationTaxChargeOnRDECforThisAccountingPeriod": "7600.00",
        "TotalRDECarisingInThisAPlessCorporationTaxChargeOnTheRDECforThisAP": "32400.00",
        "RDECarisingInThisAPlessRemainingCorporationTaxLiabilityAtStep1": "40000.00",
        "Step2RestrictionCarriedForwardToNextAccountingPeriod": "7600.00",
    }
    # Cap 20,000 + 3 x 30,000 = 110,000 does not bite
    step_3 = page["Step3"]
    assert step_3[
        "TotalRelevantExpenditureOnRandDWorkersPAYEandNationalInsuranceContributions"
    ] == ("110000.00")
    assert step_3["Step3RestrictionCarriedForwardToNextAP"] == "0.00"
    assert page["Step7"] == {"PayableRDEC": "32400.00"}
    assert page["RDECcarriedForward"]["TotalCarriedForwardToNextAP"] == "7600.00"
    result = boxes(computation)
    assert (result["880"], result["530"]) == (Decimal("32400.00"), 0)
    assert (result["650"], result["475"]) == (1, 0)
    # Trade: 10,000 - 100,000 + 40,000 RDEC = 50,000 loss carried forward
    assert computation.losses_carried_forward == 50_000


def test_merged_rdec_notional_tax_is_25_percent_for_main_rate_companies():
    computation = compute(
        profit_and_loss={"turnover": 260_000},
        research_and_development=rd("rdec", 2_000_000),
        supplementary_pages={"L": paye(100_000, "Step3")},
    )

    page = page_of(computation, "L")
    # RDEC 400,000; CT 25% x 660,000 = 165,000 discharged at step 1; L55 = 25% x 400,000
    assert page["Step1"]["AmountOfRDECusedToDischargeCorporationTaxAtStep1"] == "165000.00"
    assert page["Step2"]["CorporationTaxChargeOnRDECforThisAccountingPeriod"] == "100000.00"
    # L62 = 235,000 is less than L60 = 300,000, so nothing is restricted
    assert page["Step2"]["Step2RestrictionCarriedForwardToNextAccountingPeriod"] == "0.00"
    assert page["Step7"]["PayableRDEC"] == "235000.00"
    relief = computation.reliefs.research_and_development
    assert relief is not None
    assert relief.notional_tax_rate == Decimal("0.25")


def test_r3_eris_payable_credit():
    computation = compute(
        profit_and_loss={"turnover": 50_000, "other_expenses": 100_000},
        research_and_development=rd("eris", 100_000, intensity="35", claim_payable_credit=True),
        supplementary_pages={"L": paye(10_000)},
    )

    result = boxes(computation)
    assert (result["650"], result["653"], result["657"]) == (1, 1, 1)
    # 660 = 100,000 + 86% additional deduction = 186,000
    assert (result["659"], result["660"], result["670"]) == (100_000, 186_000, 186_000)
    sme = page_of(computation, "L")["SME"]
    # Loss 50,000 + 86,000 = 136,000 = min(186,000, 136,000) surrendered; 14.5% = 19,720
    assert (sme["RandDexpenditure"], sme["RandDPayableTaxCreditClaim"]) == ("100000", "19720.00")
    assert sme["RandDBalancePayableTaxCredit"] == "19720.00"
    assert result["875"] == Decimal("19720.00")
    assert (computation.trading_loss_arising, computation.losses_carried_forward) == (136_000, 0)
    relief = computation.reliefs.research_and_development
    assert relief is not None
    assert (relief.additional_deduction, relief.losses_surrendered) == (86_000, 136_000)


def test_eris_credit_is_limited_to_the_loss_other_profits_cannot_absorb():
    # CIRD122000 Company B: 100,000 of other profits leaves 36,000 unrelieved; 14.5% = 5,220
    computation = compute(
        profit_and_loss={"turnover": 50_000, "other_expenses": 100_000, "interest_income": 100_000},
        research_and_development=rd("eris", 100_000, intensity="35", claim_payable_credit=True),
        supplementary_pages={"L": paye(10_000)},
    )

    assert boxes(computation)["875"] == Decimal("5220.00")


def test_eris_credit_is_capped_by_paye_with_the_allowance_reduced_for_a_short_period():
    # 1 October 2024 to 31 March 2025 is 182 days: cap 20,000 x 182/365 = 9,972.60
    computation = compute(
        **period("2024-10-01", "2025-03-31", "2025-06-01"),
        profit_and_loss={"turnover": 50_000, "other_expenses": 100_000},
        research_and_development=rd("eris", 100_000, intensity="35", claim_payable_credit=True),
        supplementary_pages={"L": {}},
    )

    assert boxes(computation)["875"] == Decimal("9972.60")
    # Loss surrendered 9,972.60 / 14.5% = 68,776.55; 136,000 - 68,777 carries forward
    assert computation.losses_carried_forward == 67_223


def test_the_paye_cap_exception_needs_limited_connected_person_spending():
    exception = {
        "SME": {
            "DoesTheExceptionAtS1058DCTA2009apply": "yes",
            "TotalExpenditureOnExternallyProvidedWorkersFromAndSubcontractingToConnectedPersons": (
                "15001"
            ),
        }
    }

    found = problems(
        profit_and_loss={"turnover": 50_000, "other_expenses": 100_000},
        research_and_development=rd("eris", 100_000, intensity="35", claim_payable_credit=True),
        supplementary_pages={"L": exception},
    )

    ((location, message),) = found.items()
    assert location[-1] == (
        "TotalExpenditureOnExternallyProvidedWorkersFromAndSubcontractingToConnectedPersons"
    )
    assert "15% of £100,000" in message


def test_r4_sme_scheme_before_april_2024():
    overrides = {
        **YEAR_TO_MARCH_2024,
        "profit_and_loss": {"turnover": 80_000, "other_expenses": 100_000},
        "supplementary_pages": {"L": paye(10_000)},
    }
    claim = rd("sme", 100_000, claim_payable_credit=True)

    computation = compute(**overrides, research_and_development=claim)
    # Loss 20,000 + 86,000 = 106,000 surrendered at 10% = 10,600
    result = boxes(computation)
    assert (result["659"], result["660"], result["875"]) == (100_000, 186_000, Decimal("10600.00"))
    assert "653" not in result

    intensive = compute(**overrides, research_and_development={**claim, "intensity": "40"})
    # R&D-intensive: 14.5% = 15,370
    assert boxes(intensive)["875"] == Decimal("15370.00")
    assert boxes(intensive)["653"] == 1


def test_sme_additional_deduction_straddling_1_april_2023_is_weighted_by_days():
    computation = compute(
        **CALENDAR_2023,
        profit_and_loss={"turnover": 500_000},
        research_and_development=rd("sme", 100_000),
    )

    # (130% x 90 days + 86% x 275 days) / 365 = 96.849%; 100,000 -> 96,849
    relief = computation.reliefs.research_and_development
    assert relief is not None
    assert relief.additional_deduction == 96_849
    assert boxes(computation)["155"] == 500_000 - 96_849


def test_large_company_rdec_straddling_1_april_2023():
    computation = compute(
        **CALENDAR_2023,
        profit_and_loss={"turnover": 10_000, "other_expenses": 100_000},
        research_and_development=rd("rdec", 100_000, rd_workers_paye_and_nic=5_000),
        supplementary_pages={"L": {}},
    )

    page = page_of(computation, "L")
    # (13% x 90 + 20% x 275) / 365 of 100,000 = 18,273.97
    assert page["Step1"]["RDECclaimForThisAccountingPeriod"] == "18273.97"
    # Notional tax at the main rate: (19% x 90 + 25% x 275) / 365 of it = 4,298.14
    assert page["Step2"]["CorporationTaxChargeOnRDECforThisAccountingPeriod"] == "4298.14"
    # Old step 3 caps at R&D workers' PAYE and NICs: 13,975.83 - 5,000 carried forward
    step_3 = page["Step3"]
    assert step_3[
        "TotalRelevantExpenditureOnRandDWorkersPAYEandNationalInsuranceContributions"
    ] == ("5000.00")
    assert page["Step7"]["PayableRDEC"] == "5000.00"
    result = boxes(computation)
    assert (result["655"], result["880"]) == (1, Decimal("5000.00"))


def test_an_sme_claim_without_a_payable_credit_needs_no_ct600l():
    computation = compute(
        research_and_development=rd("eris", 10_000, intensity="30"),
        profit_and_loss={"turnover": 5_000, "other_expenses": 10_000},
    )

    result = boxes(computation)
    # Loss 5,000 + 8,600 additional deduction
    assert computation.trading_loss_arising == 13_600
    assert (result["650"], result["659"], result["660"]) == (1, 10_000, 18_600)
    assert "142" not in result


@pytest.mark.parametrize(
    ("overrides", "field", "text"),
    [
        (
            {"research_and_development": rd("sme", 1_000)},
            "scheme",
            "The SME scheme ended",
        ),
        (
            {**YEAR_TO_MARCH_2024, "research_and_development": rd("eris", 1_000, intensity="50")},
            "scheme",
            "ERIS is for periods starting on or after 1 April 2024",
        ),
        (
            {"research_and_development": rd("eris", 1_000, intensity="29.99")},
            "intensity",
            "at least 30%",
        ),
        (
            {
                "research_and_development": {
                    **rd("rdec", 1_000),
                    "additional_information_submitted": False,
                },
                "supplementary_pages": {"L": {}},
            },
            "additional_information_submitted",
            "additional information form",
        ),
        (
            {
                "research_and_development": {
                    **rd("rdec", 1_000),
                    "claimed_in_previous_three_years": False,
                },
                "supplementary_pages": {"L": {}},
            },
            "claim_notification_submitted",
            "claim notification",
        ),
        (
            {"research_and_development": rd("rdec", 1_000)},
            "scheme",
            "Add CT600L",
        ),
        (
            {
                "research_and_development": rd(
                    "eris", 1_000, intensity="30", claim_payable_credit=True
                ),
                "supplementary_pages": {"L": {}},
            },
            "scheme",
            "only for companies whose trade makes a loss",
        ),
    ],
)
def test_claims_that_cannot_be_made(overrides, field, text):
    found = problems(**overrides)

    assert text in found[("research_and_development", field)]


def test_first_claims_before_april_2023_need_no_notification():
    claim = {**rd("sme", 1_000), "claimed_in_previous_three_years": False}

    computation = compute(
        **period("2022-04-01", "2023-03-31", "2023-06-01"), research_and_development=claim
    )

    assert "656" not in boxes(computation)


def test_a_notified_first_claim_ticks_box_656():
    claim = {
        **rd("rdec", 1_000),
        "claimed_in_previous_three_years": False,
        "claim_notification_submitted": True,
    }

    computation = compute(research_and_development=claim, supplementary_pages={"L": {}})

    assert boxes(computation)["656"] == 1


def test_ct600l_is_refused_for_an_additional_deduction_alone():
    found = problems(
        research_and_development=rd("eris", 10_000, intensity="30"),
        profit_and_loss={"turnover": 5_000, "other_expenses": 10_000},
        supplementary_pages={"L": {}},
    )

    assert list(found) == [("supplementary_pages", "L")]


def test_ct600l_without_a_claim_or_anything_brought_forward_is_refused():
    found = problems(supplementary_pages={"L": {}})

    assert list(found) == [("research_and_development",)]


def test_rdec_brought_forward_is_set_against_this_periods_tax():
    brought_forward = {"PreStep1Restriction": {"Step2RestrictionBroughtForward": "5000.00"}}

    computation = compute(supplementary_pages={"L": brought_forward})

    page = page_of(computation, "L")
    # CT 25% x 100,000 less marginal relief = 22,750; all 5,000 used before step 1
    assert page["PreStep1Restriction"]["AmountOfStep2BroughtForwardRDEC"] == "5000.00"
    assert page["PreStep1Restriction"]["RemainingCorporationTaxLiability"] == "17750.00"
    assert page["RDECcarriedForward"]["TotalCarriedForwardToNextAP"] == "0.00"
    result = boxes(computation)
    assert (result["530"], result["600"]) == (Decimal("5000.00"), Decimal("17750.00"))


def test_paye_needs_its_employer_reference():
    step_3 = {"Step3": {"PAYENICsForWhichTheCompanyIsLiableInThisAP": "30000"}}

    found = problems(
        **CALENDAR_2025,
        profit_and_loss={"turnover": 10_000, "other_expenses": 100_000},
        research_and_development=rd("rdec", 200_000),
        supplementary_pages={"L": step_3},
    )

    assert list(found) == [("supplementary_pages", "L", "Step3", "EmployerPAYEreference")]


def test_income_tax_deducted_cannot_be_given():
    found = problems(
        research_and_development=rd("rdec", 1_000),
        supplementary_pages={
            "L": {"Step1": {"IncomeTaxDeductedFromProfitsApplicableToCorporationTaxLiability": "1"}}
        },
    )

    ((location, message),) = found.items()
    assert location[-1] == "IncomeTaxDeductedFromProfitsApplicableToCorporationTaxLiability"
    assert "box 515" in message


def test_eris_is_refused_for_a_profitable_trade_even_without_a_payable_credit():
    # Review M1. CIRD121000: enhanced support under ERIS is only for R&D intensive SMEs that
    # make a trading loss before the additional deduction; a profitable company claims
    # merged-scheme RDEC.
    found = problems(
        profit_and_loss={"turnover": 500_000},
        research_and_development=rd("eris", 100_000, intensity="35"),
    )

    assert (
        "only for companies whose trade makes a loss"
        in found[("research_and_development", "scheme")]
    )


def test_accounts_include_the_rdec_income_the_tax_charge_is_on():
    # Review L3. The RDEC is left out of the profit and loss answers and added by the service;
    # the accounts show it as other income (FRS 102 grant income, above the line), so the tax
    # charge of 25% x 1,100,000 = 275,000 is on the profit the accounts show.
    computation = compute(
        profit_and_loss={"turnover": 1_000_000},
        research_and_development=rd("rdec", 500_000),
        supplementary_pages={"L": {}},
    )

    accounts = computation.accounts
    assert (accounts.other_income, accounts.profit_before_tax) == (100_000, 1_100_000)
    assert (accounts.corporation_tax, accounts.profit_after_tax) == (
        Decimal("275000.00"),
        Decimal("825000.00"),
    )


def test_a_payable_rd_tax_credit_is_a_credit_in_the_accounts_tax_line():
    # ERIS: no Corporation Tax, and a 19,720 payable credit, shown as a tax credit.
    computation = compute(
        profit_and_loss={"turnover": 50_000, "other_expenses": 100_000},
        research_and_development=rd("eris", 100_000, intensity="35", claim_payable_credit=True),
        supplementary_pages={"L": paye(10_000)},
    )

    accounts = computation.accounts
    assert accounts.corporation_tax == Decimal("-19720.00")
    assert accounts.profit_after_tax == Decimal(-50_000) + Decimal("19720.00")
