"""Validate one iXBRL document with Arelle, offline, and write the log and facts as JSON.

Run in a subprocess by ``ixbrl_harness`` so each validation has a fresh Arelle and several can
run at once. Equivalent to::

    arelleCmdLine --internetConnectivity=offline --packages PACKAGE --calc=xbrl21 -v -f FILE \
        [--plugins validate/UK --disclosureSystem hmrc]

Usage:
    python arelle_runner.py [--hmrc-accounts-rules] PACKAGE FILE OUTPUT.json
"""

import json
import sys
from pathlib import Path
from typing import Any

from arelle.api.Session import Session
from arelle.ModelInstanceObject import ModelDimensionValue, ModelFact
from arelle.RuntimeOptions import RuntimeOptions

UK_PLUGIN_LOADED = "Activation of plug-in Validate UK successful"


def _member(dimension: ModelDimensionValue) -> str:
    if dimension.isExplicit:
        return str(dimension.memberQname)
    typed = dimension.typedMember
    return "" if typed is None else typed.stringValue


def _fact(fact: ModelFact) -> dict[str, Any]:
    context = fact.context
    dimensions = {}
    if context is not None:
        for dimension in context.qnameDims.values():
            dimensions[str(dimension.dimensionQname)] = _member(dimension)
    return {
        "name": str(fact.qname),
        "context": fact.contextID,
        "unit": fact.unitID,
        "decimals": fact.decimals,
        "value": str(fact.xValue) if fact.isNumeric else fact.value,
        "dimensions": dimensions,
    }


def main(argv: list[str]) -> None:
    hmrc_accounts_rules = "--hmrc-accounts-rules" in argv
    package, entry, output = (arg for arg in argv if arg != "--hmrc-accounts-rules")
    options = RuntimeOptions(
        entrypointFile=entry,
        packages=[package],
        internetConnectivity="offline",
        validate=True,
        # XBRL 2.1 calculation mode also enforces requires-element arcs, which is how ct-comp
        # declares its mandatory items; the default mode silently skips them.
        calcs="xbrl21",
        plugins="validate/UK" if hmrc_accounts_rules else None,
        disclosureSystemName="hmrc" if hmrc_accounts_rules else None,
        keepOpen=True,
        # Parallel runs must not race on Arelle's shared ~/.config/arelle files.
        disablePersistentConfig=True,
    )
    # Session's __exit__ is annotated as never receiving None, so close it explicitly.
    session = Session()
    try:
        session.run(options, logFileName="logToBuffer")
        log = json.loads(session.get_logs("json"))["log"]
        facts = [_fact(fact) for model in session.get_models() for fact in model.facts]
    finally:
        session.close()
    plugin_loaded = any(UK_PLUGIN_LOADED in record["message"]["text"] for record in log)
    Path(output).write_text(
        json.dumps({"log": log, "facts": facts, "uk_plugin_loaded": plugin_loaded})
    )


if __name__ == "__main__":
    main(sys.argv[1:])
