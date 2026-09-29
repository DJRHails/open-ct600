/**
 * Comparatives: last period's figures, shown beside this period's in the accounts. The Companies
 * Act requires them after the company's first period of account. They are typed in (or prefilled
 * from the accounts last filed at Companies House) on the profit and loss and balance sheet
 * pages, and sent as ``accounts.comparatives``.
 */
import type { CompanyRecord, Comparatives, CT600Return } from "@/api";
import type { DateParts } from "@/components/forms";
import { draftRecord, firstPeriodFromRecord } from "@/filing/companiesHouse";
import type { Draft, FieldErrors, Validated } from "@/filing/model";
import {
  addDays,
  addMonths,
  formatDate,
  isoToDateParts,
  type Parsed,
  parseCount,
  parseDateParts,
  parseWholePounds,
} from "@/format";

export type ComparativeSection = "profit_and_loss" | "balance_sheet";

/** The previous period of account and its figures, as typed. */
export type ComparativesAnswers = {
  period?: { start: DateParts; end: DateParts };
  profit_and_loss?: Record<string, string>;
  balance_sheet?: Record<string, string>;
  /** The previous period's tax charge, asked with its profit and loss account. */
  tax_on_profit?: string;
  /** The previous period's average number of employees, asked with the accounts details. */
  average_employees?: string;
};

export const PREVIOUS_EMPLOYEES = "previous_average_employees";
const MAX_EMPLOYEES = 9_999_999;

/** The previous period's average number of employees: optional, so a blank answer is ``null``. */
export function validatePreviousEmployees(raw: string | undefined): Parsed<number | null> {
  if (!raw?.trim()) return { ok: true, value: null };
  return parseCount(raw, "average number of employees in the previous period", MAX_EMPLOYEES);
}

/** A period of account can be extended to at most 18 months (Companies Act 2006 s392). */
const MAX_PERIOD_OF_ACCOUNT_MONTHS = 18;
export const TAX_ON_PROFIT = "tax_on_profit";

/** The fields of a section, as ``AmountSection`` lists them. */
type Field = { key: string; errorLabel: string };

/**
 * Comparatives are asked unless this is the company's first period of account: as the user says
 * in accounts details, or, until then, as the Companies House record shows. With neither, they
 * are asked, and the first-period question explains when they can be left out.
 */
export function comparativesAsked(draft: Draft): boolean {
  return firstPeriod(draft) !== "yes";
}

/** Whether this is the first period of account: as answered, as the record shows, or unknown. */
export function firstPeriod(draft: Draft): "yes" | "no" | "" {
  return draft.accounts?.first_period || firstPeriodFromRecord(draftRecord(draft));
}

/** Whether nothing was typed for the previous period on a section's page. */
function nothingGiven(answers: ComparativesAnswers | undefined, section: ComparativeSection) {
  const figures = Object.values(answers?.[section] ?? {});
  const dates = section === "profit_and_loss" ? Object.values(answers?.period ?? {}) : [];
  const parts = dates.flatMap((date) => Object.values(date));
  return [...figures, ...parts].every((text) => text.trim() === "");
}

export function previousFigureId(key: string): string {
  return `previous-${key}`;
}

export const PREVIOUS_START = "previous_start";
export const PREVIOUS_END = "previous_end";

/**
 * Check the previous period's dates: both given, real, in order, no longer than 18 months, and,
 * once this period's start (``followedBy``) is known, ending the day before it.
 */
export function validatePreviousPeriod(
  period: ComparativesAnswers["period"],
  followedBy?: string,
): Validated<CT600Return["period"]> {
  const empty = { day: "", month: "", year: "" };
  const start = parseDateParts(period?.start ?? empty, "start date of the previous period");
  const end = parseDateParts(period?.end ?? empty, "end date of the previous period");
  const errors: FieldErrors = {};
  if (!start.ok) errors[PREVIOUS_START] = start.error;
  if (!end.ok) errors[PREVIOUS_END] = end.error;
  if (start.ok && end.ok)
    Object.assign(errors, periodOrderErrors(start.value, end.value, followedBy));
  if (!start.ok || !end.ok || Object.keys(errors).length > 0) return { ok: false, errors };
  return { ok: true, value: { start: start.value, end: end.value } };
}

function periodOrderErrors(start: string, end: string, followedBy?: string): FieldErrors {
  const longest = addDays(addMonths(start, MAX_PERIOD_OF_ACCOUNT_MONTHS), -1);
  if (end < start) {
    return { [PREVIOUS_END]: "The previous period must end on or after the day it starts" };
  }
  if (end > longest) {
    return {
      [PREVIOUS_END]: `A period of account cannot be longer than ${MAX_PERIOD_OF_ACCOUNT_MONTHS} months, so it must end by ${formatDate(longest)}`,
    };
  }
  if (followedBy && end !== addDays(followedBy, -1)) {
    return {
      [PREVIOUS_END]: `The previous period of account must end on ${formatDate(addDays(followedBy, -1))}, the day before this period starts`,
    };
  }
  return {};
}

