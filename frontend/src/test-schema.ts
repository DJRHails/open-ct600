/**
 * The real supplementary page definitions, as ``GET /api/schema/pages`` returns them, built from
 * the backend's committed schema spec so tests exercise HMRC's actual pages.
 */
import definitionsText from "../../backend/src/open_ct600/pages/definitions.py?raw";
import specText from "../../backend/src/open_ct600/schema/ct600-v1.994.json?raw";

import type { PageCode, SchemaPage, SpecNode } from "@/api";

/** ``open_ct600.schema.spec.PAGE_DEFINITIONS``: code, root element and title of each page. */
const DEFINITIONS: [PageCode, string, string][] = [
  ["A", "LoansByCloseCompanies", "Loans to participators by close companies"],
  [
    "B",
    "ControlledForeignCompanies",
    "Controlled foreign companies, foreign permanent establishment exemptions, hybrid and other mismatches",
  ],
  ["C", "GroupAndConsortium", "Group and consortium"],
  ["D", "Insurance", "Insurance"],
  ["E", "Charity", "Charities and Community Amateur Sports Clubs (CASCs)"],
  ["F", "TonnageTax", "Tonnage tax"],
  ["G", "NorthernIreland", "Northern Ireland"],
  ["H", "CrossBorderRoyalties", "Cross-border royalties"],
  ["I", "RingFenceTrade", "Supplementary charge in respect of ring fence trades"],
  ["J", "TaxAvoidanceSchemes", "Disclosure of tax avoidance schemes"],
  ["K", "RestitutionTax", "Restitution tax"],
  ["L", "ResearchAndDevelopment", "Research and development"],
  ["M", "Freeports", "Freeports and Investment Zones"],
  ["N", "ResidentialPropertyDeveloperTax", "Residential Property Developer Tax"],
  ["P", "CreativeIndustries", "Creative industries"],
];

/**
 * ``COMPUTED_BOXES`` from ``open_ct600.pages.definitions``: each page's entry is
 * ``"A": _boxes("A15 A20 ...")`` (possibly a triple-quoted string over several lines) or
 * ``"D": frozenset()``.
 */
const COMPUTED_ENTRY =
  /"(?<code>[A-P])":\s*(?:frozenset\(\)|_boxes\(\s*(?:"""(?<lines>[^"]*)"""|"(?<line>[^"]*)")\s*,?\s*\))/g;

function computedBoxes(): Map<string, string[]> {
  const found = new Map<string, string[]>();
  for (const match of definitionsText.matchAll(COMPUTED_ENTRY)) {
    const { code, lines, line } = match.groups ?? {};
    if (code) found.set(code, (lines ?? line ?? "").split(/\s+/).filter(Boolean));
  }
  if (found.size !== 15) throw new Error(`Read ${found.size} pages from COMPUTED_BOXES, not 15`);
  return found;
}

function returnNode(): SpecNode {
  const spec = JSON.parse(specText) as { root: SpecNode };
  const found = spec.root.children.find((child) => child.name === "CompanyTaxReturn");
  if (!found) throw new Error("The schema spec has no CompanyTaxReturn element");
  return found;
}

let cached: SchemaPage[] | null = null;

export function schemaPages(): SchemaPage[] {
  if (cached) return cached;
  const companyTaxReturn = returnNode();
  const computed = computedBoxes();
  cached = DEFINITIONS.map(([code, element, title]) => {
    const node = companyTaxReturn.children.find((child) => child.name === element);
    if (!node) throw new Error(`The schema spec has no ${element} element for CT600${code}`);
    return {
      code,
      element,
      title,
      dormant: code === "G",
      node,
      computed: computed.get(code) ?? [],
    };
  });
  return cached;
}

export function schemaPage(code: PageCode): SchemaPage {
  const page = schemaPages().find((candidate) => candidate.code === code);
  if (!page) throw new Error(`No CT600${code} in the schema spec`);
  return page;
}
