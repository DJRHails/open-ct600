from decimal import Decimal
from pathlib import Path

import pytest
from lxml import etree, isoschematron
from pydantic import SecretStr
from test_hmrc_xml import RELIEF_SHAPES, SHAPES, build, make_return

from open_ct600.hmrc.govtalk import (
    Environment,
    GatewayCredentials,
    Vendor,
    build_delete,
    build_poll,
    build_submission,
)
from open_ct600.hmrc.validate import (
    ARTEFACTS,
    Problem,
    _as_message,
    _envelope_schema,
    _rules,
    validate_return,
)
from open_ct600.hmrc.xmldoc import CT_NS, GOVTALK_NS, parse_xml

REPO = Path(__file__).resolve().parents[2]
SAMPLES = REPO / "specs/hmrc/samples"
XHTML = b'<html xmlns="http://www.w3.org/1999/xhtml"><body><p>accounts</p></body></html>'


def sample(name="CT600-Sample-No-attachments.xml", edits=()):
    content = (SAMPLES / name).read_bytes()
    for old, new in edits:
        assert old in content, old
        content = content.replace(old, new)
    return parse_xml(content)


def envelope_of(message):
    return message.find(f"{{{GOVTALK_NS}}}Body/{{{CT_NS}}}IRenvelope")


def codes(problems):
    return sorted(problem.code for problem in problems)


@pytest.mark.parametrize(
    ("name", "placeholder"),
    [
        ("CT600-Sample-No-attachments.xml", None),
        (
            "CT600-Sample-for-inserting-iXBRL-accounts-attachments.xml",
            b"<!--  Place your iXBRL accounts here -->",
        ),
        (
            "CT600-Sample-for-inserting-iXBRL-computations-attachments.xml",
            b"<!--  Place your iXBRL comps here -->",
        ),
    ],
)
def test_hmrc_samples_are_valid(name, placeholder):
    message = sample(name, edits=[(placeholder, XHTML)] if placeholder else [])

    assert validate_return(message) == []
    assert validate_return(envelope_of(message)) == []


def test_generated_messages_are_valid_govtalk():
    envelope = envelope_of(sample())
    vendor = Vendor(vendor_id="0000", product="open-ct600", version="0.1.0")
    credentials = GatewayCredentials(user_id="user", password=SecretStr("password"))
    submission, _ = build_submission(
        envelope, environment=Environment.LIVE, vendor=vendor, credentials=credentials
    )

    assert validate_return(parse_xml(submission)) == []
    for follow_up in (build_poll, build_delete):
        content = follow_up("46DCD4CC7E194088B99857931C185829", Environment.LIVE)
        assert _envelope_schema().validate(etree.ElementTree(parse_xml(content)))


def test_business_rule_box_475_required_when_440_positive():
    message = sample(
        edits=[(b"<NetCorporationTaxLiability>19000.00</NetCorporationTaxLiability>", b"")]
    )

    problems = validate_return(message)

    assert (
        Problem(
            code=9319,
            message="Box 475 must be completed if Box 440 is greater than 0 (zero)",
            box=None,
            path="/IRenvelope/CompanyTaxReturn",
        )
        in problems
    )


def test_tax_rate_rule_matches_what_tpvs_reported():
    # TPVS answered this return (HMRC's sample with company type 0 and a made-up rate) with 9200.
    message = sample(
        edits=[
            (b"<CompanyType>6</CompanyType>", b"<CompanyType>0</CompanyType>"),
            (b"<TaxRate>19.00</TaxRate>", b"<TaxRate>18.00</TaxRate>"),
        ]
    )

    problems = validate_return(message)

    assert 9200 in codes(problems)
    rate = next(problem for problem in problems if problem.code == 9200)
    assert rate.path == (
        "/IRenvelope/CompanyTaxReturn/CompanyTaxCalculation/CorporationTaxChargeable"
        "/FinancialYearOne/Details/TaxRate"
    )


GOVTALK_KEY = b'\n\t\t\t<Key Type="UTR">8596148860</Key>'
IRHEADER_KEY = b'\t\t\t\t\t<Key Type="UTR">8596148860</Key>'


def test_govtalk_keys_must_match_the_irheader():
    message = sample(edits=[(GOVTALK_KEY, b'<Key Type="UTR">1111111111</Key>')])

    assert codes(validate_return(message)) == [5005]


def test_utr_must_match_box_3():
    message = sample(
        edits=[(b"<Reference>8596148860</Reference>", b"<Reference>1234567890</Reference>")]
    )

    problem = next(p for p in validate_return(message) if p.code == 9100)
    assert problem.box == "3"
    assert problem.path == "/IRenvelope/CompanyTaxReturn/CompanyInformation/Reference"


