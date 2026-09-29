import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from open_ct600.schema.generate import (
    BoxMap,
    BoxRow,
    SchemaError,
    box_id,
    generate,
    humanise,
    render,
)
from open_ct600.schema.spec import PAGE_CODES, RETURN_PATH, SPEC_PATH, load_spec

SPEC = load_spec()
LOANS = f"{RETURN_PATH}/LoansByCloseCompanies"


def test_committed_spec_is_up_to_date():
    assert SPEC_PATH.read_text(encoding="utf-8") == render(generate()), (
        "ct600-v1.994.json is stale: run `uv run python -m open_ct600.schema.generate`"
    )


def test_loader_round_trips_the_committed_spec():
    committed = json.loads(SPEC_PATH.read_text(encoding="utf-8"))

    assert SPEC.root.to_json() == committed["root"]


def test_every_supplementary_page_root_is_present():
    pages = SPEC.pages()

    assert [page.code for page in pages] == list(PAGE_CODES)
    assert len(pages) == 15
    assert all(page.node.kind == "group" and page.node.min == 0 for page in pages)
    assert [page.code for page in pages if page.dormant] == ["G"]
    assert SPEC.page("A").title == "Loans to participators by close companies"
    assert SPEC.page("L").element == "ResearchAndDevelopment"


def test_loan_participator_name_carries_its_length_limits():
    name = SPEC.node(f"{LOANS}/LoansInformation/Loan/Name")

    assert (name.box, name.kind, name.min_length, name.max_length) == ("A10A", "text", 2, 56)
    assert name.label == "Name of participator or associate"
    # Both CT_CTstringType and CTexcludedCharsStringType patterns must match.
    assert len(name.patterns) == 2


def test_loan_amount_is_non_zero_whole_pounds():
    amount = SPEC.node(f"{LOANS}/LoansInformation/Loan/AmountOfLoan")

    assert (amount.box, amount.kind) == ("A10B", "pounds")
    assert (amount.min_value, amount.max_value) == (1, Decimal(99_999_999_999))
    assert amount.patterns == ()


def test_repeating_and_optional_elements():
    loan = SPEC.node(f"{LOANS}/LoansInformation/Loan")

    assert (loan.min, loan.max, loan.repeats) == (1, None, True)
    assert SPEC.node(f"{LOANS}/LoansInformation").min == 0


def test_choice_groups_are_detected():
    company = SPEC.node(f"{RETURN_PATH}/ControlledForeignCompanies/CompanyInformation")

    (group,) = company.choices
    assert (group.id, group.min) == ("ExemptionDue|CFCTaxCalculation", 1)
    members = [child for child in company.children if child.choice == group.id]
    assert [(child.name, child.branch) for child in members] == [
        ("ExemptionDue", "ExemptionDue"),
        ("CFCTaxCalculation", "CFCTaxCalculation"),
    ]


def test_optional_choice_and_named_structure_choice():
    tracked = SPEC.node(
        f"{RETURN_PATH}/RingFenceTrade/TransferredTaxHistory/AssetInformation/"
        "TrackingOfTransferredTaxHistory/TrackedProfitsOrLosses"
    )
    adjustments = next(g for g in tracked.choices if g.id.startswith("OtherAdjustments"))
    brought_forward = tracked.child("BalanceBroughtForward")

    assert (adjustments.id, adjustments.min) == ("OtherAdjustmentsPlus|OtherAdjustmentsMinus", 0)
    assert brought_forward is not None
    assert [(g.id, g.min) for g in brought_forward.choices] == [("Profits|Losses", 1)]


def test_choice_branch_that_is_a_sequence_shares_one_branch_name():
    submission = SPEC.node(f"{RETURN_PATH}/AttachedFiles/XBRLsubmission")

    assert [(c.name, c.branch) for c in submission.children] == [
        ("Accounts", "Accounts"),
        ("Computation", "Computation"),
        ("Accounts", "Computation"),
    ]
    with pytest.raises(LookupError, match="different branches of a choice"):
        SPEC.node(f"{RETURN_PATH}/AttachedFiles/XBRLsubmission/Accounts")


def test_main_return_boxes_and_kinds():
    company_type = SPEC.node(f"{RETURN_PATH}/CompanyInformation/CompanyType")
    period_start = SPEC.node(f"{RETURN_PATH}/CompanyInformation/PeriodCovered/From")
    tick = SPEC.node(f"{RETURN_PATH}/ReturnInfoSummary/SupplementaryPages/CT600A")

    assert (company_type.box, company_type.kind) == ("4", "integer")
    assert (company_type.min_value, company_type.max_value) == (0, 11)
    assert (period_start.box, period_start.kind, period_start.min_value) == (
        "30",
        "date",
        date(2015, 4, 1),
    )
    assert (tick.box, tick.kind) == ("95", "yes")


def test_boxes_whose_box_map_paths_were_cut_off_are_matched_in_order():
    income = f"{RETURN_PATH}/CompanyTaxCalculation/Income"
    associated = f"{RETURN_PATH}/CompanyTaxCalculation/CorporationTaxChargeable/AssociatedCompanies"

    assert SPEC.node(f"{income}/NonLoanAnnuitiesAnnualPaymentsDiscounts").box == "175"
    assert SPEC.node(f"{associated}/ThisPeriod").box == "326"
    assert SPEC.node(f"{associated}/AssociatedCompaniesFinancialYears/FirstYear").box == "327"
    assert SPEC.node(f"{associated}/AssociatedCompaniesFinancialYears/SecondYear").box == "328"
    assert SPEC.node(f"{associated}/StartingOrSmallCompaniesRate").box == "329"


