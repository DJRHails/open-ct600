import pytest

from open_ct600.companies_house.names import person_name


@pytest.mark.parametrize(
    ("companies_house", "written"),
    [
        ("LOVELACE, Ada Augusta", "Ada Augusta Lovelace"),
        ("O'BRIEN, Siobhan", "Siobhan O'Brien"),
        ("SMITH-JONES, Mary  Ann", "Mary Ann Smith-Jones"),
        ("  WASEEM ,  Muhammad Arslan ", "Muhammad Arslan Waseem"),
        ("Mr M Thompson", "Mr M Thompson"),
        ("Isaac, Leslie Worrel, Rev.", "Isaac, Leslie Worrel, Rev."),
        ("Richard David HASSELL", "Richard David HASSELL"),
        ("ACME HOLDINGS LIMITED", "ACME HOLDINGS LIMITED"),
    ],
)
def test_person_name(companies_house, written):
    assert person_name(companies_house) == written
