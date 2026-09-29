"""A stub of Companies House's public data API and Document API for tests.

Responses come from ``fixtures/companies_house/api`` (shaped by the official swagger specs, see
``test_companies_house_fixtures.py``) and, for accounts content, the real filing of Ashday (1986)
Limited from the bulk accounts file. The company in the API fixtures (ACME WIDGETS LTD,
01234567) is made up.
"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx2

FIXTURES = Path(__file__).parent / "fixtures/companies_house"
API = FIXTURES / "api"
ACCOUNTS_XHTML = (FIXTURES / "accounts/Prod223_4316_02014751_20260331.html").read_bytes()
STORAGE = "https://document-api-images-live.ch.gov.uk.s3.eu-west-2.amazonaws.com/docs/sample"
COMPANY = "01234567"
DOCUMENT = "c2FtcGxlYWNjb3VudHMyMDI1"

type Answer = Callable[[], httpx2.Response]


def fixture(name: str) -> dict[str, Any]:
    return json.loads((API / name).read_text())


def json_answer(body: dict[str, Any], status: int = 200) -> Answer:
    return lambda: httpx2.Response(status, json=body)


def failing(error: Exception) -> Answer:
    def answer() -> httpx2.Response:
        raise error

    return answer


class StubCompaniesHouse:
    """Answers requests from fixtures; tests replace entries of ``answers`` by path."""

    def __init__(self) -> None:
        self.requests: list[httpx2.Request] = []
        self.answers: dict[str, Answer] = {
            "/search/companies": json_answer(fixture("search-companies.json")),
            f"/company/{COMPANY}": json_answer(fixture("company-profile.json")),
            f"/company/{COMPANY}/officers": json_answer(fixture("officers.json")),
            f"/company/{COMPANY}/filing-history": json_answer(
                fixture("filing-history-accounts.json")
            ),
            f"/document/{DOCUMENT}": json_answer(fixture("document-metadata.json")),
            f"/document/{DOCUMENT}/content": lambda: httpx2.Response(
                302, headers={"Location": f"{STORAGE}?X-Amz-Signature=abc"}
            ),
            "/docs/sample": lambda: httpx2.Response(
                200, content=ACCOUNTS_XHTML, headers={"Content-Type": "application/xhtml+xml"}
            ),
        }

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request)
        answer = self.answers.get(request.url.path)
        if answer is None:
            return httpx2.Response(404, json={"errors": [{"error": "company-profile-not-found"}]})
        return answer()

    def paths(self) -> list[str]:
        return [request.url.path for request in self.requests]
