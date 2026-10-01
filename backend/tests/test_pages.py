"""Supplementary pages B, D, E, F, H, I, J, K, M, N and P (research worked examples)."""

from decimal import Decimal

import pytest
from answers import BANK_DETAILS, CREATIVES_FORM, boxes, compute, page_of, period, problems

from open_ct600.pages.tonnage_tax import daily_profit

CALENDAR_2025 = period("2025-01-01", "2025-12-31", "2026-06-01")


def test_cfc_worked_example():
    cfcs = {
        "CompanyInformation": [
            {
                "Name": "Alpha Ltd",
                "Territory": "Territory X",
                "CFCTaxCalculation": {
                    "Percentage": "60.00",
                    "ChargeableProfits": "1000000",
                    "CreditableTax": "48000.00",
                },
            },
            {
                "Name": "Beta SA",
                "Territory": "Territory Y",
                "ExemptionDue": "Low Profits Exemption",
            },
        ]
    }

    computation = compute(**CALENDAR_2025, supplementary_pages={"B": cfcs})

    page = page_of(computation, "B")
    # F = 25% x 60% x 1,000,000 = 150,000.00; J = 150,000 - 48,000 = 102,000.00
    alpha = page["CompanyInformation"][0]["CFCTaxCalculation"]
    assert (alpha["TaxOnChargeable"], alpha["CFCchargeDue"]) == ("150000.00", "102000.00")
    assert (page["TotalTaxChargeable"], page["TotalCreditableTax"]) == ("150000.00", "48000.00")
    assert "TotalReliefInTaxTerms" not in page
    assert page["TotalCFCtaxChargeble"] == "102000.00"
    result = boxes(computation)
    assert (result["100"], result["490"], result["500"]) == (
        1,
        Decimal("102000.00"),
        Decimal("102000.00"),
    )
    assert result["510"] == result["475"] + Decimal("102000.00")


def test_cfc_deductions_cannot_exceed_the_tax():
    cfcs = {
        "CompanyInformation": [
            {
                "Name": "Alpha Ltd",
                "Territory": "Territory X",
                "CFCTaxCalculation": {
                    "Percentage": "60.00",
                    "ChargeableProfits": "1000",
                    "CreditableTax": "150.01",
                },
            }
        ]
    }

    found = problems(**CALENDAR_2025, supplementary_pages={"B": cfcs})

    ((location, message),) = found.items()
    assert location[-1] == "CreditableTax"
    assert "£150.00 or less" in message


LEGACY = {
    "Forename": "X",
    "Surname": "X",
    "Address": ["X"],
    "Overseas": "yes",
    "Date": "2025-06-15",
    "Amount": "5000",
}
"""An aggregated legacy row, as HMRC's guidance describes."""
CHARITY = {
    "ClaimExemption": {
        "Status": {"ClaimingExemptionAllOrPart": "yes", "AllCharitable": {"AllExempt": "yes"}}
    },
    "InformationRequired": {
        "Income": {"InvestmentIncome": "12000", "GiftAid": "28000"},
        "Expenditure": {"GeneralAdminCosts": "4000", "GrantsDonationsWithinUK": "30000"},
        "Assets": {"LegacyPayments": {"Payment": [LEGACY]}},
    },
}


def test_charity_totals_and_all_exempt_income():
    computation = compute(
        **CALENDAR_2025,
        company={"company_type": 8},
        profit_and_loss={"turnover": 40_000, "interest_income": 12_000},
        supplementary_pages={"E": CHARITY},
    )

    information = page_of(computation, "E")["InformationRequired"]
    # E88 = E200 = 5,000; E90 = 12,000 + 28,000 + 5,000 = 45,000; E125 = 34,000
    assert information["Assets"]["LegacyPayments"]["Total"] == "5000"
    assert (information["Income"]["LegacyIncome"], information["Income"]["Total"]) == (
        "5000",
        "45000",
    )
    assert information["Expenditure"]["Total"] == "34000"
    result = boxes(computation)
    assert (result["115"], result["155"], result["170"], result["315"], result["440"]) == (
        1,
        0,
        0,
        0,
        0,
    )


