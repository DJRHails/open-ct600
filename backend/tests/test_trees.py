import pytest

from open_ct600.schema.spec import load_spec
from open_ct600.schema.trees import TreeProblem, validate_tree

SPEC = load_spec()
LOANS_PAGE = SPEC.page("A").node
CFC_PAGE = SPEC.page("B").node
TONNAGE_PAGE = SPEC.page("F").node


def loans_page(**overrides) -> dict:
    page = {
        "BeforeEndPeriod": "no",
        "LoansInformation": {
            "Loan": [
                {"Name": "Ada Lovelace", "AmountOfLoan": "5000"},
                {"Name": "Charles Babbage", "AmountOfLoan": "1000"},
            ],
            "TotalLoans": "6000",
            "TaxChargeable": "2025.00",
        },
        "TaxPayable": "2025.00",
    }
    return {**page, **overrides}


def messages(problems: list[TreeProblem]) -> list[str]:
    return [problem.message for problem in problems]


def test_a_complete_page_is_valid():
    assert validate_tree(LOANS_PAGE, loans_page()) == []


def test_an_empty_page_reports_each_required_element():
    problems = validate_tree(LOANS_PAGE, {})

    assert [(p.path, p.box) for p in problems] == [
        (("BeforeEndPeriod",), "A5"),
        (("TaxPayable",), "A80"),
    ]
    assert problems[0].message.startswith("Select have loans made during the period")
    assert problems[1].message == "Enter tax payable s419"


def test_problems_are_located_by_json_path_with_list_indexes():
    page = loans_page()
    page["LoansInformation"]["Loan"][1]["Name"] = "X"

    (problem,) = validate_tree(LOANS_PAGE, page)

    assert problem.path == ("LoansInformation", "Loan", 1, "Name")
    assert problem.box == "A10A"
    assert problem.message == "Enter name of participator or associate, 2 to 56 characters"


def test_unknown_keys_are_rejected():
    (problem,) = validate_tree(LOANS_PAGE, loans_page(Goodwill="1"))

    assert problem.path == ("Goodwill",)
    assert problem.message.startswith("Remove Goodwill: it is not part of loans to participators")


def test_repeating_elements_must_be_lists_with_at_least_the_minimum():
    single = loans_page()
    single["LoansInformation"]["Loan"] = {"Name": "Ada Lovelace", "AmountOfLoan": "5000"}
    empty = loans_page()
    empty["LoansInformation"]["Loan"] = []

    assert messages(validate_tree(LOANS_PAGE, single)) == ["Loan must be a list"]
    assert messages(validate_tree(LOANS_PAGE, empty)) == ["Add at least 1: Loan"]


def test_maximum_occurrences_are_enforced():
    ship = TONNAGE_PAGE.child("TonnageTax")
    assert ship is not None
    qualifying = ship.child("QualifyingShips")
    assert qualifying is not None
    ships = qualifying.child("Ship")
    assert ships is not None and ships.max == 200

    problems = validate_tree(qualifying, {"Ship": [{}] * 201})

    assert "Add no more than 200: " in problems[0].message


@pytest.mark.parametrize(
    ("amount", "message"),
    [
        ("0", "Amount of loan must be £1 or more"),
        ("12.50", "Amount of loan must be a whole number of pounds, like 1234"),
        ("-5", "Amount of loan must be a whole number of pounds, like 1234"),
        ("100000000000", "Amount of loan must be £99,999,999,999 or less"),
        (5000, 'Amount of loan must be given as text, like "1234"'),
        ("", "Enter amount of loan"),
    ],
)
def test_whole_pound_values(amount, message):
    page = loans_page()
    page["LoansInformation"]["Loan"][0]["AmountOfLoan"] = amount

    assert messages(validate_tree(LOANS_PAGE, page)) == [message]


@pytest.mark.parametrize(
    ("tax", "message"),
    [
        ("2025", None),
        ("2025.5", None),
        (
            "0.00",
            "Tax due before any relief for loans repaid, released or written off after the "
            "end of the period must be £0.01 or more",
        ),
        ("20.255", "must be an amount in pounds and pence, like 1234.56"),
    ],
)
def test_money_values(tax, message):
    page = loans_page()
    page["LoansInformation"]["TaxChargeable"] = tax

    found = messages(validate_tree(LOANS_PAGE, page))

    if message is None:
        assert found == []
    else:
        assert len(found) == 1 and message in found[0]


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("yes", None),
        ("maybe", "Select yes or no for have loans made"),
    ],
)
def test_yes_no_values(value, message):
    found = messages(validate_tree(LOANS_PAGE, loans_page(BeforeEndPeriod=value)))

    assert found == [] if message is None else found[0].startswith(message)


def relief_page(date: str) -> dict:
    return loans_page(
        ReliefEarlierThan={
            "Loan": [{"Name": "Ada Lovelace", "AmountRepaid": "100", "Date": date}],
            "TotalLoans": "100",
            "ReliefDue": "33.75",
        }
    )


@pytest.mark.parametrize("date", ["2025-02-30", "30/01/2025", "2025-1-5"])
def test_dates_must_be_real_iso_dates(date):
    (problem,) = validate_tree(LOANS_PAGE, relief_page(date))

    assert problem.path == ("ReliefEarlierThan", "Loan", 0, "Date")
    assert problem.message == (
        "Date of repayment, release or write off must be a real date, like 2025-03-31"
    )


def test_a_valid_date_passes():
    assert validate_tree(LOANS_PAGE, relief_page("2025-01-05")) == []


def cfc_company(**answers) -> dict:
    return {"CompanyInformation": [{"Name": "Offshore Ltd", "Territory": "Jersey", **answers}]}


def test_a_required_choice_needs_one_branch():
    problems = validate_tree(CFC_PAGE, cfc_company())

    assert [p.path for p in problems] == [("CompanyInformation", 0)]
    assert problems[0].message.startswith("Answer one of ")


def test_a_choice_accepts_exactly_one_branch():
    assert validate_tree(CFC_PAGE, cfc_company(ExemptionDue="Excluded territories")) == []


def test_a_choice_rejects_two_branches():
    both = cfc_company(
        ExemptionDue="Excluded territories",
        CFCTaxCalculation={
            "Percentage": "100",
            "ChargeableProfits": "1000",
            "TaxOnChargeable": "250",
        },
    )

    problems = validate_tree(CFC_PAGE, both)

    assert messages(problems)[0].startswith("Answer only one of ")


def test_the_chosen_branch_is_validated_and_the_other_is_not_required():
    partial = cfc_company(CFCTaxCalculation={"Percentage": "150", "ChargeableProfits": "1000"})

    problems = validate_tree(CFC_PAGE, partial)

    assert [p.path[-1] for p in problems] == ["Percentage", "TaxOnChargeable", "CFCchargeDue"]
    assert "must be 100% or less" in problems[0].message


def test_character_patterns_are_enforced():
    page = loans_page()
    page["LoansInformation"]["Loan"][0]["Name"] = "Ada £ovelace"

    (problem,) = validate_tree(LOANS_PAGE, page)

    assert (
        problem.message
        == "Name of participator or associate contains a character that is not allowed"
    )


def test_a_group_given_as_a_scalar_is_reported():
    (problem,) = validate_tree(LOANS_PAGE, loans_page(LoansInformation="lots"))

    assert problem.path == ("LoansInformation",)
    assert problem.message == "Loans information must be a set of answers"


def test_the_page_itself_must_be_an_object():
    (problem,) = validate_tree(LOANS_PAGE, ["not", "a", "page"])

    assert problem.path == ()
