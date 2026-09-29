"""Calculated boxes, the page tree helper, and the main-return boxes the service fills."""

from decimal import Decimal

import pytest
from answers import boxes, compute, problems

from open_ct600.computation import BOX_LABELS, main_return_boxes
from open_ct600.pages.definitions import COMPUTED_BOXES, computed_paths
from open_ct600.pages.tree import PageTree, box_paths
from open_ct600.schema.spec import PAGE_CODES, RETURN_PATH, load_spec
from open_ct600.schema.trees import validate_tree

SPEC = load_spec()
MAIN_KINDS = {
    "pounds": {"pounds"},
    "money": {"money"},
    "count": {"integer"},
    "rate": {"percent", "decimal"},
    "year": {"year"},
    "flag": {"yes"},
}


@pytest.mark.parametrize("code", PAGE_CODES)
def test_every_calculated_box_is_on_its_page(code):
    page_boxes = {node.box for node in SPEC.page(code).node.walk() if node.box}

    assert page_boxes >= COMPUTED_BOXES[code]
    assert computed_paths(code) or not COMPUTED_BOXES[code]


def test_groups_of_calculated_boxes_are_calculated_as_a_whole():
    paths = computed_paths("L")
    root = SPEC.page("L").node.path

    assert f"{root}/Step2" in paths
    assert f"{root}/TotalRandDSetOffAgainstLiabilities" in paths
    assert f"{root}/Step3" not in paths  # the company answers its PAYE there
    assert f"{root}/Step3/Step3RestrictionCarriedForwardToNextAP" in paths


def test_every_main_return_box_the_service_fills_is_in_the_schema():
    assert set(map(str, BOX_LABELS)) <= main_return_boxes()


def test_every_filled_box_has_its_schema_kind():
    kinds = {
        node.box: node.kind
        for node in SPEC.node(RETURN_PATH).walk()
        if node.box and not node.path.startswith(tuple(p.node.path for p in SPEC.pages()))
    }
    computation = compute(
        tax_adjustments={"chargeable_gains": 5_000},
        supplementary_pages={"A": {"BeforeEndPeriod": "yes"}},
    )

    for box in computation.boxes:
        assert kinds[box.box] in MAIN_KINDS[box.kind], box.box


def test_boxes_are_in_box_number_order():
    numbers = [int(box.box) for box in compute().boxes]

    assert numbers == sorted(numbers)


def test_chargeable_gains_give_net_gains_in_box_220():
    result = boxes(compute(tax_adjustments={"chargeable_gains": 5_000}))

    assert (result["210"], result["220"], result["235"]) == (5_000, 5_000, 105_000)
    assert "210" not in boxes(compute())


@pytest.mark.parametrize(("end", "given"), [("2023-03-31", False), ("2023-04-01", True)])
def test_associated_companies_box_326_is_only_for_periods_ending_from_april_2023(end, given):
    start = "2022-04-01" if end == "2023-03-31" else "2022-04-02"
    result = boxes(
        compute(
            period={"start": start, "end": end},
            accounts={"approval_date": "2023-06-01"},
            tax_adjustments={"associated_companies": 1},
        )
    )

    assert ("326" in result) is given


def test_page_tree_reads_and_writes_by_box_id():
    page = PageTree("A", {"BeforeEndPeriod": "no"})

    page.set("A20", Decimal("12.5"))
    page.set("A15", 100)

    assert page.tree == {
        "BeforeEndPeriod": "no",
        "LoansInformation": {"TaxChargeable": "12.50", "TotalLoans": "100"},
    }
    assert page.amount("A20") == Decimal("12.50")
    assert page.amount("A80") == 0
    page.set("A20", None)
    page.set("A15", None)
    assert page.tree == {"BeforeEndPeriod": "no"}


def test_page_tree_rows_and_totals():
    page = PageTree(
        "A",
        {"LoansInformation": {"Loan": [{"Name": "A", "AmountOfLoan": "5"}, {"AmountOfLoan": "7"}]}},
    )

    rows = page.rows("A10B")
    assert page.total("A10B") == 12
    assert [row.text("A10A") for row in rows] == ["A", None]
    assert rows[1].location("A10A") == (
        "supplementary_pages",
        "A",
        "LoansInformation",
        "Loan",
        1,
        "Name",
    )
    with pytest.raises(ValueError, match="read from a row"):
        page.amount("A10B")


def test_page_tree_refuses_pence_in_whole_pound_boxes_and_unknown_boxes():
    page = PageTree("A", {})

    with pytest.raises(ValueError, match="whole numbers"):
        page.set("A15", Decimal("1.5"))
    with pytest.raises(KeyError, match="no box Z1"):
        page.set("Z1", 1)


def test_box_index_covers_every_page_box():
    for code in PAGE_CODES:
        page_boxes = {node.box for node in SPEC.page(code).node.walk() if node.box}
        assert set(box_paths(code)) == page_boxes


def test_answers_leave_calculated_boxes_out_but_need_the_rest():
    node = SPEC.page("A").node
    loan = {"Loan": [{"Name": "Ada Lovelace", "AmountOfLoan": "5"}]}

    assert (
        validate_tree(
            node, {"BeforeEndPeriod": "no", "LoansInformation": loan}, computed_paths("A")
        )
        == []
    )
    strict = validate_tree(node, {"BeforeEndPeriod": "no", "LoansInformation": loan})
    assert [problem.box for problem in strict] == ["A15", "A20", "A80"]


def test_a_dormant_company_has_no_activity():
    found = problems(accounts={"dormant": True, "trading_status": "never_traded"})

    assert list(found) == [("profit_and_loss", "turnover")]
    assert "dormant company" in found[("profit_and_loss", "turnover")]


def test_a_dormant_company_is_not_trading():
    found = problems(profit_and_loss={"turnover": 0}, accounts={"dormant": True})

    assert list(found) == [("accounts", "trading_status")]


def test_a_dormant_company_has_no_tax():
    loans = {
        "BeforeEndPeriod": "no",
        "LoansInformation": {"Loan": [{"Name": "Ada Lovelace", "AmountOfLoan": "1000"}]},
    }

    found = problems(
        profit_and_loss={"turnover": 0},
        accounts={"dormant": True, "trading_status": "never_traded"},
        supplementary_pages={"A": loans},
    )

    assert list(found) == [("accounts", "dormant")]


def test_a_dormant_company_files_a_nil_return():
    computation = compute(
        profit_and_loss={"turnover": 0},
        accounts={"dormant": True, "trading_status": "no_longer_trading"},
    )

    assert computation.tax.tax_chargeable == 0
