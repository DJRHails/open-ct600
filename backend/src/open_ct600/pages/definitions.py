"""Which boxes on each supplementary page the service calculates.

Companies answer the other boxes; these are filled in by the page calculations in
``open_ct600.pages`` (totals, tax at a rate, copies of main-return boxes, the steps of the
RDEC and AVEC/VGEC set-off). A group whose every element is calculated, such as CT600L's step
sections, is calculated as a whole, including whether it appears at all.

The frontend reads ``COMPUTED_BOXES`` through ``GET /api/schema/pages`` to show these boxes as
answers the service gives rather than questions.
"""

from functools import cache

from open_ct600.schema.spec import PageCode, SpecNode, load_spec


def _boxes(text: str) -> frozenset[str]:
    return frozenset(text.split())


COMPUTED_BOXES: dict[PageCode, frozenset[str]] = {
    "A": _boxes("A15 A20 A30 A35 A40 A45 A55 A60 A65 A70 A80"),
    "B": _boxes("B5F B5J B10 B15 B20 B25 B30"),
    "C": _boxes("C10 C80 C90 C95 C100 C105/C110 C130 C185 C195 C200 C205 C210/C215"),
    "D": frozenset(),
    "E": _boxes("E88 E90 E125 E200"),
    "F": _boxes("F70G F70"),
    "G": frozenset(),
    "H": _boxes("H5G"),
    "I": _boxes("I30 I35 I45 I65 I70 I80 I85 I135D I140D I145D I150D I155C I160C"),
    "J": frozenset(),
    "K": _boxes(
        "K5 K15.1A K15.1B K15.1C K15.1D K15.2A K15.2B K15.2C K15.2D K20 K30 K35",
    ),
    "L": _boxes(
        """
        L6 L7 L8 L9 L10 L15 L25 L30 L40 L45 L50 L55 L60 L62 L65 L70 L75 L80 L85 L95 L105
        L120 L125 L129 L130 L140 L145 L150 L155 L160 L165 L166 L170 L180
        L194 L195 L200 L205 L210
        """
    ),
    "M": _boxes("M10 M15 M25 M30"),
    "N": _boxes("N50 N85 N100 N125 N165 N195 N250 N260 N265 N270 N280 N285"),
    "P": _boxes(
        """
        P30A P30B P30C P30D P30E P45A P45B P45C P45D P55 P60 P65 P70 P75 P80 P81 P85 P90
        P95 P100 P110 P115 P120 P125 P130 P135 P140 P145 P155 P165 P180 P190 P195 P200
        P210 P215 P220 P225 P230 P235 P240 P245 P255 P285A P285B P285C P285D P285E P305A
        P305B P305C P305D P305E P310 P315 P320 P330
        """
    ),
}


def _computed(node: SpecNode, boxes: frozenset[str], found: set[str]) -> bool:
    """Collect the paths of computed nodes below (and including) ``node``."""
    children = [_computed(child, boxes, found) for child in node.children]
    is_computed = node.box in boxes or (bool(children) and all(children))
    if is_computed:
        found.add(node.path)
    return is_computed


@cache
def computed_paths(code: PageCode) -> frozenset[str]:
    """The schema paths of the elements the service calculates on page ``code``.

    Raises:
        ValueError: If a computed box id is not on the page.
    """
    root = load_spec().page(code).node
    unknown = COMPUTED_BOXES[code] - {node.box for node in root.walk()}
    if unknown:
        raise ValueError(f"CT600{code} has no boxes {sorted(unknown)}")
    found: set[str] = set()
    for child in root.children:
        _computed(child, COMPUTED_BOXES[code], found)
    return frozenset(found)