def test_charity_legacy_rows_need_a_postcode_or_overseas():
    rows = [{**LEGACY, "Postcode": "SW1A 1AA"}]
    page = {
        "ClaimExemption": CHARITY["ClaimExemption"],
        "InformationRequired": {"Assets": {"LegacyPayments": {"Payment": rows}}},
    }

    found = problems(**CALENDAR_2025, supplementary_pages={"E": page})

    legacies = ("supplementary_pages", "E", "InformationRequired", "Assets", "LegacyPayments")
    assert list(found) == [(*legacies, "Payment", 0, "Postcode")]


def ship(name: str, net_tonnage: int, days: int, interest: str = "O") -> dict:
    return {
        "Name": name,
        "IMOnumber": "9123456",
        "InterestInShip": interest,
        "GrossTonnage": str(net_tonnage * 2),
        "NetTonnage": str(net_tonnage),
        "NumberDays": str(days),
        "Flagged": "yes",
        "FirstTime": "no",
    }


def tonnage_page(*ships: dict, allowance: str | None = None) -> dict:
    information = {
        "TrainingCertificate": "yes",
        "CompanyMetCharteredInLimit": "yes",
        "NotRegistered": "na",
        "OffshoreActivities": "yes" if allowance else "no",
    }
    tonnage_tax: dict = {"Information": information}
    if allowance:
        tonnage_tax["OffshoreTrainingAllowance"] = {"OffsetAgainstCorpTax": allowance}
    tonnage_tax["QualifyingShips"] = {"Ship": list(ships)}
    return {"TonnageTax": tonnage_tax}


def test_tonnage_tax_worked_example():
    page = tonnage_page(
        ship("Northern Star", 30_099, 365), ship("Tern", 5_450, 183, "M"), allowance="500.00"
    )

    computation = compute(
        **CALENDAR_2025,
        profit_and_loss={"turnover": 0},
        supplementary_pages={"F": page},
    )

    ships = page_of(computation, "F")["TonnageTax"]["QualifyingShips"]
    # 99.00 a day x 365 = 36,135.00; managed Tern 5.16 x 183 = 944.28
    assert [each["Profits"] for each in ships["Ship"]] == ["36135.00", "944.28"]
    assert ships["Total"] == "37079"
    result = boxes(computation)
    assert (result["120"], result["200"], result["315"]) == (1, 37_079, 37_079)
    # The training allowance is set against the tax in box 450
    assert (result["450"], result["470"]) == (Decimal("500.00"), Decimal("500.00"))
    assert result["475"] == result["440"] - Decimal("500.00")


@pytest.mark.parametrize(
    ("net_tonnage", "daily"),
    [(30_099, "99.00"), (17_371, "68.40"), (32_495, "102.60"), (99, "0.00"), (1_000, "6.00")],
)
def test_daily_tonnage_tax_profit_matches_hmrc(net_tonnage, daily):
    assert daily_profit(net_tonnage) == Decimal(daily)


def test_the_training_allowance_cannot_exceed_the_tax():
    page = tonnage_page(ship("Northern Star", 1_000, 10), allowance="999999.00")

    found = problems(**CALENDAR_2025, supplementary_pages={"F": page})

    ((location, message),) = found.items()
    assert location[-1] == "OffsetAgainstCorpTax"
    assert "carry the rest forward" in message


def test_royalties_worked_example():
    def royalty(name: str, amount: str, rate: str) -> dict:
        return {
            "RecipientName": name,
            "AddressOfRecipient": {"Line": ["1 Main Street", "Springfield"]},
            "PaymentType": "Royalty",
            "Amount": amount,
            "RoyaltiesAgreement": {"DoubleTaxationAgreement": "Country"},
            "DeductionRate": rate,
        }

    rows = [royalty("US Parent Inc", "250000", "0.00"), royalty("Licensor Pvt", "40000", "15.00")]
    computation = compute(supplementary_pages={"H": {"Royalties": rows}})

    # 40,000 x 15% = 6,000.00
    assert [row["DeductionAmount"] for row in page_of(computation, "H")["Royalties"]] == [
        "0.00",
        "6000.00",
    ]
    result = boxes(computation)
    assert (result["130"], result["645"]) == (1, 1)


