from pathlib import Path

import pytest

from open_ct600.hmrc.irmark import IRmarkError, add_irmark, canonical_body, compute_irmark
from open_ct600.hmrc.xmldoc import MalformedXMLError

REPO = Path(__file__).resolve().parents[2]
WORKED_EXAMPLE = REPO / "specs/hmrc/irmark"
FIXTURES = Path(__file__).parent / "fixtures/hmrc"


def test_reproduces_hmrc_worked_example_canonical_bytes():
    submission = (WORKED_EXAMPLE / "irmarkexample-submission.xml").read_bytes()
    expected = (WORKED_EXAMPLE / "irmarkexample-canonicalised.xml").read_bytes()

    assert canonical_body(submission) == expected


def test_reproduces_hmrc_worked_example_irmark():
    submission = (WORKED_EXAMPLE / "irmarkexample-submission.xml").read_bytes()

    irmark = compute_irmark(submission)

    assert irmark.base64 == "RPfWtxHeCZRcwfitnIJmK9xc4OQ="
    assert irmark.base32 == "IT35NNYR3YEZIXGB7CWZZATGFPOFZYHE"


@pytest.mark.parametrize(
    ("message", "accepted_digest"),
    [
        # HMRC's sample with a namespace declared on GovTalkMessage but unused in the Body.
        ("tpvs-accepted-sample.xml", "YrgW02ybxWOff7gHrELynhp1gRw="),
        # The same sample keeping its XML comments inside the Body.
        ("tpvs-accepted-sample-with-comments.xml", "ZNOrWz9xqFdEAr17jzhh6gFvBFI="),
    ],
)
def test_matches_irmarks_hmrc_tpvs_accepted(message, accepted_digest):
    assert compute_irmark((FIXTURES / message).read_bytes()).base64 == accepted_digest


def test_comments_in_the_body_are_hashed():
    with_comments = (FIXTURES / "tpvs-accepted-sample-with-comments.xml").read_bytes()
    body_comment = b"<!--  Will need to match the CH number in the accounts  -->"
    assert body_comment in with_comments
    edited_comment = with_comments.replace(body_comment, b"<!-- edited -->")

    assert compute_irmark(with_comments) != compute_irmark(edited_comment)


def test_add_irmark_fills_placeholder_and_is_stable():
    submission = (WORKED_EXAMPLE / "irmarkexample-submission.xml").read_bytes()
    placeholder = submission.replace(b"RPfWtxHeCZRcwfitnIJmK9xc4OQ=", b"placeholder")

    marked, irmark = add_irmark(placeholder)

    assert irmark.base64 == "RPfWtxHeCZRcwfitnIJmK9xc4OQ="
    assert b'<IRmark Type="generic">RPfWtxHeCZRcwfitnIJmK9xc4OQ=</IRmark>' in marked
    assert compute_irmark(marked) == irmark


def test_irmark_changes_when_the_body_changes():
    submission = (WORKED_EXAMPLE / "irmarkexample-submission.xml").read_bytes()
    edited = submission.replace(b"<Amount>250.00</Amount>", b"<Amount>251.00</Amount>", 1)

    assert compute_irmark(edited) != compute_irmark(submission)


def test_irmark_ignores_the_header():
    submission = (WORKED_EXAMPLE / "irmarkexample-submission.xml").read_bytes()
    edited = submission.replace(b"<SenderID>ctfuser001</SenderID>", b"<SenderID>x</SenderID>")

    assert compute_irmark(edited) == compute_irmark(submission)


def test_add_irmark_requires_a_placeholder():
    submission = (WORKED_EXAMPLE / "irmarkexample-submission.xml").read_bytes()
    irmark_element = b'<IRmark Type="generic">RPfWtxHeCZRcwfitnIJmK9xc4OQ=</IRmark>'
    without = submission.replace(irmark_element, b"")

    with pytest.raises(IRmarkError, match="found 0"):
        add_irmark(without)


def test_rejects_a_message_without_a_govtalk_body():
    with pytest.raises(IRmarkError, match="GovTalk message"):
        compute_irmark(b"<IRenvelope/>")


def test_rejects_malformed_xml():
    with pytest.raises(MalformedXMLError):
        compute_irmark(b"<GovTalkMessage>")
