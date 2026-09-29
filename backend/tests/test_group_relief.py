"""CT600C: group relief claims and surrenders (research worked examples)."""

from answers import boxes, compute, page_of, period, problems

CALENDAR_2025 = period("2025-01-01", "2025-12-31", "2026-06-01")
AUTHORISED = {
    "AuthorisationForSimplifiedArrangements": {
        "AuthorisationWhereSimplifiedArrangement": "yes",
        "CompanyName": "Parent Ltd",
        "NameOfAuthorisedPerson": "Ada Lovelace",
        "Status": "Director",
    }
}


def claims(*rows: dict, carried_forward: tuple[dict, ...] = ()) -> dict:
    page: dict = {}
    if rows:
        page["ClaimToGroupRelief"] = {
            "CompanyInformation": {"Company": list(rows)},
            "ClaimAuthorisation": AUTHORISED,
        }
    if carried_forward:
        page["GroupReliefForCarriedForwardLosses"] = {
            "CompanyInformation": {"Company": list(carried_forward)},
            "ClaimAuthorisation": AUTHORISED,
        }
    return page


def claim(amount: int, reference: str = "1234567891", accounting_period=None) -> dict:
    row = {"Name": "Sub Ltd", "TaxReference": reference, "AmountClaimed": str(amount)}
    if accounting_period:
        row["AccountingPeriod"] = {"From": accounting_period[0], "To": accounting_period[1]}
    return row


def test_worked_example_1_coterminous_claim_is_deducted_after_donations():
    # P: box 235 = 300,000, donations 10,000, claims S's 200,000 loss; one associated company.
    computation = compute(
        **CALENDAR_2025,
        profit_and_loss={"turnover": 300_000},
        tax_adjustments={"qualifying_donations": 10_000, "associated_companies": 1},
        supplementary_pages={"C": claims(claim(200_000))},
    )

    result = boxes(computation)
    assert (result["300"], result["305"], result["310"], result["312"]) == (
        300_000,
        10_000,
        200_000,
        0,
    )
    # 315 = 300,000 - 10,000 - 200,000
    assert result["315"] == 90_000
    # Limits 25,000 / 125,000 for two companies, so marginal relief applies
    assert result["435"] > 0
    assert (
        page_of(computation, "C")["ClaimToGroupRelief"]["CompanyInformation"]["TotalAmountClaimed"]
        == "200000"
    )
    relief = computation.reliefs.group_relief
    assert relief is not None
    assert (relief.claimed, relief.available, relief.unused) == (200_000, 290_000, 90_000)


def test_claims_cannot_exceed_profits_after_donations():
    found = problems(
        tax_adjustments={"qualifying_donations": 10_000},
        supplementary_pages={"C": claims(claim(95_000))},
    )

    location = (
        "supplementary_pages",
        "C",
        "ClaimToGroupRelief",
        "CompanyInformation",
        "Company",
        0,
        "AmountClaimed",
    )
    # Available: 100,000 - 10,000 = 90,000
    assert "£90,000 or less" in found[location]
    assert "£90,000 or less in total" in found[(*location[:4], "TotalAmountClaimed")]


def test_worked_example_2_non_coterminous_claim_is_limited_to_the_overlap():
    # A (profit 72,000, calendar 2025) claims from D (loss 120,000, year to 31 March 2026),
    # which already surrendered 5,000 to C for the common period. Overlap: 1 April to
    # 31 December 2025, 275 of 365 days. A's available profits for it: 72,000 x 275/365 =
    # 54,246.57; D's surrenderable: 120,000 x 275/365 - 5,000 = 85,410.95. Relief 54,246.
    # (CTM80255 counts months, giving 54,000; the service apportions by days.)
    d = claim(54_246, accounting_period=("2025-04-01", "2026-03-31"))
    surrenderer = {
        "tax_reference": "1234567891",
        "surrenderable_amount": 120_000,
        "surrendered_to_others": 5_000,
    }
    overrides = {
        **CALENDAR_2025,
        "profit_and_loss": {"turnover": 72_000},
        "group_relief_surrenderers": [surrenderer],
    }

    assert boxes(compute(**overrides, supplementary_pages={"C": claims(d)}))["315"] == 17_754
    too_much = claim(54_247, accounting_period=("2025-04-01", "2026-03-31"))
    found = problems(**overrides, supplementary_pages={"C": claims(too_much)})
    (message,) = found.values()
    assert "£54,246 or less" in message
    assert "275 days" in message


def test_the_surrendering_companys_figures_can_limit_the_claim():
    # D can surrender 60,000 for its year: 60,000 x 275/365 - 5,000 = 40,205.48
    d = claim(45_000, accounting_period=("2025-04-01", "2026-03-31"))
    surrenderer = {
        "tax_reference": "1234567891",
        "surrenderable_amount": 60_000,
        "surrendered_to_others": 5_000,
    }

    found = problems(
        **CALENDAR_2025,
        profit_and_loss={"turnover": 72_000},
        group_relief_surrenderers=[surrenderer],
        supplementary_pages={"C": claims(d)},
    )

    (message,) = found.values()
    assert "£40,205 or less" in message
    assert "surrendering company can surrender" in message