/** Check the previous period's figures for a section; a blank figure is nil, as this period's. */
export function validatePreviousFigures(
  fields: Field[],
  values: Record<string, string> | undefined,
): Validated<Record<string, number>> {
  const errors: FieldErrors = {};
  const figures: Record<string, number> = {};
  for (const { key, errorLabel } of fields) {
    const parsed = parseWholePounds(values?.[key] ?? "", `previous period’s ${errorLabel}`);
    if (parsed.ok) figures[key] = parsed.value;
    else errors[previousFigureId(key)] = parsed.error;
  }
  return Object.keys(errors).length > 0 ? { ok: false, errors } : { ok: true, value: figures };
}

/**
 * The problems with a section's comparatives, if they are asked. The profit and loss page also
 * holds the previous period's dates. The amount sections come before the first-period question,
 * so until it is answered (or the Companies House record shows it) a blank previous period is
 * accepted: the section reopens if the user then says it is not the first period.
 */
export function comparativesProblems(
  draft: Draft,
  section: ComparativeSection,
  fields: Field[],
  periodStart?: string,
): FieldErrors {
  if (!comparativesAsked(draft)) return {};
  if (firstPeriod(draft) === "" && nothingGiven(draft.comparatives, section)) return {};
  const figures = validatePreviousFigures(fields, draft.comparatives?.[section]);
  if (section !== "profit_and_loss") return figures.ok ? {} : figures.errors;
  const period = validatePreviousPeriod(draft.comparatives?.period, periodStart);
  const tax = validateTaxOnProfit(draft.comparatives);
  return {
    ...(figures.ok ? {} : figures.errors),
    ...(period.ok ? {} : period.errors),
    ...(tax.ok ? {} : { [previousFigureId(TAX_ON_PROFIT)]: tax.error }),
  };
}

function validateTaxOnProfit(answers: ComparativesAnswers | undefined) {
  return parseWholePounds(answers?.tax_on_profit ?? "", "previous period’s tax on profit");
}

/**
 * ``accounts.comparatives``: ``null`` for a first period, the previous period's figures
 * otherwise, or ``undefined`` while they are incomplete.
 */
export function comparativesFor(
  draft: Draft,
  fields: Record<ComparativeSection, Field[]>,
  periodStart: string,
): Comparatives | null | undefined {
  if (!comparativesAsked(draft)) return null;
  const period = validatePreviousPeriod(draft.comparatives?.period, periodStart);
  const pnl = validatePreviousFigures(fields.profit_and_loss, draft.comparatives?.profit_and_loss);
  const sheet = validatePreviousFigures(fields.balance_sheet, draft.comparatives?.balance_sheet);
  const tax = validateTaxOnProfit(draft.comparatives);
  const employees = validatePreviousEmployees(draft.comparatives?.average_employees);
  if (!period.ok || !pnl.ok || !sheet.ok || !tax.ok || !employees.ok) return undefined;
  return {
    period: period.value,
    profit_and_loss: pnl.value as CT600Return["profit_and_loss"],
    balance_sheet: sheet.value as CT600Return["balance_sheet"],
    tax_on_profit: tax.value,
    average_employees: employees.value,
  };
}

/** The previous figures for a section's fields from the accounts last filed, as typed text. */
function filedFigures(filed: Record<string, number>, fields: Field[]): Record<string, string> {
  return Object.fromEntries(
    fields.filter(({ key }) => key in filed).map(({ key }) => [key, String(filed[key])]),
  );
}

/** Comparatives from the accounts last filed at Companies House, for a section's fields. */
export function filedComparatives(
  record: CompanyRecord | null,
  section: ComparativeSection,
  fields: Field[],
): ComparativesAnswers | null {
  const filed = record?.previous_accounts;
  if (!filed) return null;
  const tax = filed.profit_and_loss.tax;
  return {
    period: { start: isoToDateParts(filed.period.start), end: isoToDateParts(filed.period.end) },
    [section]: filedFigures(filed[section], fields),
    ...(section === "profit_and_loss" && tax !== undefined ? { tax_on_profit: String(tax) } : {}),
  };
}

/** Where prefilled comparatives came from: "From the accounts filed on … for the period …". */
export function filingDescription(record: CompanyRecord | null): string | null {
  const filed = record?.previous_accounts;
  if (!filed) return null;
  return `From the accounts filed on ${formatDate(filed.filed_on)} for the period ending ${formatDate(filed.period.end)}.`;
}
