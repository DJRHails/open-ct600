"""API routes that download a return's iXBRL accounts and computations."""

from collections.abc import Callable

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from open_ct600.ct600 import CT600Return, ReturnComputation, compute_return
from open_ct600.ixbrl.accounts import render_accounts
from open_ct600.ixbrl.computations import render_computations
from open_ct600.ixbrl.layout import IxbrlRenderError

XHTML_MEDIA_TYPE = "application/xhtml+xml"

router = APIRouter(prefix="/api/returns")

Renderer = Callable[[CT600Return, ReturnComputation], str]


def _download(ct600: CT600Return, render: Renderer, document: str) -> Response:
    try:
        xhtml = render(ct600, compute_return(ct600))
    except IxbrlRenderError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    filename = f"{ct600.company.registration_number}-{document}-{ct600.period.end}.xhtml"
    return Response(
        content=xhtml,
        media_type=XHTML_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/accounts.xhtml", response_class=Response)
def accounts_xhtml(ct600: CT600Return) -> Response:
    """Download the return's statutory accounts as Inline XBRL (FRC 2026 taxonomy)."""
    return _download(ct600, render_accounts, "accounts")


@router.post("/computations.xhtml", response_class=Response)
def computations_xhtml(ct600: CT600Return) -> Response:
    """Download the Corporation Tax computation as Inline XBRL (HMRC ct-comp taxonomy).

    Answers 422 when HMRC accepts no published computations taxonomy for the period.
    """
    return _download(ct600, render_computations, "computations")
