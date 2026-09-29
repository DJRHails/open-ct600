"""Read and write a supplementary page's element tree by CT600 box id.

Page calculations work in box ids (``"A15"``), as the forms and HMRC's rules do; this module
turns them into element paths using the schema spec, so a calculation never spells out
``LoansInformation/TotalLoans``. Values are kept in the element-tree convention of
``open_ct600.schema.trees``: every scalar is a string (whole pounds ``"1234"``, pounds and
pence ``"1234.56"``, a tick ``"yes"``).
"""

import copy
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from functools import cache
from typing import cast

from pydantic import JsonValue

from open_ct600.problems import Location, Problem
from open_ct600.schema.spec import PageCode, SpecNode, load_spec

Value = Decimal | int | str | date | bool | Mapping[str, JsonValue] | None
"""A box value: an amount, text, a date, ``True`` for a tick, a group's element tree, or
``None`` to remove the box."""
Tree = dict[str, JsonValue]

_PENNY = Decimal("0.01")


@dataclass(frozen=True)
class BoxPath:
    """Where a box is on its page.

    Attributes:
        node: The box's spec node.
        names: Element names from the page root to the box.
        table: Element names from the page root to the repeating element (the table row) the
            box is in, or ``None`` when the box is not in a table.
    """

    node: SpecNode
    names: tuple[str, ...]
    table: tuple[str, ...] | None


@cache
def box_paths(code: PageCode) -> dict[str, BoxPath]:
    """Index a page's boxes by id.

    Raises:
        ValueError: If a box id appears twice on the page (it does not in the v1.994 schema).
    """
    index: dict[str, BoxPath] = {}
    root = load_spec().page(code).node
    stack: list[tuple[SpecNode, tuple[str, ...], tuple[str, ...] | None]] = [(root, (), None)]
    while stack:
        node, names, table = stack.pop()
        for child in node.children:
            child_names = (*names, child.name)
            child_table = child_names if table is None and child.repeats else table
            if child.box is not None:
                if child.box in index:
                    raise ValueError(f"CT600{code} box {child.box} appears twice")
                index[child.box] = BoxPath(child, child_names, child_table)
            stack.append((child, child_names, child_table))
    return index


def format_value(node: SpecNode, value: Value) -> JsonValue:
    """Write ``value`` as the element tree string for ``node``'s kind.

    Raises:
        ValueError: If a whole-pounds box is given pence, or a tick box anything but ``True``.
    """
    if isinstance(value, Mapping):
        return dict(value)
    if node.kind == "yes" and value is True:
        return "yes"
    if isinstance(value, date):
        return value.isoformat()
    if value is None or isinstance(value, bool):
        raise ValueError(f"Box {node.box} needs a value (True only for a tick box), not {value}")
    if node.kind in {"pounds", "integer", "year"}:
        amount = Decimal(value)
        if amount != amount.to_integral_value():
            raise ValueError(f"Box {node.box} takes whole numbers, not {value}")
        return str(int(amount))
    if node.kind in {"money", "percent"}:
        return f"{Decimal(value).quantize(_PENNY):f}"
    return str(value)


