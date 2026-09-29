/**
 * Whether something read from outside this browser, like an imported file, has the shape of a
 * draft. It checks types, not answers: a section whose answers no longer validate just shows as
 * incomplete, as it would for a draft saved here.
 */
import type { PageCode } from "@/api";
import type { DateParts } from "@/components/forms";
import {
  type AccountsAnswers,
  type CompanyAnswers,
  type Draft,
  EMPTY_ACCOUNTS,
  EMPTY_COMPANY,
} from "@/filing/model";
import {
  type CreativeAnswers,
  EMPTY_RESEARCH,
  type ResearchAnswers,
  type SurrendererFigures,
} from "@/filing/reliefs";
import { isRecord } from "@/filing/returns/savedReturns";

/** Where the shape is wrong, like ``draft.company.name``; ``null`` if it is right. */
type Check = (value: unknown, path: string) => string | null;

const PAGE_CODES: Record<PageCode, true> = {
  A: true,
  B: true,
  C: true,
  D: true,
  E: true,
  F: true,
  G: true,
  H: true,
  I: true,
  J: true,
  K: true,
  L: true,
  M: true,
  N: true,
  P: true,
};

function isPageCode(value: unknown): value is PageCode {
  return typeof value === "string" && Object.hasOwn(PAGE_CODES, value);
}

/** The first problem among the items of a list or the fields of a record. */
function firstProblem(
  container: object,
  path: string,
  check: (item: unknown, itemPath: string, key: string) => string | null,
): string | null {
  for (const [key, item] of Object.entries(container)) {
    const problem = check(item, `${path}.${key}`, key);
    if (problem) return problem;
  }
  return null;
}

const isText: Check = (value, path) => (typeof value === "string" ? null : path);

const isTextList: Check = (value, path) =>
  Array.isArray(value) ? firstProblem(value, path, isText) : path;

const textByKey: Check = (value, path) =>
  isRecord(value) ? firstProblem(value, path, isText) : path;

/**
 * Exactly the fields of ``template``, each of the same kind as the template's: text, a list of
 * text, or answers of their own. The question pages always save every field.
 */
function fieldsLike(template: object): Check {
  const fields = new Map(Object.entries(template));
  const check: Check = (value, path) => {
    if (!isRecord(value)) return path;
    const missing = [...fields.keys()].find((key) => !Object.hasOwn(value, key));
    if (missing) return `${path}.${missing}`;
    return firstProblem(value, path, (field, fieldPath, key) => {
      if (!fields.has(key)) return fieldPath;
      const example = fields.get(key);
      if (Array.isArray(example)) return isTextList(field, fieldPath);
      if (isRecord(example)) return fieldsLike(example)(field, fieldPath);
      return isText(field, fieldPath);
    });
  };
  return check;
}

/** A supplementary page's answers as typed: text, nested answers and lists of them. */
const isRawValue: Check = (value, path) => {
  if (typeof value === "string") return null;
  if (Array.isArray(value) || isRecord(value)) return firstProblem(value, path, isRawValue);
  return path;
};

const EMPTY_DATE: DateParts = { day: "", month: "", year: "" };
const COMPANY: CompanyAnswers = EMPTY_COMPANY;
const ACCOUNTS: AccountsAnswers = EMPTY_ACCOUNTS;
const RESEARCH: ResearchAnswers = EMPTY_RESEARCH;
const CREATIVE: CreativeAnswers = { additional_information_submitted: "" };
const SURRENDERER: SurrendererFigures = {
  surrenderable_amount: "",
  surrendered_to_others: "",
  consortium_share: "",
};

/** One check for every part of a draft, so a new part cannot be added without one. */
const DRAFT_CHECKS: { [K in keyof Required<Draft>]: Check } = {
  company: fieldsLike(COMPANY),
  period: fieldsLike({ start: EMPTY_DATE, end: EMPTY_DATE }),
  profit_and_loss: textByKey,
  tax_adjustments: textByKey,
  balance_sheet: textByKey,
  accounts: fieldsLike(ACCOUNTS),
  chosen_pages: (value, path) => {
    if (!Array.isArray(value)) return path;
    return firstProblem(value, path, (code, codePath) => (isPageCode(code) ? null : codePath));
  },
  supplementary_pages: (value, path) => {
    if (!isRecord(value)) return path;
    return firstProblem(value, path, (page, pagePath, code) =>
      isPageCode(code) && isRecord(page) ? isRawValue(page, pagePath) : pagePath,
    );
  },
  research_and_development: fieldsLike(RESEARCH),
  group_relief_surrenderers: (value, path) =>
    isRecord(value) ? firstProblem(value, path, fieldsLike(SURRENDERER)) : path,
  creative_industries: fieldsLike(CREATIVE),
};

function hasCheck(key: string): key is keyof Draft {
  return Object.hasOwn(DRAFT_CHECKS, key);
}

/** Where ``value`` is not shaped like a draft, like ``draft.company.name``; ``null`` if it is. */
export function draftShapeProblem(value: unknown): string | null {
  if (!isRecord(value)) return "draft";
  return firstProblem(value, "draft", (part, path, key) =>
    hasCheck(key) ? DRAFT_CHECKS[key](part, path) : path,
  );
}