def ring_fence(trade: dict, **boxes: str) -> dict:
    calculation: dict = {"Trade": trade}
    if "I20" in boxes:
        calculation["DisallowedFinancingCosts"] = {"RelatedToCompany": boxes.pop("I20")}
    names = {"I50": "MinusLosses", "I60": "FieldAllowance"}
    calculation |= {names[box]: value for box, value in boxes.items() if box in names}
    page: dict = {"CalculationOfSupplementaryCharge": calculation}
    if "I75" in boxes:
        page["LossesArising"] = boxes["I75"]
    if "I85" in boxes:
        page["NetRingFenceTrade"] = {"SupplementaryChargeTax": boxes["I85"]}
    return page


def test_ring_fence_worked_example_scaled_down():
    # The research example divided by 1,000: I5 50,000, I20 4,000, I50 10,000, I60 6,000
    page = ring_fence({"Amount": "50000", "Profits": "yes"}, I20="4000", I50="10000", I60="6000")

    computation = compute(supplementary_pages={"I": page})

    calculation = page_of(computation, "I")["CalculationOfSupplementaryCharge"]
    # I35 = 54,000 = I45; I65 = 54,000 - 16,000 = 38,000; I70 = 10% = 3,800.00
    assert calculation["DisallowedFinancingCosts"]["Total"] == "4000"
    assert (calculation["Profits"], calculation["RevisedProfits"]) == ("54000", "54000")
    assert (calculation["NetProfits"], calculation["Tax"]) == ("38000", "3800.00")
    result = boxes(computation)
    assert (result["135"], result["505"], result["590"]) == (
        1,
        Decimal("3800.00"),
        Decimal("3800.00"),
    )
    assert result["510"] == result["475"] + Decimal("3800.00")


def test_ring_fence_loss_variant_has_no_charge():
    page = ring_fence({"Amount": "3000000", "Losses": "yes"}, I20="1000000", I75="2000000")

    computation = compute(supplementary_pages={"I": page})

    calculation = page_of(computation, "I")["CalculationOfSupplementaryCharge"]
    # I35 = max(1,000,000 - 3,000,000, 0) = 0; I70 omitted
    assert (calculation["Profits"], calculation["NetProfits"]) == ("0", "0")
    assert "Tax" not in calculation
    assert "505" not in boxes(computation)


def test_ring_fence_loss_needs_the_losses_arising():
    page = ring_fence({"Amount": "3000000", "Losses": "yes"}, I20="1000000")

    found = problems(supplementary_pages={"I": page})

    assert list(found) == [("supplementary_pages", "I", "LossesArising")]


def test_restitution_tax_worked_example():
    page = {"TaxCalculation": {"RestitutionInterest": "1000000"}}

    computation = compute(**CALENDAR_2025, supplementary_pages={"K": page})

    calculation = page_of(computation, "K")["TaxCalculation"]
    # 1,000,000 x 90/365 = 246,575.34 -> 246,575 in FY2024; 45% = 110,958.75 and 339,041.25
    assert calculation["TaxCalculation"] == {
        "FinancialYearOne": {
            "Year": "2024",
            "AmountOfInterest": "246575",
            "TaxRate": "45.00",
            "Tax": "110958.75",
        },
        "FinancialYearTwo": {
            "Year": "2025",
            "AmountOfInterest": "753425",
            "TaxRate": "45.00",
            "Tax": "339041.25",
        },
    }
    result = boxes(computation)
    assert calculation["TotalRestitutionTax"] == "450000.00"
    assert calculation["SAbeforeRestitutionTax"] == f"{result['525']:.2f}"
    assert (result["141"], result["527"]) == (1, Decimal("450000.00"))
    # 528 = 525 + 527; K30 = K5 + K20 - K25
    assert result["528"] == result["525"] + Decimal("450000.00")
    assert calculation["SAafterRestitutionTax"] == f"{result['528']:.2f}"


def test_restitution_tax_withheld_by_hmrc_leaves_nil_payable():
    page = {"TaxCalculation": {"RestitutionInterest": "1000", "TaxAlreadyWithheld": "450.00"}}

    computation = compute(supplementary_pages={"K": page})

    calculation = page_of(computation, "K")["TaxCalculation"]
    assert "FinancialYearTwo" not in calculation["TaxCalculation"]
    assert calculation["RestitutionTaxNowPayable"] == "0.00"
    assert boxes(computation)["527"] == 0


