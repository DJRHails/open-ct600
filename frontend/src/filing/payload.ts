/**
 * The whole API payload: the sections and pages (``sectionsReturn``) plus the relief answers
 * the supplementary pages have no box for, each asked as its own task when it applies.
 */
import type { CT600Return, ElementTree, PageCode, SchemaPage } from "@/api";
import { type Draft, savedPeriod, sectionsReturn, type Validated } from "@/filing/model";
import {
  loanRows,
  s455RateChanges,
  surrenderingCompanies,
  validateCreative,
  validateLoanDates,
  validateResearch,
  validateSurrenderers,
} from "@/filing/reliefs";
import { convertPage } from "@/filing/supplementary/answers";

export type ReliefTask =
  | "research_and_development"
  | "participator_loan_dates"
  | "group_relief_surrenderers"
  | "creative_industries";

/** Each relief task's title, its path under ``/file``, and the page it belongs with, if any. */
export const RELIEF_TASKS: Record<
  ReliefTask,
  { title: string; slug: string; page: PageCode | null }
> = {
  research_and_development: {
    title: "Research and development relief",
    slug: "research-and-development",
    page: null,
  },
  participator_loan_dates: {
    title: "CT600A: when the loans were made",
    slug: "loan-dates",
    page: "A",
  },
  group_relief_surrenderers: {
    title: "CT600C: surrendering companies' figures",
    slug: "group-relief-surrenderers",
    page: "C",
  },
  creative_industries: {
    title: "CT600P: additional information form",
    slug: "creative-industries-form",
    page: "P",
  },
};

type ReliefFields = Required<
  Pick<
    CT600Return,
    | "research_and_development"
    | "participator_loan_dates"
    | "group_relief_surrenderers"
    | "creative_industries"
  >
>;

/** A chosen page's answers as an element tree (valid answers only), once its spec is loaded. */
export function pageTree(
  draft: Draft,
  pages: SchemaPage[] | undefined,
  code: PageCode,
): ElementTree | null {
  const page = pages?.find((candidate) => candidate.code === code);
  const raw = draft.supplementary_pages?.[code];
  if (!page || raw === undefined || !draft.chosen_pages?.includes(code)) return null;
  return convertPage(page, raw).value;
}

/** Whether CT600A has loans whose dates are needed: the s455 rate changes in the period. */
function needsLoanDates(draft: Draft, pages: SchemaPage[] | undefined): boolean {
  const ct600a = pageTree(draft, pages, "A");
  const period = savedPeriod(draft);
  if (!ct600a || !period || !s455RateChanges(period)) return false;
  return Object.values(loanRows(ct600a)).some((rows) => rows.length > 0);
}

/** The relief tasks that apply: R&D always; the others when their page needs them. */
export function reliefTasks(draft: Draft, pages: SchemaPage[] | undefined): ReliefTask[] {
  const ct600c = pageTree(draft, pages, "C");
  const tasks: ReliefTask[] = ["research_and_development"];
  if (needsLoanDates(draft, pages)) tasks.push("participator_loan_dates");
  if (ct600c && surrenderingCompanies(ct600c).length > 0) tasks.push("group_relief_surrenderers");
  if (draft.chosen_pages?.includes("P")) tasks.push("creative_industries");
  return tasks;
}

/** Check one relief task's saved answers; ``null`` if it has not been answered. */
export function checkRelief(
  draft: Draft,
  task: ReliefTask,
  pages: SchemaPage[] | undefined,
): Validated<unknown> | null {
  switch (task) {
    case "research_and_development":
      return draft.research_and_development
        ? validateResearch(draft.research_and_development, savedPeriod(draft)?.start)
        : null;
    case "participator_loan_dates": {
      const ct600a = pageTree(draft, pages, "A");
      const period = savedPeriod(draft);
      if (!draft.participator_loan_dates || !ct600a || !period) return null;
      return validateLoanDates(draft.participator_loan_dates, loanRows(ct600a), period);
    }
    case "group_relief_surrenderers": {
      const ct600c = pageTree(draft, pages, "C");
      if (!draft.group_relief_surrenderers || !ct600c) return null;
      return validateSurrenderers(draft.group_relief_surrenderers, surrenderingCompanies(ct600c));
    }
    case "creative_industries":
      return draft.creative_industries ? validateCreative(draft.creative_industries) : null;
  }
}

export function reliefComplete(
  draft: Draft,
  task: ReliefTask,
  pages: SchemaPage[] | undefined,
): boolean {
  return checkRelief(draft, task, pages)?.ok === true;
}

/** The relief answers for the payload; ``null`` until every relief task that applies is done. */
function reliefFields(draft: Draft, pages: SchemaPage[] | undefined): ReliefFields | null {
  const fields: ReliefFields = {
    research_and_development: null,
    participator_loan_dates: null,
    group_relief_surrenderers: [],
    creative_industries: null,
  };
  for (const task of reliefTasks(draft, pages)) {
    const checked = checkRelief(draft, task, pages);
    if (!checked?.ok) return null;
    Object.assign(fields, { [task]: checked.value });
  }
  return fields;
}

/** Build the API payload, or ``null`` if any section, page or relief task is not complete. */
export function toReturn(draft: Draft, pages?: SchemaPage[]): CT600Return | null {
  const sections = sectionsReturn(draft, pages);
  const reliefs = reliefFields(draft, pages);
  return sections && reliefs ? { ...sections, ...reliefs } : null;
}
