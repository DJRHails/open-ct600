"""Bank details for a repayment (CT600 boxes 920 to 940).

HMRC's schema makes boxes 920 to 935 required only inside ``BankAccountDetails``, and its
business rules never require the group. The Company Tax Return guide does: payable R&D and
creative credits are paid only into the account given there ("you need to enter account
details"), and a repayment of £100 or less is held against later periods without them. So the
service asks for them whenever the computed return shows money due back.
"""

import pytest
from answers import BANK_DETAILS
from lxml import etree
from pydantic import ValidationError
from test_api import client_for
from test_hmrc_xml import NS, RELIEF_SHAPES, build, make_return, text

from open_ct600.ct600 import CT600Return
from open_ct600.hmrc.validate import validate_return
from open_ct600.repayment import BankDetails

# The ERIS shape without the bank details test_hmrc_xml gives it.
ERIS_PAYABLE_CREDIT = {
    section: answers
    for section, answers in RELIEF_SHAPES["ERIS payable credit (CT600L)"].items()
    if section != "repayment"
}
# A theatre production's payable credit (box 885), as in test_pages' worked example.
CREATIVE_PAYABLE_CREDIT = {
    "period": {"start": "2025-04-01", "end": "2026-03-31"},
    "accounts": {"approval_date": "2026-06-01"},
    "supplementary_pages": {
        "P": {
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
    },
    "creative_industries": {"additional_information_submitted": True},
}
BANK = BANK_DETAILS
DETAILS = "//ct:OverpaymentsAndRepayments/ct:BankAccountDetails"


def problems_of(**overrides) -> dict[tuple, str]:
    with pytest.raises(ValidationError) as caught:
        make_return(**overrides)
    return {error["loc"]: error["msg"] for error in caught.value.errors()}


class TestBankDetails:
    def test_reads_a_sort_code_and_account_number_as_people_write_them(self):
        details = BankDetails.model_validate(
            {**BANK, "sort_code": "30 94-30", "account_number": "0073 3445"}
        )

        assert details.sort_code == "309430"
        assert details.account_number == "00733445"
        assert details.building_society_reference is None

    @pytest.mark.parametrize(
        ("field", "value", "message"),
        [
            ("bank_name", "", "Enter the name of the bank or building society"),
            ("bank_name", "B", "Name of the bank or building society must be 2 characters or more"),
            (
                "bank_name",
                "B" * 57,
                "Name of the bank or building society must be 56 characters or fewer",
            ),
            (
                "bank_name",
                "Bank £ Co",
                "Name of the bank or building society must only include letters a to z, numbers, "
                "spaces and these characters: , . ( ) / & ' - \" ! % * _ + : @ < > ? = ;",
            ),
            ("sort_code", "", "Enter a sort code"),
            ("sort_code", "30-94", "Sort code must be 6 digits long"),
            ("sort_code", "30-94-3O", "Enter a valid sort code like 309430"),
            ("account_number", "", "Enter an account number"),
            (
                "account_number",
                "7334450",
                "Account number must be 8 digits long. If yours is 6 or 7 digits, add zeros to "
                "the start",
            ),
            ("account_number", "0073344S", "Enter a valid account number like 00733445"),
            ("account_name", " ", "Enter the name on the account"),
            ("account_name", "A" * 29, "Name on the account must be 28 characters or fewer"),
            (
                "building_society_reference",
                "R" * 19,
                "Building society roll number must be 18 characters or fewer",
            ),
        ],
    )
    def test_explains_details_hmrc_would_refuse(self, field, value, message):
        with pytest.raises(ValidationError) as caught:
            BankDetails.model_validate({**BANK, field: value})

        # The API's users see the message without pydantic's prefix (frontend ``toProblems``).
        assert [
            (error["loc"], error["msg"].removeprefix("Value error, "))
            for error in caught.value.errors()
        ] == [((field,), message)]

    def test_reads_a_sort_code_written_with_en_dashes(self):
        details = BankDetails.model_validate({**BANK, "sort_code": "30\u201394\u201330"})

        assert details.sort_code == "309430"

    def test_leaves_out_a_blank_building_society_roll_number(self):
        details = BankDetails.model_validate({**BANK, "building_society_reference": "  "})

        assert details.building_society_reference is None


class TestWhenTheyAreNeeded:
    @pytest.mark.parametrize(
        "shape",
        [ERIS_PAYABLE_CREDIT, CREATIVE_PAYABLE_CREDIT],
        ids=["ERIS payable credit", "creative payable credit"],
    )
    def test_a_payable_credit_needs_bank_details(self, shape):
        assert problems_of(**shape) == {
            ("repayment",): (
                "Enter the bank details for HMRC to pay the money due back to the company into: "
                "HMRC pays payable credits and repayments only into the account given on the "
                "return (boxes 920 to 940)"
            )
        }

    def test_a_return_with_nothing_due_back_does_not(self):
        assert make_return().repayment is None

    def test_bank_details_are_kept_when_nothing_is_due_back(self):
        envelope = build(make_return(repayment=BANK))

        assert text(envelope, f"{DETAILS}/ct:BankName") == "Synthetic Bank plc"
        assert validate_return(envelope) == []


class TestTheReturn:
    def test_writes_boxes_920_to_940_in_schema_order_and_passes_hmrc_checks(self):
        ct600 = make_return(
            **ERIS_PAYABLE_CREDIT,
            repayment={**BANK, "building_society_reference": "ROLL/123-4"},
        )

        envelope = build(ct600)

        (details,) = envelope.xpath(DETAILS, namespaces=NS)
        assert [(etree.QName(child).localname, child.text) for child in details] == [
            ("BankName", "Synthetic Bank plc"),
            ("SortCode", "000000"),
            ("AccountNumber", "00000000"),
            ("AccountName", "Acme Widgets Ltd"),
            ("BuildingSocReference", "ROLL/123-4"),
        ]
        assert text(envelope, "//ct:RepaymentsForThePeriodCoveredByThisReturn/ct:RandDTaxCredit")
        assert validate_return(envelope) == []

    def test_hmrc_rules_alone_would_accept_the_return_without_them(self):
        """Only the service's check stops a payable credit being filed with no account."""
        envelope = build(make_return(**ERIS_PAYABLE_CREDIT, repayment=BANK))
        (details,) = envelope.xpath(DETAILS, namespaces=NS)
        details.getparent().remove(details)

        assert validate_return(envelope) == []


def test_the_api_links_missing_bank_details_to_the_repayment_answers():
    ct600 = make_return(**ERIS_PAYABLE_CREDIT, repayment=BANK).model_dump(mode="json")
    del ct600["repayment"]
    with client_for() as client:
        response = client.post("/api/returns/compute", json=ct600)

    assert response.status_code == 422
    (problem,) = response.json()["detail"]
    assert problem["loc"] == ["body", "repayment"]


def test_repayment_is_optional_on_the_model():
    assert "repayment" in CT600Return.model_fields
    assert not CT600Return.model_fields["repayment"].is_required()
