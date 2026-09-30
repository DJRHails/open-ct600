"""The API fixtures match Companies House's own swagger specs (``specs/companies-house/api``).

The specs are from https://developer-specs.company-information.service.gov.uk: every object
must have its definition's required members and nothing it does not define, and enumerated
strings must be one of the listed values.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from companies_house_stub import API

from open_ct600.companies_house.sic import SIC_LIST, sic_description

SPECS = Path(__file__).resolve().parents[2] / "specs/companies-house"
UNDOCUMENTED = {("filingHistory.json", "filingHistoryItem"): {"description_values"}}
"""Members the API sends but its spec leaves out. ``description_values`` fills the placeholders
of a filing's ``description`` (``{made_up_date}`` in "accounts made up to {made_up_date}", see
Companies House's ``api-enumerations/filing_history_descriptions.yml``), which is how its own
register pages show each filing."""


def definitions(spec: str) -> dict[str, Any]:
    return json.loads((SPECS / "api" / spec).read_text())["definitions"]


def resolve(spec: str, reference: str) -> tuple[str, str]:
    """``(spec file, definition)`` for a swagger ``$ref``."""
    target, _, pointer = reference.partition("#/definitions/")
    return (target.rsplit("/", 1)[-1] or spec, pointer)


def schema_of(spec: str, name: str) -> tuple[set[str], set[str], dict[str, Any]]:
    """Required and allowed members, and member schemas, following ``allOf``."""
    definition = definitions(spec)[name]
    required = set(definition.get("required", []))
    properties = dict(definition.get("properties", {}))
    for parent in definition.get("allOf", []):
        parent_required, _, parent_properties = schema_of(*resolve(spec, parent["$ref"]))
        required |= parent_required
        properties |= parent_properties
    return required, set(properties) | UNDOCUMENTED.get((spec, name), set()), properties


def problems(spec: str, name: str, value: Any, path: str = "") -> list[str]:
    required, allowed, properties = schema_of(spec, name)
    if "{content_type}" in allowed:  # the Document API's map keyed by content type
        return [
            problem
            for key, item in value.items()
            for problem in problems(spec, "resourceContent", item, f"{path}.{key}")
        ]
    found = [f"{path}: missing {member}" for member in sorted(required - set(value))]
    # documentMetadata requires company_number without defining it; required means allowed.
    found += [f"{path}: undefined {member}" for member in sorted(set(value) - allowed - required)]
    for member in set(value) & properties.keys():
        found += member_problems(spec, properties[member], value[member], f"{path}.{member}")
    return found


def member_problems(spec: str, schema: dict[str, Any], value: Any, path: str) -> list[str]:
    reference = (schema.get("items") or {}).get("$ref")
    if "enum" in schema and isinstance(value, str) and value not in schema["enum"]:
        return [f"{path}: {value!r} is not one of the enumerated values"]
    if reference and isinstance(value, dict):
        return problems(*resolve(spec, reference), value, path)
    if reference and isinstance(value, list):
        return [
            problem
            for index, item in enumerate(value)
            for problem in problems(*resolve(spec, reference), item, f"{path}[{index}]")
        ]
    return []


@pytest.mark.parametrize(
    ("fixture", "spec", "definition"),
    [
        ("search-companies.json", "search.json", "CompanySearch"),
        ("company-profile.json", "companyProfile.json", "companyProfile"),
        ("officers.json", "companyOfficerList.json", "officerList"),
        ("filing-history-accounts.json", "filingHistory.json", "filingHistoryList"),
        ("document-metadata.json", "document.json", "documentMetadata"),
    ],
)
def test_fixture_matches_the_official_spec(fixture, spec, definition):
    value = json.loads((API / fixture).read_text())

    assert problems(spec, definition, value) == []


def test_the_checker_catches_a_member_the_spec_does_not_define():
    value = json.loads((API / "company-profile.json").read_text()) | {"turnover": 1}

    assert problems("companyProfile.json", "companyProfile", value) == [": undefined turnover"]


def test_packaged_sic_list_matches_the_published_one():
    assert SIC_LIST.read_bytes() == (SPECS / "SIC07_CH_condensed_list_en.csv").read_bytes()


@pytest.mark.parametrize(
    ("code", "description"),
    [
        ("01110", "Growing of cereals (except rice), leguminous crops and oil seeds"),
        ("62020", "Information technology consultancy activities"),
        ("99999", "Dormant Company"),
        ("00000", None),
    ],
)
def test_sic_descriptions(code, description):
    assert sic_description(code) == description


def test_the_checker_follows_nested_items_and_enumerations():
    value = json.loads((API / "officers.json").read_text())
    value["items"][0]["officer_role"] = "wizard"

    assert problems("companyOfficerList.json", "officerList", value) == [
        ".items[0].officer_role: 'wizard' is not one of the enumerated values"
    ]