def address() -> dict:
    return {"Line": ["1 Dock Road", "Tilbury"]}


FREEPORTS = {
    "EnhancedSBAinFreeports": [
        {
            "LocationOfFreeport": "7",
            "AddressOfBusinessOperation": address(),
            "DateStructureOrBuildingWasBroughtIntoQualifyingUse": "2025-04-01",
            "DateOfFirstContractForConstruction": "2023-06-01",
            "TotalAmountOfQualifyingExpenditure": "1200000",
            "TotalSBAclaimAmount": "120000",
        },
        {
            "LocationOfFreeport": "15",
            "AddressOfBusinessOperation": address(),
            "DateStructureOrBuildingWasBroughtIntoQualifyingUse": "2024-10-01",
            "DateOfFirstContractForConstruction": "2024-05-15",
            "TotalAmountOfQualifyingExpenditure": "0",
            "TotalSBAclaimAmount": "50000",
        },
    ],
    "ECAforPlantAndMachineryInFreeports": [
        {
            "LocationOfFreeport": "7",
            "AddressOfBusinessOperation": address(),
            "TotalAmountOfECAclaimedWithinTheAccountingPeriod": "300000",
        },
        {
            "LocationOfFreeport": "13",
            "AddressOfBusinessOperation": address(),
            "DisposalValue": "20000",
        },
    ],
}


def test_freeports_worked_example():
    year_to_march_2026 = period("2025-04-01", "2026-03-31", "2026-06-01")

    computation = compute(
        **year_to_march_2026,
        profit_and_loss={"turnover": 1_000_000},
        tax_adjustments={"capital_allowances": 470_000},
        supplementary_pages={"M": FREEPORTS},
    )

    page = page_of(computation, "M")
    # M10 1,200,000; M15 120,000 + 50,000 = 170,000; M25 300,000; M30 20,000
    assert (page["QualifyingExpenditureTotal"], page["SBAclaimTotal"]) == ("1200000", "170000")
    assert page["AmountOfECAclaimedWithinTheAccountingPeriodTotal"] == "300000"
    assert page["DisposalValueTotal"] == "20000"
    result = boxes(computation)
    assert (result["143"], result["711"], result["760"], result["771"]) == (
        1,
        170_000,
        300_000,
        1_200_000,
    )


def test_freeport_allowances_are_part_of_the_capital_allowances():
    found = problems(
        tax_adjustments={"capital_allowances": 469_999}, supplementary_pages={"M": FREEPORTS}
    )

    ((location, message),) = found.items()
    assert location == ("supplementary_pages", "M", "SBAclaimTotal")
    assert "£470,000" in message


RPDT = {
    "Section4": {
        "AdjustedProfit": "40000000",
        "JointVentureProfit": "2000000",
        "AllowableLossRelief": "5000000",
        "AllowanceAllocationForAccountingPeriod": "25000000",
    }
}


def test_rpdt_worked_example():
    computation = compute(**CALENDAR_2025, supplementary_pages={"N": RPDT})

    section = page_of(computation, "N")["Section4"]
    # N250 42m; N270 42m - 5m = 37m; N280 37m - 25m = 12m; N285 4% = 480,000.00
    assert (section["TotalOfProfit"], section["RPDprofitsForAccountingPeriod"]) == (
        "42000000",
        "37000000",
    )
    assert (section["ProfitsChargeableToRPDT"], section["RPDTpayable"]) == (
        "12000000",
        "480000.00",
    )
    result = boxes(computation)
    assert (result["144"], result["497"], result["500"]) == (
        1,
        Decimal("480000.00"),
        Decimal("480000.00"),
    )


def test_rpdt_allowance_is_reduced_for_a_short_period():
    # 1 April to 31 December 2025: 275 days, £25m x 275/365 = £18,835,616
    short = period("2025-04-01", "2025-12-31", "2026-06-01")

    found = problems(**short, supplementary_pages={"N": RPDT})

    ((location, message),) = found.items()
    assert location[-1] == "AllowanceAllocationForAccountingPeriod"
    assert "£18,835,616 or less" in message


