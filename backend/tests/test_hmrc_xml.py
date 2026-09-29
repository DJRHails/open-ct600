"""CT600 XML for returns of each shape, checked with HMRC's XSD and schematron."""

import base64
from dataclasses import replace
from decimal import Decimal

import pytest
from lxml import etree

from open_ct600.ct600 import CT600Box, CT600Return, Declaration, compute_return
from open_ct600.hmrc.validate import validate_return
from open_ct600.hmrc.xml import ReturnXMLError, build_return_xml
from open_ct600.hmrc.xmldoc import CT_NS

ACCOUNTS = '<html xmlns="http://www.w3.org/1999/xhtml"><body><p>Accounts</p></body></html>'
COMPUTATIONS = '<html xmlns="http://www.w3.org/1999/xhtml"><body><p>Tax</p></body></html>'
DECLARATION = Declaration(name="Ada Lovelace", capacity="director", confirmed=True)
NS = {"ct": CT_NS}


def make_return(**overrides) -> CT600Return:
    answers = {
        "company": {
            "name": "Acme Widgets Ltd",
            "registration_number": "01234567",
            "utr": "1234567890",
            "principal_activity": "Manufacture of widgets",
        },
        "period": {"start": "2024-04-01", "end": "2025-03-31"},
        "profit_and_loss": {
            "turnover": 120_000,
            "interest_income": 500,
            "cost_of_sales": 20_000,
            "staff_costs": 30_000,
            "depreciation": 2_000,
            "other_expenses": 8_000,
        },
        "tax_adjustments": {
            "disallowable_expenses": 1_000,
            "capital_allowances": 5_000,
            "losses_brought_forward": 3_000,
            "qualifying_donations": 500,
        },
        "balance_sheet": {"current_assets": 70_000, "called_up_share_capital": 100},
        "accounts": {
            "standard": "micro",
            "approval_date": "2025-06-30",
            "directors": ["Ada Lovelace"],
            "signing_director": "Ada Lovelace",
            "average_employees": 2,
            "trading_status": "trading",
        },
    }
    for section, values in overrides.items():
        current = answers.get(section)
        answers[section] = {**current, **values} if isinstance(current, dict) else values
    return CT600Return.model_validate(answers)


def build(ct600, *, declaration=DECLARATION, documents=True):
    return build_return_xml(
        ct600,
        compute_return(ct600),
        declaration=declaration,
        accounts_xhtml=ACCOUNTS if documents else None,
        computations_xhtml=COMPUTATIONS if documents else None,
    )


def text(envelope, path):
    return envelope.xpath(f"string({path})", namespaces=NS)


ROYALTY = {
    "RecipientName": "Babbage Engines GmbH",
    "AddressOfRecipient": {"Line": ["1 Hauptstrasse", "Berlin"]},
    "PaymentType": "Royalty",
    "Amount": "1000",
    "RoyaltiesAgreement": {"DoubleTaxationAgreement": "UK/Germany"},
    "DeductionRate": "5",
}

SHAPES = {
    "marginal relief": {},
    "small profits rate": {"profit_and_loss": {"turnover": 60_000}},
    "main rate": {"profit_and_loss": {"turnover": 600_000}},
    "trading loss": {"profit_and_loss": {"turnover": 10_000}},
    "nil profits": {
        "profit_and_loss": {"turnover": 0, "interest_income": 0},
        "tax_adjustments": {"disallowable_expenses": 0, "qualifying_donations": 0},
    },
    "associated companies": {"tax_adjustments": {"associated_companies": 2}},
    "straddles 1 April 2023": {
        "period": {"start": "2022-10-01", "end": "2023-09-30"},
        "accounts": {"approval_date": "2023-12-01"},
    },
    "flat 19% before April 2023": {
        "period": {"start": "2021-04-01", "end": "2022-03-31"},
        "accounts": {"approval_date": "2022-06-01"},
    },
    "short period": {
        "period": {"start": "2024-10-01", "end": "2025-03-31"},
    },
    "small company accounts": {"accounts": {"standard": "small"}},
    "members' club": {"company": {"company_type": 6}},
    "tax avoidance scheme (CT600J)": {
        "supplementary_pages": {
            "J": {
                "AvoidanceSchemes": [
                    {"ReferenceNumber": "12345678", "AccountingPeriod": "2025-03-31"}
                ]
            }
        }
    },
    "cross-border royalties (CT600H)": {"supplementary_pages": {"H": {"Royalties": [ROYALTY]}}},
}

