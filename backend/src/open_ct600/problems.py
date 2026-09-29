"""Problems found while computing a return, located at the answer that needs fixing."""

from dataclasses import dataclass

Location = tuple[str | int, ...]


@dataclass(frozen=True)
class Problem:
    """Something the company must fix before the return can be computed.

    Attributes:
        location: Where the answer is, from the return's root, like
            ``("supplementary_pages", "A", "LoansInformation", "Loan", 0, "AmountOfLoan")`` or
            ``("research_and_development", "additional_information_submitted")``.
        message: What to fix, in GOV.UK error message style.
        box: The CT600 box id of the answer, if it is a box.
    """

    location: Location
    message: str
    box: str | None = None


class InvalidReturnError(ValueError):
    """Raised when a return has problems that stop it being computed."""

    def __init__(self, problems: list[Problem]) -> None:
        """Keep the problems; the message lists them for logs."""
        super().__init__("; ".join(problem.message for problem in problems))
        self.problems = problems
