"""Demonstration filing: accept a declared return and issue a receipt.

Nothing is sent to HMRC. Submitting to HMRC requires recognition as Corporation Tax
software and Government Gateway credentials, which this open-source project does not hold.
The receipt mirrors what HMRC's service returned: a submission reference and a
fingerprint of exactly what was declared, which the company can keep for its records.
"""

import base64
import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime

from open_ct600.ct600 import CompanyDetails, ReturnComputation, Submission, compute_return
from open_ct600.ids import new_id


@dataclass(frozen=True)
class SubmissionReceipt:
    """Acknowledgement of a submitted return.

    Attributes:
        reference: Unique submission reference.
        received_at: When the submission was accepted (UTC).
        fingerprint: Base32 SHA-256 digest of the submitted return and declaration.
        company: The company the return is for.
        signatory: Name of the person who made the declaration.
        computation: The computed return that was submitted.
    """

    reference: str
    received_at: datetime
    fingerprint: str
    company: CompanyDetails
    signatory: str
    computation: ReturnComputation


def fingerprint(submission: Submission) -> str:
    """Return a stable digest of a submission, so a copy can be checked against it later."""
    digest = hashlib.sha256(submission.model_dump_json().encode()).digest()
    return base64.b32encode(digest[:20]).decode()


def submit_return(submission: Submission) -> SubmissionReceipt:
    """Compute a declared return and issue a receipt for it."""
    return SubmissionReceipt(
        reference=new_id("sub"),
        received_at=datetime.now(UTC),
        fingerprint=fingerprint(submission),
        company=submission.ct600.company,
        signatory=submission.declaration.name,
        computation=compute_return(submission.ct600),
    )
