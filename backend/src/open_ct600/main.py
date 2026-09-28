"""FastAPI application: the Open CT600 API and, optionally, the built frontend."""

from datetime import date
from pathlib import PurePosixPath
from typing import Annotated, Self

from fastapi import APIRouter, FastAPI, status
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, model_validator
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import Scope

from open_ct600.config import Settings
from open_ct600.ct600 import CT600Return, Pounds, ReturnComputation, Submission, compute_return
from open_ct600.filing import SubmissionReceipt, submit_return
from open_ct600.tax import PeriodError, TaxComputation, compute_corporation_tax, validate_period


class CalculatorRequest(BaseModel):
    """Inputs to the standalone Corporation Tax calculator."""

    model_config = ConfigDict(extra="forbid")

    period_start: date
    period_end: date
    taxable_profits: Pounds
    associated_companies: Annotated[int, Field(ge=0, le=999)] = 0
    exempt_distributions: Pounds = 0

    @model_validator(mode="after")
    def _check_period(self) -> Self:
        try:
            validate_period(self.period_start, self.period_end)
        except PeriodError as error:
            raise ValueError(str(error)) from error
        return self


class Health(BaseModel):
    """Liveness response."""

    status: str


api = APIRouter(prefix="/api")


@api.get("/health")
def health() -> Health:
    """Report that the API is running."""
    return Health(status="ok")


@api.post("/calculator")
def calculate(request: CalculatorRequest) -> TaxComputation:
    """Compute Corporation Tax for a period and taxable profit."""
    return compute_corporation_tax(
        request.period_start,
        request.period_end,
        taxable_profits=request.taxable_profits,
        associated_companies=request.associated_companies,
        exempt_distributions=request.exempt_distributions,
    )


@api.post("/returns/compute")
def compute(ct600: CT600Return) -> ReturnComputation:
    """Compute the CT600 boxes, tax and accounts for a draft return."""
    return compute_return(ct600)


@api.post("/returns/submit", status_code=status.HTTP_201_CREATED)
def submit(submission: Submission) -> SubmissionReceipt:
    """Accept a declared return and issue a receipt. Nothing is sent to HMRC."""
    return submit_return(submission)


class SinglePageApp(StaticFiles):
    """Static files that fall back to ``index.html`` so client-side routes load."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        """Serve ``path``, or ``index.html`` for unknown page routes.

        Only extension-less paths outside ``/api`` are page routes; a missing asset such as
        ``/assets/app.js`` stays a 404 rather than being answered with HTML.
        """
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as error:
            is_page_route = not path.startswith("api") and "." not in PurePosixPath(path).name
            if error.status_code != status.HTTP_404_NOT_FOUND or not is_page_route:
                raise
            return await super().get_response("index.html", scope)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the application.

    Args:
        settings: Configuration; read from the environment when omitted.

    Returns:
        The configured FastAPI application.
    """
    resolved = settings or Settings()
    app = FastAPI(title="Open CT600", version="0.1.0")
    app.include_router(api)
    if resolved.static_dir is not None:
        if not (resolved.static_dir / "index.html").is_file():
            raise RuntimeError(
                f"STATIC_DIR={resolved.static_dir} has no index.html. "
                "Build the frontend with `pnpm build` or unset STATIC_DIR."
            )
        app.mount("/", SinglePageApp(directory=resolved.static_dir, html=True), name="app")
    return app