def test_worked_example_3_consortium_share_limits_the_claim():
    # X's lowest ownership proportion of JV is 35% (votes); JV's loss is 100,000.
    surrenderer = {
        "tax_reference": "1234567891",
        "surrenderable_amount": 100_000,
        "consortium_share": "35",
    }

    assert (
        boxes(
            compute(
                group_relief_surrenderers=[surrenderer],
                supplementary_pages={"C": claims(claim(35_000))},
            )
        )["310"]
        == 35_000
    )
    found = problems(
        group_relief_surrenderers=[surrenderer],
        supplementary_pages={"C": claims(claim(35_001))},
    )
    assert "£35,000 or less" in next(iter(found.values()))


def test_periods_that_do_not_overlap_cannot_be_claimed_for():
    row = claim(1_000, accounting_period=("2023-04-01", "2024-03-31"))

    found = problems(supplementary_pages={"C": claims(row)})

    (location,) = found
    assert location[-1] == "AccountingPeriod"


def test_surrenderer_figures_must_match_a_claim():
    found = problems(
        group_relief_surrenderers=[{"tax_reference": "9999999999", "surrenderable_amount": 1}],
        supplementary_pages={"C": claims(claim(1_000))},
    )

    assert list(found) == [("group_relief_surrenderers", 0, "tax_reference")]


def test_carried_forward_losses_are_claimed_after_current_period_relief():
    computation = compute(
        supplementary_pages={"C": claims(claim(60_000), carried_forward=(claim(30_000),))}
    )

    result = boxes(computation)
    assert (result["310"], result["312"], result["315"]) == (60_000, 30_000, 10_000)
    found = problems(
        supplementary_pages={"C": claims(claim(60_000), carried_forward=(claim(40_001),))}
    )
    assert any("£40,000 or less" in message for message in found.values())


def test_tonnage_tax_profits_are_ring_fenced_from_group_relief_and_donations():
    ships = {
        "TonnageTax": {
            "Information": {
                "TrainingCertificate": "yes",
                "CompanyMetCharteredInLimit": "yes",
                "NotRegistered": "na",
                "OffshoreActivities": "no",
            },
            "QualifyingShips": {
                "Ship": [
                    {
                        "Name": "Northern Star",
                        "IMOnumber": "9123456",
                        "InterestInShip": "O",
                        "GrossTonnage": "45000",
                        "NetTonnage": "30099",
                        "NumberDays": "365",
                        "Flagged": "yes",
                        "FirstTime": "no",
                    }
                ]
            },
        }
    }
    # Tonnage tax profits 36,135 (99.00 a day), trading profits 10,000.
    overrides = {
        "profit_and_loss": {"turnover": 10_000},
        "tax_adjustments": {"qualifying_donations": 50_000},
    }

    computation = compute(**overrides, supplementary_pages={"F": ships})
    result = boxes(computation)
    assert (result["200"], result["305"], result["315"]) == (36_135, 10_000, 36_135)
    found = problems(**overrides, supplementary_pages={"F": ships, "C": claims(claim(1))})
    assert any("£0 or less" in message for message in found.values())


def surrender(amount: int, trading_losses: int | None = None) -> dict:
    return {
        "SurrenderedGroupRelief": {
            "TradingLosses": str(amount if trading_losses is None else trading_losses),
            "SurrenderInformation": {
                "Company": [
                    {
                        "Name": "Parent Ltd",
                        "TaxReference": "1234567891",
                        "AmountSurrendered": str(amount),
                    }
                ]
            },
            "ConsentToSurrender": {
                "ConsentOptions": {"NoticeOfConsentCompleted": "yes"},
                "Declaration": {
                    "AcceptDeclaration": "yes",
                    "Name": "Ada Lovelace",
                    "Status": "Director",
                },
            },
        }
    }


def test_surrendered_trading_losses_leave_the_carry_forward_and_fill_the_declaration():
    # Turnover 10,000, expenses 30,000: loss 20,000, of which 15,000 is surrendered.
    computation = compute(
        profit_and_loss={"turnover": 10_000, "other_expenses": 30_000},
        supplementary_pages={"C": surrender(15_000)},
    )

    part = page_of(computation, "C")["SurrenderedGroupRelief"]
    assert (part["TotalSurrender"], part["SurrenderInformation"]["AmountSurrenderedTotal"]) == (
        "15000",
        "15000",
    )
    declaration = part["ConsentToSurrender"]["Declaration"]
    assert (declaration["CompanyName"], declaration["TaxReference"]) == (
        "Acme Widgets Ltd",
        "1234567890",
    )
    assert declaration["AccountingPeriod"] == {"From": "2024-04-01", "To": "2025-03-31"}
    assert (computation.trading_loss_arising, computation.losses_carried_forward) == (
        20_000,
        5_000,
    )
    relief = computation.reliefs.group_relief
    assert relief is not None
    assert (relief.surrendered, relief.trading_losses_surrendered) == (15_000, 15_000)


def test_trading_losses_surrendered_cannot_exceed_the_loss():
    found = problems(
        profit_and_loss={"turnover": 10_000, "other_expenses": 30_000},
        supplementary_pages={"C": surrender(25_000)},
    )

    assert list(found) == [("supplementary_pages", "C", "SurrenderedGroupRelief", "TradingLosses")]


def test_surrender_details_must_add_up_to_the_total():
    found = problems(
        profit_and_loss={"turnover": 10_000, "other_expenses": 30_000},
        supplementary_pages={"C": surrender(15_000, trading_losses=10_000)},
    )

    ((location, message),) = found.items()
    assert location[-1] == "AmountSurrenderedTotal"
    assert "add up to box C80" in message
