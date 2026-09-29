/**
 * Whether something read from outside this browser, like an imported file, has the shape of a
 * draft. It checks types, not answers: a section whose answers no longer validate just shows as
 * incomplete, as it would for a draft saved here.
 */
import type { CompanyRecord, PageCode, PreviousAccounts } from "@/api";
import type { DateParts } from "@/components/forms";
import { LEGAL_FORMS } from "@/filing/companiesHouse";
import type { ComparativesAnswers } from "@/filing/comparatives";
import {
  ACCOUNTS_ANSWERS_ADDED_LATER,
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
 * text, or answers of their own. The question pages always save every field, except that
 * answers saved before a question was added (``addedLater``) do not have it.
 */
function fieldsLike(template: object, addedLater: readonly string[] = []): Check {
  const fields = new Map(Object.entries(template));
  const check: Check = (value, path) => {
    if (!isRecord(value)) return path;
    const missing = [...fields.keys()].find(
      (key) => !Object.hasOwn(value, key) && !addedLater.includes(key),
    );
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

const isNumber: Check = (value, path) =>
  typeof value === "number" && Number.isFinite(value) ? null : path;

const isBoolean: Check = (value, path) => (typeof value === "boolean" ? null : path);

const orNull =
  (check: Check): Check =>
  (value, path) =>
    value === null ? null : check(value, path);

/** For a field the draft may leave out. */
const optional =
  (check: Check): Check =>
  (value, path) =>
    value === undefined ? null : check(value, path);

const listOf =
  (check: Check): Check =>
  (value, path) =>
    Array.isArray(value) ? firstProblem(value, path, check) : path;

const numberByKey: Check = (value, path) =>
  isRecord(value) ? firstProblem(value, path, isNumber) : path;

/** Exactly the fields of ``T``, each passing its own check. */
function shape<T>(fields: { [K in keyof Required<T>]: Check }): Check {
  const checks = new Map<string, Check>(Object.entries(fields));
  return (value, path) => {
    if (!isRecord(value)) return path;
    for (const [key, check] of checks) {
      const problem = check(value[key], `${path}.${key}`);
      if (problem) return problem;
    }
    const unknown = Object.keys(value).find((key) => !checks.has(key));
    return unknown === undefined ? null : `${path}.${unknown}`;
  };
}

const isLegalForm: Check = (value, path) =>
  LEGAL_FORMS.some((form) => form.value === value) ? null : path;

const ISO_PERIOD = shape<{ start: string; end: string }>({ start: isText, end: isText });

/** The company's record as the Companies House route returned it. */
const COMPANY_RECORD = shape<CompanyRecord>({
  number: isText,
  name: isText,
  status: orNull(isText),
  incorporated_on: orNull(isText),
  legal_form: orNull(isLegalForm),
  registered_office: orNull(
    shape<NonNullable<CompanyRecord["registered_office"]>>({
      lines: isTextList,
      postcode: orNull(isText),
    }),
  ),
  sic_codes: listOf(
    shape<CompanyRecord["sic_codes"][number]>({
      code: isText,
      description: orNull(isText),
    }),
  ),
  principal_activity: orNull(isText),
  directors: listOf(
    shape<CompanyRecord["directors"][number]>({ name: isText, appointed_on: orNull(isText) }),
  ),
  accounts: shape<CompanyRecord["accounts"]>({
    reference_date: orNull(isText),
    last_made_up_to: orNull(isText),
    next_period: orNull(ISO_PERIOD),
  }),
  suggested_period: orNull(
    shape<NonNullable<CompanyRecord["suggested_period"]>>({
      start: isText,
      end: isText,
      note: orNull(isText),
    }),
  ),
  previous_accounts: orNull(
    shape<PreviousAccounts>({
      period: ISO_PERIOD,
      filed_on: isText,
      standard: orNull((value, path) => (value === "micro" || value === "small" ? null : path)),
      dormant: orNull(isBoolean),
      profit_and_loss: orNull(numberByKey),
      balance_sheet: numberByKey,
      average_employees: orNull(isNumber),
      directors: isTextList,
      principal_activity: orNull(isText),
    }),
  ),
  previous_accounts_unavailable: orNull(isText),
});

/** A supplementary page's answers as typed: text, nested answers and lists of them. */
const isRawValue: Check = (value, path) => {
  if (typeof value === "string") return null;
  if (Array.isArray(value) || isRecord(value)) return firstProblem(value, path, isRawValue);
  return path;
};

const EMPTY_DATE: DateParts = { day: "", month: "", year: "" };
const PERIOD = fieldsLike({ start: EMPTY_DATE, end: EMPTY_DATE });
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
  companies_house: COMPANY_RECORD,
  company: fieldsLike(COMPANY),
  period: PERIOD,
  profit_and_loss: textByKey,
  tax_adjustments: textByKey,
  balance_sheet: textByKey,
  accounts: fieldsLike(ACCOUNTS, ACCOUNTS_ANSWERS_ADDED_LATER),
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
  comparatives: shape<ComparativesAnswers>({
    period: optional(PERIOD),
    profit_and_loss: optional(textByKey),
    balance_sheet: optional(textByKey),
    tax_on_profit: optional(isText),
    average_employees: optional(isText),
  }),
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
