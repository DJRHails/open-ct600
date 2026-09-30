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
        ("DYSON, James, Sir", "Sir James Dyson"),
        ("SMITH, John Paul, Dr", "Dr John Paul Smith"),
        ("BROWN, James Gordon, Rt Hon", "Rt Hon James Gordon Brown"),
        ("SMITH, Jane, Dame", "Dame Jane Smith"),
        ("JONES, Sarah Anne, Mrs", "Mrs Sarah Anne Jones"),
        ("BLOGGS, Joseph, Professor Sir", "Professor Sir Joseph Bloggs"),
        ("HOPPER, Grace Brewster, Dr, OBE", "Dr Grace Brewster Hopper OBE"),
        ("PATEL, Priti, Rt Hon Dame, DBE", "Rt Hon Dame Priti Patel DBE"),
        ("NURSE, Paul Maxime, Sir FRS", "Sir Paul Maxime Nurse FRS"),
        ("  DYSON ,  James ,  Sir  ", "Sir James Dyson"),
        ("WATSON, John Hamish, DR", "DR John Hamish Watson"),
        ("MCDONALD, Ronald", "Ronald McDonald"),
        ("MACDONALD, Flora", "Flora Macdonald"),
    ],
)
def test_person_name(companies_house, written):
    assert person_name(companies_house) == written
