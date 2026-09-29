"""XML namespaces and the hardened parser shared by the HMRC modules."""

from lxml import etree

GOVTALK_NS = "http://www.govtalk.gov.uk/CM/envelope"
CT_NS = "http://www.govtalk.gov.uk/taxation/CT/5"
SUCCESS_RESPONSE_NS = "http://www.inlandrevenue.gov.uk/SuccessResponse"
ERROR_RESPONSE_NS = "http://www.govtalk.gov.uk/CM/errorresponse"
XMLDSIG_NS = "http://www.w3.org/2000/09/xmldsig#"


class MalformedXMLError(ValueError):
    """A document that is not well-formed XML."""


def parse_xml(content: bytes) -> etree._Element:
    """Parse an XML document without resolving entities or touching the network.

    ``huge_tree`` is on because a return carries its iXBRL accounts and computations as
    base64 text nodes, which can exceed libxml2's default 10 MB text-node limit (HMRC accepts
    up to 25 MB).

    Args:
        content: The serialised document.

    Returns:
        The root element.

    Raises:
        MalformedXMLError: If ``content`` is not well-formed XML.
    """
    parser = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)
    try:
        return etree.fromstring(content, parser)
    except etree.XMLSyntaxError as error:
        raise MalformedXMLError(f"Not well-formed XML: {error}") from error


def serialise(root: etree._Element) -> bytes:
    """Serialise a document as UTF-8 with an XML declaration and no added whitespace."""
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8")