def test_internal_ids_are_not_boxes_but_still_label_the_element():
    page = SPEC.node(LOANS)

    assert page.box is None
    assert page.label.startswith("Loans to participators by close companies")


def test_elements_without_a_description_are_labelled_from_their_name():
    header_key = SPEC.node("/IRenvelope/IRheader/Keys/Key/@Type")

    assert header_key.label == "Type"
    assert header_key.min == 0


def test_monetary_currency_attributes_are_omitted():
    assert all(node.name != "@Currency" for node in SPEC.root.walk())


def test_page_values_carry_no_attributes():
    # Element trees give every value as a plain string, which relies on this.
    for page in SPEC.pages():
        for node in page.node.walk():
            assert node.kind == "group" or not node.children, node.path


def test_every_pattern_compiles_as_a_python_regex():
    for node in SPEC.root.walk():
        for pattern in node.patterns:
            re.compile(pattern)


def test_unknown_path_is_a_key_error():
    with pytest.raises(KeyError, match="No CT600 schema element"):
        SPEC.node(f"{RETURN_PATH}/Nonsense")


@pytest.mark.parametrize(
    ("raw", "page", "expected"),
    [
        ("[145]", None, "145"),
        ("[80A]", None, "80A"),
        ("[795/800]", None, "795/800"),
        ("[A10A]", "A", "A10A"),
        ("[C105/C110]", "C", "C105/C110"),
        ("[K15.1A]", "K", "K15.1A"),
        ("[H5Ea]", "H", "H5Ea"),
        ("[I145C1]", "I", "I145C1"),
        ("[N095]", None, None),
        ("[N120]", None, None),
        ("[N120]", "N", "N120"),
        ("[N028a]", "N", None),
        ("[LOANSINFORMATION]", "A", None),
        ("[A10A]", "B", None),
        ("[A10A]", None, None),
        ("[145]", "A", None),
        ("", None, None),
    ],
)
def test_box_ids_are_told_apart_from_internal_ids(raw, page, expected):
    assert box_id(raw, page) == expected


@pytest.mark.parametrize(
    ("name", "label"),
    [
        ("AmountOfLoan", "Amount of loan"),
        ("CFCTaxCalculation", "CFC tax calculation"),
        ("PayableRDEC", "Payable RDEC"),
        ("@ReturnType", "Return type"),
        ("Step3RestrictionCarriedForwardToNextAP", "Step 3 restriction carried forward to next AP"),
    ],
)
def test_humanise(name, label):
    assert humanise(name) == label


def test_cut_off_rows_are_consumed_in_schema_order_and_exact_rows_win():
    group = "/IRenvelope/CompanyTaxReturn/CompanyTaxCalculation/CorporationTaxChargeable"
    cut_off = f"{group}/AssociatedC"
    rows = [
        BoxRow(f"{group}/Exact", "[1]", "Exact"),
        BoxRow(cut_off, "[2]", "First"),
        BoxRow(cut_off, "[3]", "Second"),
    ]
    first, second = f"{group}/AssociatedCompanies", f"{group}/AssociatedCharges"
    box_map = BoxMap(rows, {f"{group}/Exact", first, second})

    assert box_map.match([f"{group}/Exact"]) == rows[0]
    assert box_map.match([first]) == rows[1]
    assert box_map.match([second]) == rows[2]
    assert box_map.match([first + "/Child"]) is None


XSD_TEMPLATE = """<?xml version="1.0"?>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:ct="urn:ct" targetNamespace="urn:ct">
  <xsd:element name="IRenvelope">
    <xsd:complexType>
      <xsd:sequence>{content}</xsd:sequence>
    </xsd:complexType>
  </xsd:element>
</xsd:schema>
"""


def write_schema(tmp_path: Path, content: str) -> Path:
    xsd = tmp_path / "schema.xsd"
    xsd.write_text(XSD_TEMPLATE.format(content=content), encoding="utf-8")
    box_map = tmp_path / "box-map.tsv"
    box_map.write_text("box_id\tpath\tcardinality\tdescription\n", encoding="utf-8")
    return xsd


def test_generator_fails_fast_on_facets_it_does_not_understand(tmp_path: Path):
    xsd = write_schema(
        tmp_path,
        """<xsd:element name="Amount"><xsd:simpleType><xsd:restriction base="xsd:decimal">
             <xsd:totalDigits value="5"/></xsd:restriction></xsd:simpleType></xsd:element>""",
    )

    with pytest.raises(SchemaError, match="Unsupported facet xsd:totalDigits"):
        generate(xsd, tmp_path / "box-map.tsv")


def test_generator_fails_fast_on_repeating_choices(tmp_path: Path):
    xsd = write_schema(
        tmp_path,
        """<xsd:choice maxOccurs="2"><xsd:element name="A" type="xsd:string"/>
             <xsd:element name="B" type="xsd:string"/></xsd:choice>""",
    )

    with pytest.raises(SchemaError, match="repeating choices"):
        generate(xsd, tmp_path / "box-map.tsv")