def test_rpdt_loss_relief_is_capped_at_half_the_excess_over_the_allowance():
    # (42m - 25m) / 2 = 8.5m
    section = {**RPDT["Section4"], "AllowableLossRelief": "8500001"}

    found = problems(**CALENDAR_2025, supplementary_pages={"N": {"Section4": section}})

    assert "£8,500,000 or less" in next(iter(found.values()))


HETV = {
    "AudioVisualExpenditureCredit": {
        "HighEndTV": {
            "RelevantGlobalExpenditure": "1000000",
            "UKrelevantGlobalExpenditure": "900000",
            "QualifyingExpenditure": "800000",
            "ExpenditureCreditClaimed": "272000.00",
        }
    }
}


def test_avec_worked_example_for_a_loss_making_producer():
    # The credit is taxable: costs of 192,000 leave 80,000 of profit once it is added. With
    # nine associated companies the limits are divided by ten, so all of it is taxed at 25%,
    # giving the research example's box 475 of 20,000.
    computation = compute(
        repayment=BANK_DETAILS,
        **period("2025-04-01", "2026-03-31", "2026-06-01"),
        profit_and_loss={"turnover": 0, "other_expenses": 192_000},
        tax_adjustments={"associated_companies": 9},
        supplementary_pages={"P": HETV},
        **CREATIVES_FORM,
    )

    result = boxes(computation)
    # Profit 272,000 - 192,000 = 80,000 at 25% (limits divided by 10) = 20,000.00
    assert result["475"] == Decimal("20000.00")
    page = page_of(computation, "P")
    assert page["AudioVisualExpenditureCredit"]["TotalAudioVisual"][
        "TotalQualifyingExpenditure"
    ] == ("800000")
    assert page["Step1"]["AmountOfAVECVGECusedToDischargeCorporationTaxAtStep1"] == "20000.00"
    assert page["Step2"] == {
        "Step1BalanceCarriedForwardToStep2": "252000.00",
        "CorporationTaxChargeOnAVECandVGECforThisAP": "68000.00",
        "TotalAVECandVGECarisingInThisAPlessCorporationTaxChargeOnTheAVECandVGECforThisAP": (
            "204000.00"
        ),
        "AVECandVGECarisingInThisAPlessRemainingCorporationTaxLiabilityAtStep1": "252000.00",
        "Step2RestrictionCarriedForwardToNextAP": "48000.00",
    }
    assert page["Step6"] == {"PayableAVECandVGEC": "204000.00"}
    assert page["AVECVGECcarriedForward"]["TotalCarriedForwardToNextAP"] == "48000.00"
    assert (result["96"], result["541"], result["545"], result["886"], result["658"]) == (
        1,
        Decimal("20000.00"),
        Decimal("20000.00"),
        Decimal("204000.00"),
        1,
    )
    # 525 = 20,000; 570 = 0; 600 = 0
    assert (result["570"], result["600"]) == (0, 0)


def test_cultural_relief_worked_example():
    theatre = {
        "CulturalReliefs": {
            "Theatre": {
                "CoreExpenditure": "500000",
                "UKcoreExpenditure": "450000",
                "AdditionalDeduction": "400000",
                "LossesSurrenderedForTaxCredit": "300000",
                "TaxCreditClaimed": "120000.00",
            }
        }
    }

    computation = compute(
        repayment=BANK_DETAILS,
        **period("2025-04-01", "2026-03-31", "2026-06-01"),
        profit_and_loss={"turnover": 100_000},
        supplementary_pages={"P": theatre},
        **CREATIVES_FORM,
    )

    totals = page_of(computation, "P")[
        "CulturalReliefsAndFilmHighEndTVchildrensTVanimationAndVideoGameTaxRelief"
    ]
    assert totals == {
        "TotalCoreExpenditureForThisAP": "500000",
        "TotalAdditionalDeductionForThisAP": "400000",
        "TotalTaxCreditClaimForThisAP": "120000.00",
        "PayableTaxCreditSetOffAgainstOtherLiabilitiesOnThisReturn": "0.00",
        "BalancePayableTaxCredit": "120000.00",
    }
    result = boxes(computation)
    # 100,000 - 400,000 additional deduction: a 300,000 loss, all surrendered for the credit
    assert (result["155"], computation.trading_loss_arising) == (0, 300_000)
    assert computation.losses_carried_forward == 0
    assert (result["663"], result["665"], result["670"]) == (500_000, 400_000, 400_000)
    assert (result["540"], result["885"]) == (0, Decimal("120000.00"))