@pytest.mark.parametrize(
    ("old", "new", "code", "box"),
    [
        (b"<CompanyType>6</CompanyType>", b"<CompanyType>12</CompanyType>", 4083, "4"),
        (b"<RegistrationNumber>12345678", b"<RegistrationNumber>ab", 4085, "2"),
        (b"<Name>Test</Name>", b"", 4065, "985"),
        (b"<Total>100000.00</Total>", b"<Total>lots</Total>", 4020, "145"),
        (b'ReturnType="new"', b'ReturnType="old"', 4080, None),
        (b"<TaxRate>19.00</TaxRate>", b"<TaxRate>101.00</TaxRate>", 4083, "340"),
        (b"<Declaration>", b"<Declaration><Bogus/>", 4065, None),
    ],
)
def test_schema_errors_carry_hmrc_codes_and_boxes(old, new, code, box):
    problems = validate_return(envelope_of(sample(edits=[(old, new)])))

    assert [(problem.code, problem.box) for problem in problems][:1] == [(code, box)]
    assert all("{http" not in problem.message for problem in problems)


def test_schema_errors_skip_business_rules():
    message = sample(
        edits=[
            (b"<CompanyType>6</CompanyType>", b"<CompanyType>12</CompanyType>"),
            (b"<NetCorporationTaxLiability>19000.00</NetCorporationTaxLiability>", b""),
        ]
    )

    assert codes(validate_return(message)) == [4083]


def test_repeated_elements_are_indexed_in_paths():
    message = sample(edits=[(IRHEADER_KEY, IRHEADER_KEY + b'<Key Type="UTR">1111111111</Key>')])

    paths = {problem.path for problem in validate_return(message) if problem.code == 5005}
    assert paths == {"/IRenvelope/IRheader/Keys/Key[2]"}


def test_rejects_other_documents():
    with pytest.raises(ValueError, match="IRenvelope or GovTalkMessage"):
        validate_return(parse_xml(b"<html/>"))


def test_packaged_artefacts_match_the_published_specs():
    published = {
        "CT-2014-v1-994.xsd": "ct600-v1.994/CT-2014-v1-994.xsd",
        "CT-2014-v1-994.sch": "ct600-v1.994/CT-2014-v1-994.sch",
        "envelope-v2-0-HMRC.xsd": "ct600-v1.994/envelope-v2-0-HMRC.xsd",
        "xmldsig-core-schema.xsd": "ct600-v1.994/xmldsig-core-schema.xsd",
    }

    assert sorted(path.name for path in ARTEFACTS.iterdir()) == sorted(published)
    for packaged, spec in published.items():
        assert (ARTEFACTS / packaged).read_bytes() == (REPO / "specs/hmrc" / spec).read_bytes()


def full_iso_schematron():
    """HMRC's schematron compiled by the plain ISO skeleton, walking the whole document."""
    schematron = etree.parse(str(ARTEFACTS / "CT-2014-v1-994.sch"))
    namespace = "{http://purl.oclc.org/dsdl/schematron}"
    for block in schematron.getroot().findall(f"{namespace}diagnostics"):
        schematron.getroot().remove(block)
    return etree.XSLT(isoschematron.iso_svrl_for_xslt1(schematron))


def failed_asserts(stylesheet, message):
    report = stylesheet(etree.ElementTree(message))
    return sorted(
        (failure.get("id"), failure.get("location"))
        for failure in report.getroot().iter("{http://purl.oclc.org/dsdl/svrl}failed-assert")
    )


def scrambled(envelope):
    """Every amount off by one, so HMRC's arithmetic rules fail all over the return."""
    for element in envelope.iter():
        if element.text and element.text.replace(".", "", 1).isdigit() and len(element) == 0:
            element.text = str(Decimal(element.text) + 1)
    return envelope


def test_pruned_schematron_reports_exactly_what_the_full_schematron_reports():
    full = full_iso_schematron()
    envelopes = [
        build(make_return(**overrides)) for overrides in [*SHAPES.values(), *RELIEF_SHAPES.values()]
    ]
    messages = [_as_message(scrambled(envelope)) for envelope in envelopes]
    messages.append(sample(edits=[(GOVTALK_KEY, b'<Key Type="UTR">1111111111</Key>')]))
    compared = 0

    for message in messages:
        expected = failed_asserts(full, message)
        assert failed_asserts(_rules().stylesheet, message) == expected
        compared += len(expected)

    assert compared > 200
