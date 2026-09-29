"""The taxonomies HMRC accepts for Company Tax Return accounts and computations.

Acceptance windows are from HMRC's "Corporation Tax: taxonomies accepted by HMRC" guidance
(updated 17 April 2026). The package files and their SHA-256 digests are pinned in
``specs/ixbrl/taxonomies.tsv``.
"""

from datetime import date

from open_ct600.ixbrl.xhtml import Taxonomy

FRC_2026 = Taxonomy(
    name="FRC 2026",
    schema_ref="https://xbrl.frc.org.uk/FRS-102/2026-01-01/FRS-102-2026-01-01.xsd",
    namespaces={
        "core": "http://xbrl.frc.org.uk/fr/2026-01-01/core",
        "bus": "http://xbrl.frc.org.uk/cd/2026-01-01/business",
        "direp": "http://xbrl.frc.org.uk/reports/2026-01-01/direp",
    },
    package="FRC-2026-Taxonomy-v1.0.0.zip",
    accepted_period_start=date(2015, 4, 1),
    accepted_period_end=None,
)

CT_COMP_2024 = Taxonomy(
    name="HMRC Corporation Tax computational 2024",
    schema_ref="http://www.hmrc.gov.uk/schemas/ct/comp/2024-01-01/ct-comp-2024.xsd",
    namespaces={"ct-comp": "http://www.hmrc.gov.uk/schemas/ct/comp/2024-01-01"},
    package="CT2024-v1.0.0.zip",
    accepted_period_start=date(2015, 4, 1),
    accepted_period_end=date(2026, 3, 31),
)


def computations_taxonomy_for(period_start: date, period_end: date) -> Taxonomy | None:
    """The computations taxonomy HMRC accepts for an accounting period.

    HMRC has not published the Corporation Tax computational 2025 taxonomy, so no accepted
    taxonomy exists yet for periods ending after 31 March 2026 (HMRC error 3320).

    Args:
        period_start: First day of the accounting period.
        period_end: Last day of the accounting period.

    Returns:
        The taxonomy to use, or ``None`` when HMRC accepts none of the ones supported here.
    """
    return CT_COMP_2024 if CT_COMP_2024.accepts(period_start, period_end) else None
