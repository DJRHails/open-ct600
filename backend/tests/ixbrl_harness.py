"""Offline Arelle validation of iXBRL documents for the test suite.

Taxonomy packages are downloaded once to ``~/.cache/open-ct600/taxonomies/`` from the URLs
pinned in ``specs/ixbrl/taxonomies.tsv`` and checked against their SHA-256 digests.

Arelle always exits 0, even when validation fails or a plugin does not load, so every
validation parses Arelle's JSON log and treats any warning or error as a problem. Loading the
FRC taxonomy takes ~15 s per document, so ``validate`` runs documents in parallel processes.
"""

import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

REPOSITORY = Path(__file__).resolve().parents[2]
TAXONOMIES_TSV = REPOSITORY / "specs" / "ixbrl" / "taxonomies.tsv"
EXAMPLES = REPOSITORY / "specs" / "ixbrl" / "examples"
RUNNER = Path(__file__).with_name("arelle_runner.py")
FAILING_LEVELS = frozenset({"warning", "inconsistency", "error", "critical", "fatal"})
MAX_PARALLEL = 8


class Rules(Enum):
    """Which rule set a document is validated against."""

    ACCOUNTS = "accounts"
    """XBRL 2.1 + dimensions + iXBRL 1.1, and Arelle's UK plugin with HMRC's disclosure
    system (Joint Filing Validation Checks, statement wording)."""

    COMPUTATIONS = "computations"
    """XBRL 2.1 + dimensions + iXBRL 1.1, with requires-element (mandatory item) checks."""


@dataclass(frozen=True)
class Document:
    """An iXBRL document to validate against one taxonomy package."""

    xhtml: str
    package: str
    rules: Rules


@dataclass(frozen=True)
class Problem:
    """A warning or error Arelle logged."""

    level: str
    code: str
    message: str
    arguments: Mapping[str, str] = field(default_factory=dict)
    """The message's arguments, e.g. ``{"fact": "core:Equity", "contextID": "end"}``."""


@dataclass(frozen=True)
class Fact:
    """A fact as Arelle extracted it; numeric values are after transformation and sign."""

    name: str
    context: str
    unit: str | None
    decimals: str | None
    value: str
    dimensions: Mapping[str, str]


@dataclass(frozen=True)
class Validation:
    """The outcome of validating one document."""

    problems: tuple[Problem, ...]
    facts: tuple[Fact, ...]

    def codes(self) -> set[str]:
        """The distinct problem codes."""
        return {problem.code for problem in self.problems}

    def values(self, name: str) -> dict[str, str]:
        """The values of every fact for concept ``name``, keyed by context id."""
        return {fact.context: fact.value for fact in self.facts if fact.name == name}


def _cache_directory() -> Path:
    base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return base / "open-ct600" / "taxonomies"


def _pinned_packages() -> dict[str, tuple[str, str]]:
    with TAXONOMIES_TSV.open(newline="") as handle:
        rows = csv.DictReader(handle, delimiter="\t")
        return {row["name"]: (row["url"], row["sha256"]) for row in rows}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def taxonomy_package(name: str) -> Path:
    """The local path of a pinned taxonomy package, downloading and verifying it if needed.

    Raises:
        KeyError: If ``name`` is not listed in ``specs/ixbrl/taxonomies.tsv``.
        RuntimeError: If the download does not match the pinned SHA-256.
    """
    url, expected = _pinned_packages()[name]
    path = _cache_directory() / name
    if path.exists() and _sha256(path) == expected:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "open-ct600-tests"})
    with urllib.request.urlopen(request, timeout=300) as response:
        content = response.read()
    actual = hashlib.sha256(content).hexdigest()
    if actual != expected:
        raise RuntimeError(
            f"Taxonomy package {name} from {url} has SHA-256 {actual}, but "
            f"{TAXONOMIES_TSV} pins {expected}. Do not update the pin without checking why "
            "the published package changed."
        )
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as partial:
        partial.write(content)
    Path(partial.name).replace(path)
    return path


def _problems(log: list[dict[str, Any]]) -> list[Problem]:
    return [
        Problem(
            level=record["level"],
            code=record["code"],
            message=record["message"]["text"],
            arguments={
                name: str(value) for name, value in record["message"].get("args", {}).items()
            },
        )
        for record in log
        if record["level"] in FAILING_LEVELS
    ]


def _validate_one(document: Document, workspace: Path, key: str) -> Validation:
    entry = workspace / f"{key}.xhtml"
    output = workspace / f"{key}.json"
    entry.write_text(document.xhtml, encoding="utf-8")
    command = [sys.executable, str(RUNNER)]
    if document.rules is Rules.ACCOUNTS:
        command.append("--hmrc-accounts-rules")
    command += [str(taxonomy_package(document.package)), str(entry), str(output)]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=900, check=False)
    if completed.returncode != 0 or not output.exists():
        raise RuntimeError(f"Arelle runner failed for {key}:\n{completed.stderr}")
    report = json.loads(output.read_text())
    problems = _problems(report["log"])
    if document.rules is Rules.ACCOUNTS and not report["uk_plugin_loaded"]:
        problems.append(Problem("error", "harness:ukPlugin", "validate/UK plugin not loaded"))
    if not report["facts"]:
        problems.append(Problem("error", "harness:noFacts", "Arelle found no facts"))
    facts = tuple(Fact(**fact) for fact in report["facts"])
    return Validation(problems=tuple(problems), facts=facts)


def validate(documents: Mapping[str, Document]) -> dict[str, Validation]:
    """Validate documents with Arelle, offline, several at a time.

    Args:
        documents: Documents keyed by a name that is safe to use as a file name.

    Returns:
        Each document's validation, under the same key.
    """
    for package in {document.package for document in documents.values()}:
        taxonomy_package(package)
    with tempfile.TemporaryDirectory(prefix="arelle-") as directory:
        workspace = Path(directory)
        workers = max(1, min(len(documents), os.cpu_count() or 1, MAX_PARALLEL))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                key: pool.submit(_validate_one, document, workspace, key)
                for key, document in documents.items()
            }
            return {key: future.result() for key, future in futures.items()}
