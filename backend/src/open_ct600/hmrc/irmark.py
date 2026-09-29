"""IRmark: HMRC's digest of a GovTalk message body, carried in the return and quoted on receipts.

The algorithm follows HMRC's "IRmark Generation Step By Step Guide for Gateway Protocol services"
(v2.0) and reproduces HMRC's worked example byte for byte:

1. Take the GovTalk ``Body`` element with the namespace declarations it inherits.
2. Remove ``IRenvelope/IRheader/IRmark``, keeping the whitespace either side of it.
3. Canonicalise with inclusive C14N 1.0 **with comments**. HMRC's signed receipts name that
   transform (``REC-xml-c14n-20010315#WithComments``), and TPVS rejects a message whose body
   holds comments when the IRmark was computed without them (error 2021).
4. SHA-1 the canonical bytes. The Base64 form goes in the return; HMRC prints the Base32 form on
   receipts.
"""

import base64
import hashlib
from dataclasses import dataclass

from lxml import etree

from open_ct600.hmrc.xmldoc import GOVTALK_NS, parse_xml, serialise

_IRMARK_ELEMENTS = etree.XPath(
    "./*[local-name()='IRenvelope']/*[local-name()='IRheader']/*[local-name()='IRmark']"
)


class IRmarkError(ValueError):
    """A message that cannot carry an IRmark."""


@dataclass(frozen=True)
class IRmark:
    """An IRmark in both of HMRC's encodings.

    Attributes:
        base64: 28-character Base64 SHA-1 digest, as written in ``IRheader/IRmark``.
        base32: 32-character Base32 form of the same digest, as HMRC quotes it on receipts.
    """

    base64: str
    base32: str


def canonical_body(message: bytes) -> bytes:
    """Return the exact bytes HMRC hashes for a GovTalk message's IRmark.

    Args:
        message: A serialised GovTalk message.

    Returns:
        The inclusive C14N 1.0 (with comments) form of ``Body`` without its IRmark element.

    Raises:
        IRmarkError: If the message has no GovTalk ``Body``.
        MalformedXMLError: If the message is not well-formed XML.
    """
    body = _body(parse_xml(message))
    for element in _IRMARK_ELEMENTS(body):
        _remove_keeping_whitespace(element)
    return etree.tostring(body, method="c14n", exclusive=False, with_comments=True)


def compute_irmark(message: bytes) -> IRmark:
    """Compute the IRmark of a GovTalk message, ignoring any IRmark it already carries.

    Args:
        message: A serialised GovTalk message.

    Returns:
        The IRmark in Base64 and Base32.
    """
    digest = hashlib.sha1(canonical_body(message), usedforsecurity=False).digest()
    return IRmark(
        base64=base64.b64encode(digest).decode("ascii"),
        base32=base64.b32encode(digest).decode("ascii"),
    )


def add_irmark(message: bytes) -> tuple[bytes, IRmark]:
    """Fill in the IRmark of a GovTalk message.

    Args:
        message: A serialised GovTalk message whose ``IRenvelope/IRheader`` holds exactly one
            ``IRmark`` element (its content is replaced).

    Returns:
        The re-serialised message carrying its IRmark, and the IRmark.

    Raises:
        IRmarkError: If the message has no GovTalk ``Body`` or not exactly one IRmark element.
    """
    irmark = compute_irmark(message)
    root = parse_xml(message)
    elements = _IRMARK_ELEMENTS(_body(root))
    if len(elements) != 1:
        raise IRmarkError(
            f"Expected one IRenvelope/IRheader/IRmark element to fill in, found {len(elements)}. "
            'Add <IRmark Type="generic"/> to the IRheader before computing the IRmark.'
        )
    elements[0].text = irmark.base64
    return serialise(root), irmark


def _body(root: etree._Element) -> etree._Element:
    body = root.find(f"{{{GOVTALK_NS}}}Body")
    if body is None:
        raise IRmarkError(
            f"No {{{GOVTALK_NS}}}Body element under the root {root.tag!r}; "
            "an IRmark can only be computed for a GovTalk message."
        )
    return body


def _remove_keeping_whitespace(element: etree._Element) -> None:
    """Remove ``element``, moving its tail text onto whatever precedes it."""
    parent = element.getparent()
    if parent is None:
        raise IRmarkError("The IRmark element has no parent to remove it from.")
    tail = element.tail or ""
    previous = element.getprevious()
    if previous is None:
        parent.text = (parent.text or "") + tail
    else:
        previous.tail = (previous.tail or "") + tail
    parent.remove(element)