RD_FORMS = {"claimed_in_previous_three_years": True, "additional_information_submitted": True}
PAYE_REFERENCE = [{"HMRCofficeNumber": "123", "EmployerPAYEreference": "AB12345"}]
LOSS_MAKING = {"profit_and_loss": {"turnover": 10_000}}
SME_PAYE = {
    "SME": {
        "PAYENICforWhichTheCompanyIsLiableInThisAccountingPeriod": "10000",
        "EmployerPAYEreference": PAYE_REFERENCE,
    }
}
AUTHORISED = {
    "AuthorisationForSimplifiedArrangements": {
        "AuthorisationWhereSimplifiedArrangement": "yes",
        "CompanyName": "Parent Ltd",
        "NameOfAuthorisedPerson": "Ada Lovelace",
        "Status": "Director",
    }
}
SHIP = {
    "Name": "Northern Star",
    "IMOnumber": "9123456",
    "InterestInShip": "O",
    "GrossTonnage": "45000",
    "NetTonnage": "30099",
    "NumberDays": "365",
    "Flagged": "yes",
    "FirstTime": "no",
}
ADDRESS = {"Line": ["1 Dock Road", "Tilbury"]}
CREATIVES_FORM = {"creative_industries": {"additional_information_submitted": True}}

RELIEF_SHAPES = {
    "merged RDEC, profit-making (CT600L)": {
        "research_and_development": {
            **RD_FORMS,
            "scheme": "rdec",
            "qualifying_expenditure": 50_000,
        },
        "supplementary_pages": {"L": {}},
    },
    "merged RDEC, loss-making to step 7 (CT600L)": {
        **LOSS_MAKING,
        "research_and_development": {
            **RD_FORMS,
            "scheme": "rdec",
            "qualifying_expenditure": 50_000,
            "company_is_sme": True,
        },
        "supplementary_pages": {
            "L": {
                "Step3": {
                    "PAYENICsForWhichTheCompanyIsLiableInThisAP": "30000",
                    "EmployerPAYEreference": PAYE_REFERENCE,
                }
            }
        },
    },
    "ERIS payable credit (CT600L)": {
        **LOSS_MAKING,
        "research_and_development": {
            **RD_FORMS,
            "scheme": "eris",
            "qualifying_expenditure": 50_000,
            "intensity": "35",
            "claim_payable_credit": True,
        },
        "supplementary_pages": {"L": SME_PAYE},
    },
    "ERIS additional deduction only": {
        **LOSS_MAKING,
        "research_and_development": {
            **RD_FORMS,
            "scheme": "eris",
            "qualifying_expenditure": 50_000,
            "intensity": "35",
        },
    },
    "SME scheme before April 2024 (CT600L)": {
        "period": {"start": "2023-04-01", "end": "2024-03-31"},
        "accounts": {"approval_date": "2024-06-01"},
        **LOSS_MAKING,
        "research_and_development": {
            **RD_FORMS,
            "scheme": "sme",
            "qualifying_expenditure": 50_000,
            "intensity": "45",
            "claim_payable_credit": True,
        },
        "supplementary_pages": {"L": SME_PAYE},
    },
    "large-company RDEC straddling April 2023 (CT600L)": {
        "period": {"start": "2023-01-01", "end": "2023-12-31"},
        "accounts": {"approval_date": "2024-06-01"},
        **LOSS_MAKING,
        "research_and_development": {
            **RD_FORMS,
            "scheme": "rdec",
            "qualifying_expenditure": 50_000,
            "rd_workers_paye_and_nic": 5_000,
        },
        "supplementary_pages": {"L": {}},
    },
    "RDEC brought forward only (CT600L)": {
        "supplementary_pages": {
            "L": {"PreStep1Restriction": {"Step2RestrictionBroughtForward": "5000.00"}}
        }
    },
    "loans to participators with relief (CT600A)": {
        "supplementary_pages": {
            "A": {
                "BeforeEndPeriod": "no",
                "LoansInformation": {"Loan": [{"Name": "J Smith", "AmountOfLoan": "40000"}]},
                "ReliefEarlierThan": {
                    "Loan": [{"Name": "J Smith", "AmountRepaid": "15000", "Date": "2025-06-30"}]
                },
            }
        }
    },
    "loans to participators repaid in full (CT600A)": {
        "supplementary_pages": {
            "A": {
                "BeforeEndPeriod": "no",
                "LoansInformation": {"Loan": [{"Name": "J Smith", "AmountOfLoan": "6000"}]},
                "ReliefEarlierThan": {
                    "Loan": [{"Name": "J Smith", "AmountRepaid": "6000", "Date": "2025-06-30"}]
                },
            }
        }
    },
    "loans either side of 6 April 2022 (CT600A)": {
        "period": {"start": "2022-01-01", "end": "2022-12-31"},
        "accounts": {"approval_date": "2023-06-01"},
        "supplementary_pages": {
            "A": {
                "BeforeEndPeriod": "no",
                "LoansInformation": {
                    "Loan": [
                        {"Name": "J Smith", "AmountOfLoan": "10000"},
                        {"Name": "A Jones", "AmountOfLoan": "10000"},
                    ]
                },
            }
        },
        "participator_loan_dates": {"loans": ["2022-02-01", "2022-07-01"]},
    },
    "group relief claims (CT600C)": {
        "supplementary_pages": {
            "C": {
                "ClaimToGroupRelief": {
                    "CompanyInformation": {
                        "Company": [
                            {
                                "Name": "Sub Ltd",
                                "AccountingPeriod": {"From": "2024-07-01", "To": "2025-06-30"},
                                "TaxReference": "1234567891",
                                "AmountClaimed": "10000",
                            }
                        ]
                    },
                    "ClaimAuthorisation": AUTHORISED,
                },
                "GroupReliefForCarriedForwardLosses": {
                    "CompanyInformation": {
                        "Company": [
                            {
                                "Name": "Sub Ltd",
                                "TaxReference": "1234567891",
                                "AmountClaimed": "5000",
                            }
                        ]
                    },
                    "ClaimAuthorisation": AUTHORISED,
                },
            }
        }
    },
    "group relief surrendered (CT600C)": {
        **LOSS_MAKING,
        "supplementary_pages": {
            "C": {
                "SurrenderedGroupRelief": {
                    "TradingLosses": "20000",
                    "SurrenderInformation": {
                        "Company": [
                            {
                                "Name": "Parent Ltd",
                                "TaxReference": "1234567891",
                                "AmountSurrendered": "20000",
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
        },
    },
    "controlled foreign companies (CT600B)": {
        "supplementary_pages": {
            "B": {
                "CompanyInformation": [
                    {
                        "Name": "Alpha Ltd",
                        "Territory": "Ruritania",
                        "CFCTaxCalculation": {
                            "Percentage": "60.00",
                            "ChargeableProfits": "1000000",
                            "CreditableTax": "48000.00",
                        },
                    },
                    {"Name": "Beta SA", "Territory": "Freedonia", "ExemptionDue": "Low Profits"},
                ]
            }
        }
    },
    "insurance (CT600D)": {"supplementary_pages": {"D": {"Declaration": "yes"}}},
    "charity, all income exempt (CT600E)": {
        "company": {"company_type": 8},
        "supplementary_pages": {
            "E": {
                "ClaimExemption": {
                    "Status": {
                        "ClaimingExemptionAllOrPart": "yes",
                        "AllCharitable": {"AllExempt": "yes"},
                    }
                },
                "InformationRequired": {
                    "Income": {"TotalTurnover": "120000", "GiftAid": "28000"},
                    "Expenditure": {"TradingCosts": "60000"},
                },
            }
        },
    },
    "tonnage tax (CT600F)": {
        "supplementary_pages": {
            "F": {
                "TonnageTax": {
                    "Information": {
                        "TrainingCertificate": "yes",
                        "CompanyMetCharteredInLimit": "yes",
                        "NotRegistered": "na",
                        "OffshoreActivities": "yes",
                    },
                    "OffshoreTrainingAllowance": {"OffsetAgainstCorpTax": "500.00"},
                    "QualifyingShips": {"Ship": [SHIP]},
                }
            }
        }
    },
    "ring fence supplementary charge (CT600I)": {
        "supplementary_pages": {
            "I": {
                "CalculationOfSupplementaryCharge": {
                    "Trade": {"Amount": "50000", "Profits": "yes"},
                    "DisallowedFinancingCosts": {"RelatedToCompany": "4000"},
                    "MinusLosses": "10000",
                    "FieldAllowance": "6000",
                },
            }
        }
    },
    "ring fence profits taxed at 30% (CT600I)": {
        "profit_and_loss": {"turnover": 100_000},
        "supplementary_pages": {
            "I": {
                "CalculationOfSupplementaryCharge": {
                    "Trade": {"Amount": "100000", "Profits": "yes"}
                }
            }
        },
    },
    "ring fence and other profits, two rates (CT600I)": {
        "profit_and_loss": {"turnover": 400_000, "interest_income": 60_000},
        "period": {"start": "2024-10-01", "end": "2025-09-30"},
        "accounts": {"approval_date": "2025-12-01"},
        "supplementary_pages": {
            "I": {
                "CalculationOfSupplementaryCharge": {
                    "Trade": {"Amount": "100000", "Profits": "yes"}
                }
            }
        },
    },
    "close investment-holding company": {
        "company": {"company_type": 2},
        "profit_and_loss": {"turnover": 60_000},
    },
    "trading loss with surrender for ERIS credit": {
        **LOSS_MAKING,
        "research_and_development": {
            **RD_FORMS,
            "scheme": "eris",
            "qualifying_expenditure": 50_000,
            "intensity": "35",
            "claim_payable_credit": True,
        },
        "supplementary_pages": {"L": SME_PAYE},
    },
    "restitution tax straddling 1 April (CT600K)": {
        "period": {"start": "2025-01-01", "end": "2025-12-31"},
        "accounts": {"approval_date": "2026-06-01"},
        "supplementary_pages": {"K": {"TaxCalculation": {"RestitutionInterest": "1000000"}}},
    },
    "freeports (CT600M)": {
        "tax_adjustments": {"capital_allowances": 50_000},
        "supplementary_pages": {
            "M": {
                "EnhancedSBAinFreeports": [
                    {
                        "LocationOfFreeport": "7",
                        "AddressOfBusinessOperation": ADDRESS,
                        "DateStructureOrBuildingWasBroughtIntoQualifyingUse": "2024-06-01",
                        "DateOfFirstContractForConstruction": "2023-06-01",
                        "TotalAmountOfQualifyingExpenditure": "120000",
                        "TotalSBAclaimAmount": "10000",
                    }
                ],
                "ECAforPlantAndMachineryInFreeports": [
                    {
                        "LocationOfFreeport": "7",
                        "AddressOfBusinessOperation": ADDRESS,
                        "TotalAmountOfECAclaimedWithinTheAccountingPeriod": "30000",
                    }
                ],
            }
        },
    },
    "residential property developer tax (CT600N)": {
        "supplementary_pages": {
            "N": {
                "Section4": {
                    "AdjustedProfit": "40000000",
                    "JointVentureProfit": "2000000",
                    "AllowableLossRelief": "5000000",
                    "AllowanceAllocationForAccountingPeriod": "25000000",
                }
            }
        }
    },
    "audio-visual expenditure credit (CT600P)": {
        **LOSS_MAKING,
        **CREATIVES_FORM,
        "supplementary_pages": {
            "P": {
                "AudioVisualExpenditureCredit": {
                    "HighEndTV": {
                        "RelevantGlobalExpenditure": "1000000",
                        "UKrelevantGlobalExpenditure": "900000",
                        "QualifyingExpenditure": "800000",
                        "ExpenditureCreditClaimed": "272000.00",
                    },
                    "Animation": {
                        "RelevantGlobalExpenditure": "100000",
                        "UKrelevantGlobalExpenditure": "90000",
                        "QualifyingExpenditure": "80000",
                        "ExpenditureCreditClaimed": "31200.00",
                    },
                }
            }
        },
    },
    "theatre tax relief (CT600P)": {
        **LOSS_MAKING,
        **CREATIVES_FORM,
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
    },
    "creative credits brought forward only (CT600P)": {
        **CREATIVES_FORM,
        "supplementary_pages": {
            "P": {"PreStep1Restriction": {"Step2RestrictionBroughtForward": "5000.00"}}
        },
    },
}


@pytest.mark.parametrize("overrides", RELIEF_SHAPES.values(), ids=RELIEF_SHAPES.keys())
def test_every_relief_and_page_is_accepted_by_hmrc_schema_and_rules(overrides):
    assert validate_return(build(make_return(**overrides))) == []


@pytest.mark.parametrize("overrides", SHAPES.values(), ids=SHAPES.keys())
def test_every_shape_is_accepted_by_hmrc_schema_and_rules(overrides):
    assert validate_return(build(make_return(**overrides))) == []


def test_chargeable_gains_are_accepted():
    ct600 = make_return(tax_adjustments={"chargeable_gains": 5_000})

    assert validate_return(build(ct600)) == []


def test_associated_companies_before_april_2023_are_accepted():
    ct600 = make_return(
        period={"start": "2021-04-01", "end": "2022-03-31"},
        accounts={"approval_date": "2022-06-01"},
        tax_adjustments={"associated_companies": 1},
    )

    assert validate_return(build(ct600)) == []


def test_loans_to_participators_page_is_accepted():
    loans = {
        "BeforeEndPeriod": "no",
        "LoansInformation": {"Loan": [{"Name": "Ada Lovelace", "AmountOfLoan": "6000"}]},
    }

    assert validate_return(build(make_return(supplementary_pages={"A": loans}))) == []


def test_boxes_are_placed_and_formatted_by_kind():
    envelope = build(make_return())
    calculation = "//ct:CompanyTaxReturn/ct:CompanyTaxCalculation"

    assert text(envelope, "//ct:Turnover/ct:Total") == "120000.00"
    assert text(envelope, f"{calculation}/ct:Income/ct:Trading/ct:Profits") == "58000.00"
    assert text(envelope, f"{calculation}/ct:ChargeableProfits") == "55000.00"
    details = f"{calculation}/ct:CorporationTaxChargeable/ct:FinancialYearOne"
    assert text(envelope, f"{details}/ct:Year") == "2024"
    assert text(envelope, f"{details}/ct:Details/ct:TaxRate") == "25.00"
    assert text(envelope, f"{details}/ct:Details/ct:Tax") == "13750.00"
    associated = f"{calculation}/ct:CorporationTaxChargeable/ct:AssociatedCompanies"
    assert text(envelope, f"{associated}/ct:ThisPeriod") == "0"
    assert text(envelope, f"{associated}/ct:StartingOrSmallCompaniesRate") == "yes"


def test_nil_optional_boxes_are_left_blank():
    envelope = build(make_return(profit_and_loss={"turnover": 600_000}))

    assert not envelope.xpath("//ct:MarginalReliefForRingFenceTrades", namespaces=NS)
    assert not envelope.xpath("//ct:StartingOrSmallCompaniesRate", namespaces=NS)
    assert not envelope.xpath("//ct:ChargeableGains", namespaces=NS)


def test_header_and_company_information():
    envelope = build(make_return())

    assert text(envelope, "/ct:IRenvelope/ct:IRheader/ct:Keys/ct:Key[@Type='UTR']") == "1234567890"
    assert text(envelope, "//ct:IRheader/ct:PeriodEnd") == "2025-03-31"
    assert text(envelope, "//ct:Manifest//ct:SchemaVersion") == "2025-v1.994"
    assert envelope.xpath("//ct:IRheader/ct:IRmark[@Type='generic']", namespaces=NS)
    assert text(envelope, "//ct:CompanyInformation/ct:Reference") == "1234567890"
    assert text(envelope, "//ct:CompanyInformation/ct:RegistrationNumber") == "01234567"
    assert text(envelope, "//ct:PeriodCovered/ct:From") == "2024-04-01"
    assert text(envelope, "//ct:CompanyTaxReturn/@ReturnType") == "new"


@pytest.mark.parametrize(
    ("capacity", "status"),
    [
        ("director", "Director"),
        ("company_secretary", "Company secretary"),
        ("authorised_agent", "Authorised agent"),
    ],
)
def test_declaration(capacity, status):
    declaration = Declaration(name="Grace Hopper", capacity=capacity, confirmed=True)
    envelope = build(make_return(), declaration=declaration)

    assert text(envelope, "//ct:Declaration/ct:AcceptDeclaration") == "yes"
    assert text(envelope, "//ct:Declaration/ct:Name") == "Grace Hopper"
    assert text(envelope, "//ct:Declaration/ct:Status") == status


def test_ixbrl_documents_are_attached_computations_first():
    envelope = build(make_return())

    documents = envelope.xpath(
        "//ct:AttachedFiles/ct:XBRLsubmission/*/ct:Instance/ct:EncodedInlineXBRLDocument",
        namespaces=NS,
    )
    assert [etree.QName(d.getparent().getparent()).localname for d in documents] == [
        "Computation",
        "Accounts",
    ]
    assert base64.b64decode(documents[0].text).decode() == COMPUTATIONS
    assert base64.b64decode(documents[1].text).decode() == ACCOUNTS
    assert [d.get("Filename") for d in documents] == ["computations.xhtml", "accounts.xhtml"]


def test_without_ixbrl_hmrc_rules_ask_for_accounts_and_computations():
    problems = validate_return(build(make_return(), documents=False))

    assert sorted(problem.code for problem in problems) == [9113, 9965]


def test_supplementary_page_is_flagged_and_serialised_in_schema_order():
    scheme = {"AccountingPeriod": "2025-03-31", "ReferenceNumber": "12345678"}
    envelope = build(make_return(supplementary_pages={"J": {"AvoidanceSchemes": [scheme]}}))

    assert text(envelope, "//ct:ReturnInfoSummary/ct:SupplementaryPages/ct:CT600J") == "yes"
    assert text(envelope, "//ct:ReturnInfoSummary/ct:RegisteredAvoidanceScheme") == "yes"
    schemes = envelope.xpath("//ct:TaxAvoidanceSchemes/ct:AvoidanceSchemes", namespaces=NS)
    assert [etree.QName(child).localname for child in schemes[0]] == [
        "ReferenceNumber",
        "AccountingPeriod",
    ]
    order = [
        etree.QName(child).localname for child in envelope.find(f"{{{CT_NS}}}CompanyTaxReturn")
    ]
    assert order.index("Declaration") < order.index("TaxAvoidanceSchemes")
    assert order.index("TaxAvoidanceSchemes") < order.index("AttachedFiles")


def test_page_values_are_written_in_xml_form():
    envelope = build(make_return(supplementary_pages={"H": {"Royalties": [ROYALTY]}}))

    royalties = "//ct:CrossBorderRoyalties/ct:Royalties"
    assert text(envelope, f"{royalties}/ct:Amount") == "1000.00"
    assert text(envelope, f"{royalties}/ct:DeductionRate") == "5.00"
    assert text(envelope, f"{royalties}/ct:DeductionAmount") == "50.00"
    assert len(envelope.xpath(f"{royalties}/ct:AddressOfRecipient/ct:Line", namespaces=NS)) == 2


def test_page_box_in_the_main_box_list_is_refused():
    ct600 = make_return()
    computation = compute_return(ct600)
    stray = CT600Box(box="A80", label="Tax chargeable", value=Decimal(1), kind="money")
    broken = replace(computation, boxes=(*computation.boxes, stray))

    with pytest.raises(ReturnXMLError, match="Box A80"):
        build_return_xml(
            ct600, broken, declaration=DECLARATION, accounts_xhtml=None, computations_xhtml=None
        )


def test_fractional_whole_pounds_are_refused():
    ct600 = make_return()
    computation = compute_return(ct600)
    boxes = tuple(
        replace(box, value=box.value + Decimal("0.5")) if box.box == "145" else box
        for box in computation.boxes
    )
    broken = replace(computation, boxes=boxes)

    with pytest.raises(ReturnXMLError, match="whole pounds"):
        build_return_xml(
            ct600, broken, declaration=DECLARATION, accounts_xhtml=None, computations_xhtml=None
        )


def test_a_loss_return_records_the_loss_and_is_accepted():
    ct600 = make_return(profit_and_loss={"turnover": 20_000})
    envelope = build(ct600)

    losses = "//ct:LossesDeficitsAndExcess/ct:AmountArising/ct:LossesOfTradesUK"
    assert text(envelope, f"{losses}/ct:Arising") == text(envelope, f"{losses}/ct:SurrenderMaximum")
    assert text(envelope, f"{losses}/ct:Arising") != ""
    assert validate_return(envelope) == []