class Elements:
    """Box access below one element: a page's root, or one row of a table on the page."""

    def __init__(
        self,
        page: "PageTree",
        element: Tree,
        table: tuple[str, ...] | None,
        location: Location,
    ) -> None:
        """Wrap ``element``, found at ``location``; ``table`` names the table it is a row of."""
        self._page = page
        self._element = element
        self._table = table
        self._location = location

    def _names(self, box: str) -> tuple[BoxPath, tuple[str, ...]]:
        path = self._page.path(box)
        is_whole_table = self._table is None and path.table == path.names
        if path.table != self._table and not is_whole_table:
            where = "a row of its table" if path.table is not None else "the page"
            raise ValueError(f"CT600{self._page.code} box {box} must be read from {where}")
        depth = 0 if self._table is None else len(self._table)
        return path, path.names[depth:]

    def _lookup(self, box: str) -> JsonValue:
        _, names = self._names(box)
        current: JsonValue = self._element
        for name in names:
            if not isinstance(current, dict) or name not in current:
                return None
            current = current[name]
        return current

    def has(self, box: str) -> bool:
        """Whether the box (or group) has an answer."""
        return self._lookup(box) is not None

    def text(self, box: str) -> str | None:
        """The box's answer, or ``None``."""
        value = self._lookup(box)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"CT600{self._page.code} box {box} is not a single value")
        return value

    def amount(self, box: str) -> Decimal:
        """The box's amount, 0 when it is not answered."""
        value = self.text(box)
        return Decimal(0) if value is None else Decimal(value)

    def day(self, box: str) -> date | None:
        """The box's date, or ``None``."""
        value = self.text(box)
        return None if value is None else date.fromisoformat(value)

    def ticked(self, box: str) -> bool:
        """Whether a tick (or yes/no) box is answered ``yes``."""
        return self.text(box) == "yes"

    def group(self, box: str) -> Tree | None:
        """A group box's answers, like a period's ``{"From": …, "To": …}``."""
        value = self._lookup(box)
        return value if isinstance(value, dict) else None

    def set(self, box: str, value: Value) -> None:
        """Answer the box, creating its enclosing groups; ``None`` removes it."""
        path, names = self._names(box)
        parents: list[Tree] = [self._element]
        for name in names[:-1]:
            child = parents[-1].get(name)
            if not isinstance(child, dict):
                if value is None:
                    return
                child = parents[-1][name] = {}
            parents.append(cast(Tree, child))
        if value is None:
            parents[-1].pop(names[-1], None)
            for parent, name in zip(reversed(parents[:-1]), reversed(names[:-1]), strict=True):
                if parent.get(name) == {}:
                    del parent[name]
            return
        parents[-1][names[-1]] = format_value(path.node, value)

    def location(self, box: str) -> Location:
        """Where the box's answer is, from the return's root."""
        _, names = self._names(box)
        return (*self._location, *names)

    def problem(self, box: str, message: str) -> None:
        """Record a problem with the box's answer."""
        self._page.problems.append(Problem(self.location(box), message, box))


class Row(Elements):
    """One row of a table on a page.

    Attributes:
        index: The row's position in its table, from 0.
    """

    def __init__(self, page: "PageTree", element: Tree, table: tuple[str, ...], index: int) -> None:
        """Wrap the row ``element`` at position ``index`` of ``table``."""
        super().__init__(page, element, table, ("supplementary_pages", page.code, *table, index))
        self.index = index


class PageTree(Elements):
    """A working copy of one supplementary page's answers, with the page's problems.

    Attributes:
        code: The page code, ``"A"`` for CT600A.
        tree: The page's element tree; calculations fill in computed boxes.
        problems: Problems found by the page's calculation.
    """

    def __init__(self, code: PageCode, answers: Mapping[str, JsonValue]) -> None:
        """Copy ``answers`` so the calculation can fill boxes in."""
        self.code: PageCode = code
        self.tree: Tree = {name: copy.deepcopy(answer) for name, answer in answers.items()}
        self.problems: list[Problem] = []
        super().__init__(self, self.tree, None, ("supplementary_pages", code))

    def defines(self, box: str) -> bool:
        """Whether the page has a box with this id (P5E exists, P15E does not)."""
        return box in box_paths(self.code)

    def path(self, box: str) -> BoxPath:
        """Where ``box`` is on this page.

        Raises:
            KeyError: If the page has no such box.
        """
        paths = box_paths(self.code)
        if box not in paths:
            raise KeyError(f"CT600{self.code} has no box {box}")
        return paths[box]

    def rows(self, box: str) -> list[Row]:
        """The rows of the table ``box`` is in (or is), in order; empty if none are answered."""
        table = self.path(box).table
        if table is None:
            raise ValueError(f"CT600{self.code} box {box} is not in a table")
        elements: JsonValue = self.tree
        for name in table:
            elements = elements.get(name) if isinstance(elements, dict) else None
        if not isinstance(elements, list):
            return []
        return [
            Row(self, element, table, index)
            for index, element in enumerate(elements)
            if isinstance(element, dict)
        ]

    def total(self, box: str) -> Decimal:
        """The sum of ``box`` over its table's rows."""
        return sum((row.amount(box) for row in self.rows(box)), Decimal(0))

    def answered_in_any_row(self, box: str) -> bool:
        """Whether any row of ``box``'s table answers it."""
        return any(row.has(box) for row in self.rows(box))

    def section(self, *names: str) -> Tree | None:
        """The answers in the section (a group without a box id) at ``names``, if any."""
        element: JsonValue = self.tree
        for name in names:
            element = element.get(name) if isinstance(element, dict) else None
        return element if isinstance(element, dict) else None

    def remove(self, *names: str) -> None:
        """Remove the section at ``names`` and every answer in it."""
        parent = self.section(*names[:-1]) if len(names) > 1 else self.tree
        if parent is not None:
            parent.pop(names[-1], None)