def test_creative_claims_need_the_additional_information_form():
    found = problems(supplementary_pages={"P": HETV}, repayment=BANK_DETAILS)

    assert list(found) == [("creative_industries", "additional_information_submitted")]


def test_avec_credit_must_be_less_than_qualifying_expenditure():
    film = {
        "AudioVisualExpenditureCredit": {
            "ChildrensTV": {
                "RelevantGlobalExpenditure": "100",
                "UKrelevantGlobalExpenditure": "200",
                "QualifyingExpenditure": "80",
                "ExpenditureCreditClaimed": "80.00",
            }
        }
    }

    found = problems(supplementary_pages={"P": film}, **CREATIVES_FORM)

    assert sorted(location[-1] for location in found) == [
        "ExpenditureCreditClaimed",
        "UKrelevantGlobalExpenditure",
    ]


def test_information_pages_tick_their_boxes():
    computation = compute(
        supplementary_pages={
            "D": {"Declaration": "yes"},
            "J": {
                "AvoidanceSchemes": [
                    {"ReferenceNumber": "12345678", "AccountingPeriod": "2025-03-31"}
                ]
            },
        }
    )

    result = boxes(computation)
    assert (result["65"], result["110"], result["140"]) == (1, 1, 1)


RING_FENCE_TRADE = ring_fence({"Amount": "100000", "Profits": "yes"})


def test_ring_fence_profits_are_taxed_at_the_ring_fence_rates():
    # Review M6. CTA 2010 s279A: ring fence profits pay 30% (19% small), with ring fence
    # marginal relief of 11/400 x (250,000 - 100,000) = 4,125: 30,000 - 4,125 = 25,875.
    computation = compute(supplementary_pages={"I": RING_FENCE_TRADE})

    result = boxes(computation)
    assert (result["320"], result["335"], result["340"]) == (100_000, 100_000, 30)
    assert (result["435"], result["440"]) == (Decimal("4125.00"), Decimal("25875.00"))
    net = page_of(computation, "I")["NetRingFenceTrade"]
    # I80: ring fence Corporation Tax, carried to box 585
    assert net == {"RingFenceCorpTaxIncluded": "25875.00", "SupplementaryChargeTax": "10000.00"}
    assert (result["585"], result["590"]) == (Decimal("25875.00"), Decimal("10000.00"))


def test_ring_fence_and_other_profits_are_taxed_in_separate_rows():
    # Interest of 60,000 besides ring fence profits of 100,000: augmented profits 160,000.
    # Main rate row 60,000 x 25% = 15,000; ring fence row 100,000 x 30% = 30,000.
    # Marginal relief: 3/200 x 90,000 x 60/160 = 506.25 and 11/400 x 90,000 x 100/160 =
    # 1,546.875 -> 1,546.88. Tax 45,000 - 2,053.13 = 42,946.87.
    computation = compute(
        profit_and_loss={"turnover": 100_000, "interest_income": 60_000},
        supplementary_pages={"I": RING_FENCE_TRADE},
    )

    result = boxes(computation)
    assert (result["335"], result["340"], result["345"]) == (60_000, 25, Decimal("15000.00"))
    assert (result["350"], result["355"], result["360"]) == (100_000, 30, Decimal("30000.00"))
    assert (result["435"], result["440"]) == (Decimal("2053.13"), Decimal("42946.87"))


def test_ring_fence_profits_before_april_2023_are_refused():
    found = problems(
        **period("2022-04-01", "2023-03-31", "2023-06-01"),
        supplementary_pages={"I": RING_FENCE_TRADE},
    )

    assert "1 April 2023" in found[("supplementary_pages", "I")]
