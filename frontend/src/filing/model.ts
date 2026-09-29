/**
 * The draft return: what the user has typed, section by section, and how each section
 * is validated and turned into the API payload.
 *
 * A section is stored only once it validates, so "saved" means "completed". A section saved
 * before its questions changed no longer validates, and shows as incomplete again.
 */
import type {
  AccountsDetails,
  CompanyDetails,
  CompanyRecord,
  CT600Return,
  LegalForm,
  ElementTree,
  PageCode,
  SchemaPage,
  TradingStatus,
} from "@/api";
import type { DateParts } from "@/components/forms";
import type { CreativeAnswers, ResearchAnswers, SurrendererAnswers } from "@/filing/reliefs";
import { LEGAL_FORMS } from "@/filing/companiesHouse";
import {
  type ComparativesAnswers,
  comparativesFor,
  comparativesProblems,
} from "@/filing/comparatives";
import { convertPage, getAt, isBlank, type RawTree } from "@/filing/supplementary/answers";
import {
  formatDate,
  formatPounds,
  parseCount,
  parseDateParts,
  parseWholePounds,
  twelveMonthPeriodEnd,
} from "@/format";

type AmountSections = Pick<CT600Return, "profit_and_loss" | "tax_adjustments" | "balance_sheet">;
export type AmountSectionKey = keyof AmountSections;
export type SectionKey = "company" | "period" | AmountSectionKey | "accounts";

export type CompanyAnswers = {
  name: string;
  registration_number: string;
  utr: string;
  /** CT600 box 4 code, "0" to "11". */
  company_type: string;
  principal_activity: string;
};

export type AccountsAnswers = {
  standard: AccountsDetails["standard"] | "";
  directors: string[];
  signing_director: string;
  approval_date: DateParts;
  average_employees: string;
  trading_status: TradingStatus | "";
  dormant: YesNo;
  legal_form: LegalForm | "";
  /** Whether this is the company's first period of account, when there are no comparatives. */
  first_period: YesNo;
};

/** A yes or no question's answer; blank until answered. */
export type YesNo = "yes" | "no" | "";

export type Draft = {
  /** The company's public record, from the company chosen in the Companies House search. */
  companies_house?: CompanyRecord;
  company?: CompanyAnswers;
  period?: { start: DateParts; end: DateParts };
  profit_and_loss?: Record<string, string>;
  tax_adjustments?: Record<string, string>;
  balance_sheet?: Record<string, string>;
  accounts?: AccountsAnswers;
  /** The supplementary pages the user said apply (none is ``[]``); absent until they answer. */
  chosen_pages?: PageCode[];
  /** Each chosen page's answers as typed, saved screen by screen. */
  supplementary_pages?: Partial<Record<PageCode, RawTree>>;
  research_and_development?: ResearchAnswers;
  /** Figures from CT600C's surrendering companies, by tax reference. */
  group_relief_surrenderers?: SurrendererAnswers;
  creative_industries?: CreativeAnswers;
  /** Last period's figures and dates, typed on the profit and loss and balance sheet pages. */
  comparatives?: ComparativesAnswers;
};

export type FieldErrors = Record<string, string>;
export type Validated<T> = { ok: true; value: T } | { ok: false; errors: FieldErrors };

export type AmountField<K extends AmountSectionKey> = {
  key: keyof AmountSections[K] & string;
  label: string;
  errorLabel: string;
  hint?: string;
  kind?: "count";
  /** The row's name in check your answers, when the label is a question. */
  summaryLabel?: string;
  /** Asked only when this holds for the answers; otherwise the amount is nil. */
  askedWhen?: (values: Record<string, string>, draft: Draft) => boolean;
};

export type AmountSection<K extends AmountSectionKey> = {
  key: K;
  slug: string;
  title: string;
  intro: string;
  fields: AmountField<K>[];
  /** Checks between the section's amounts, once each amount is valid on its own. */
  check?: (
    amounts: Record<string, number>,
    values: Record<string, string>,
    draft: Draft,
  ) => FieldErrors;
};

export const PROFIT_AND_LOSS: AmountSection<"profit_and_loss"> = {
  key: "profit_and_loss",
  slug: "profit-and-loss",
  title: "Profit and loss account",
  intro:
    "Enter the figures from your company's profit and loss account for this accounting " +
    "period, in whole pounds. Leave a box blank if the amount is zero.",
  fields: [
    {
      key: "turnover",
      label: "Turnover",
      errorLabel: "turnover",
      hint: "Sales and other income from the company's trade, before any expenses.",
    },
    {
      key: "interest_income",
      label: "Bank and building society interest received",
      errorLabel: "interest received",
    },
    {
      key: "cost_of_sales",
      label: "Cost of sales",
      errorLabel: "cost of sales",
      hint: "Materials, stock and other direct costs of what you sold.",
    },
    {
      key: "staff_costs",
      label: "Staff costs",
      errorLabel: "staff costs",
      hint: "Salaries, employer's National Insurance and pension contributions, including directors.",
    },
    {
      key: "depreciation",
      label: "Depreciation",
      errorLabel: "depreciation",
      hint: "The amount charged in your accounts for the fall in value of equipment and other assets.",
    },
    {
      key: "other_expenses",
      label: "Other expenses",
      errorLabel: "other expenses",
      hint: "Rent, utilities, insurance, travel, professional fees and any other running costs.",
    },
  ],
};

const PRE_2017_LOSSES = "losses_brought_forward_before_april_2017";

function positiveAmount(raw: string | undefined): boolean {
  const parsed = parseWholePounds(raw ?? "", "amount");
  return parsed.ok && parsed.value > 0;
}

/** Whether CT600C claims group relief for carried-forward losses (box C130). */
export function claimsCarriedForwardGroupRelief(draft: Draft): boolean {
  if (!draft.chosen_pages?.includes("C")) return false;
  const path = ["GroupAndConsortium", "GroupReliefForCarriedForwardLosses", "CompanyInformation"];
  const companies = getAt(draft.supplementary_pages?.C, [...path, "Company"]);
  return Array.isArray(companies) && companies.some((company) => !isBlank(company));
}

/**
 * Losses from before 1 April 2017 are part of those brought forward. They matter when the
 * company claims group relief for carried-forward losses, which its own later losses must be
 * used before (CTM82010), so the answer is needed then.
 */
function checkPre2017Losses(
  amounts: Record<string, number>,
  values: Record<string, string>,
  draft: Draft,
): FieldErrors {
  if ((amounts[PRE_2017_LOSSES] ?? 0) > (amounts.losses_brought_forward ?? 0)) {
    return {
      [PRE_2017_LOSSES]:
        "Losses from before 1 April 2017 are part of the trading losses brought forward, so cannot be more than them",
    };
  }
  if (claimsCarriedForwardGroupRelief(draft) && !(values[PRE_2017_LOSSES] ?? "").trim()) {
    return {
      [PRE_2017_LOSSES]:
        "Enter how much of the trading losses brought forward arose before 1 April 2017, or 0 if none",
    };
  }
  return {};
}

export const TAX_ADJUSTMENTS: AmountSection<"tax_adjustments"> = {
  key: "tax_adjustments",
  slug: "tax-adjustments",
  title: "Tax adjustments",
  intro:
    "Some expenses in your accounts cannot be deducted for tax, and some allowances and " +
    "reliefs are only given for tax. Leave a box blank if it does not apply.",
  fields: [
    {
      key: "disallowable_expenses",
      label: "Disallowable expenses",
      errorLabel: "disallowable expenses",
      hint: "Expenses in your accounts that cannot be deducted for tax, such as client entertaining and fines.",
    },
    {
      key: "capital_allowances",
      label: "Capital allowances",
      errorLabel: "capital allowances",
      hint: "Tax relief on equipment and vehicles you bought, for example the Annual Investment Allowance.",
    },
    {
      key: "losses_brought_forward",
      label: "Trading losses brought forward",
      errorLabel: "trading losses brought forward",
      hint: "Unused trading losses from earlier periods. We use as much as your trading profits allow.",
    },
    {
      key: PRE_2017_LOSSES,
      label: "How much of the trading losses brought forward arose before 1 April 2017?",
      summaryLabel: "Trading losses brought forward that arose before 1 April 2017",
      errorLabel: "losses brought forward from before 1 April 2017",
      hint:
        "Losses from before 1 April 2017 can only be set against profits of the same trade. " +
        "Later losses can be set against the company's other profits too, and must be used " +
        "before group relief for carried-forward losses. Enter 0 if none.",
      askedWhen: (values, draft) =>
        positiveAmount(values.losses_brought_forward) || claimsCarriedForwardGroupRelief(draft),
    },
    {
      key: "chargeable_gains",
      label: "Chargeable gains",
      errorLabel: "chargeable gains",
      hint: "Taxable gains from selling assets such as property or shares.",
    },
    {
      key: "qualifying_donations",
      label: "Qualifying charitable donations",
      errorLabel: "qualifying charitable donations",
    },
    {
      key: "exempt_distributions",
      label: "Dividends received from companies outside your group",
      errorLabel: "dividends received",
      hint: "These are not taxed, but they count towards the limits for the small profits rate.",
    },
    {
      key: "associated_companies",
      label: "Number of associated companies",
      errorLabel: "number of associated companies",
      hint: "Other companies under the same control as yours. Enter 0 if there are none.",
      kind: "count",
    },
  ],
  check: checkPre2017Losses,
};

export const BALANCE_SHEET: AmountSection<"balance_sheet"> = {
  key: "balance_sheet",
  slug: "balance-sheet",
  title: "Balance sheet",
  intro:
    "Enter your company's balance sheet at the end of the accounting period, in whole pounds, " +
    "in the order of the micro-entity format. Leave a box blank if the amount is zero.",
  fields: [
    {
      key: "called_up_share_capital_not_paid",
      label: "Called up share capital not paid",
      errorLabel: "called up share capital not paid",
      hint: "Money shareholders still owe the company for shares it has called up.",
    },
    {
      key: "fixed_assets",
      label: "Fixed assets",
      errorLabel: "fixed assets",
      hint: "Equipment, vehicles and property the company owns, after depreciation.",
    },
    {
      key: "current_assets",
      label: "Current assets",
      errorLabel: "current assets",
      hint: "Cash at bank, money owed to the company and stock.",
    },
    {
      key: "prepayments_and_accrued_income",
      label: "Prepayments and accrued income",
      errorLabel: "prepayments and accrued income",
      hint: "Costs paid in advance for the next period, and income earned but not yet billed.",
    },
    {
      key: "creditors_within_one_year",
      label: "Creditors: amounts falling due within one year",
      errorLabel: "creditors due within one year",
      hint: "Bills, loans, tax and director's loan balances the company must pay within 12 months.",
    },
    {
      key: "creditors_after_one_year",
      label: "Creditors: amounts falling due after more than one year",
      errorLabel: "creditors due after more than one year",
    },
    {
      key: "provisions",
      label: "Provisions for liabilities",
      errorLabel: "provisions for liabilities",
      hint: "Amounts set aside for liabilities whose timing or amount is uncertain.",
    },
    {
      key: "accruals_and_deferred_income",
      label: "Accruals and deferred income",
      errorLabel: "accruals and deferred income",
      hint: "Costs of this period not yet billed, and income received in advance.",
    },
    {
      key: "called_up_share_capital",
      label: "Called up share capital",
      errorLabel: "called up share capital",
      hint: "The nominal value of the company's issued shares, for example £100.",
    },
  ],
};

export const AMOUNT_SECTIONS = [PROFIT_AND_LOSS, TAX_ADJUSTMENTS, BALANCE_SHEET] as const;

export const SECTION_TITLES: Record<SectionKey, string> = {
  company: "Company details",
  period: "Accounting period",
  profit_and_loss: PROFIT_AND_LOSS.title,
  tax_adjustments: TAX_ADJUSTMENTS.title,
  balance_sheet: BALANCE_SHEET.title,
  accounts: "Accounts details",
};

export const SECTION_SLUGS: Record<SectionKey, string> = {
  company: "company-details",
  period: "accounting-period",
  profit_and_loss: PROFIT_AND_LOSS.slug,
  tax_adjustments: TAX_ADJUSTMENTS.slug,
  balance_sheet: BALANCE_SHEET.slug,
  accounts: "accounts-details",
};

export const SECTION_ORDER: SectionKey[] = [
  "company",
  "period",
  "profit_and_loss",
  "tax_adjustments",
  "balance_sheet",
  "accounts",
];

/**
 * CT600 box 4, type of company, with the codes and names in HMRC's Company Tax Return guide.
 * Only the types the service can tax are offered: insurance companies (5) and REIT C tax-exempt
 * companies (10) need treatment it does not provide, and the backend refuses them.
 */
export const COMPANY_TYPES: { value: string; label: string; hint?: string }[] = [
  {
    value: "0",
    label: "None of these",
    hint:
      "Most companies, including community interest companies and companies in their first " +
      "year of liquidation.",
  },
  {
    value: "1",
    label: "Unit trust or open-ended investment company",
    hint: "Authorised funds pay Corporation Tax at 20%.",
  },
  {
    value: "2",
    label: "Close investment-holding company",
    hint: "Pays the main rate on all profits, with no small profits rate or marginal relief.",
  },
  {
    value: "3",
    label: "Company in liquidation, second or later year",
    hint: "Pays the main rate on all profits.",
  },
  { value: "4", label: "Qualifying asset holding company" },
  { value: "6", label: "Members' club or voluntary association" },
  { value: "7", label: "Property management company" },
  { value: "8", label: "Charity, or a company owned by a charity" },
  {
    value: "9",
    label: "Real Estate Investment Trust C: residual company",
    hint: "Pays the main rate on all profits.",
  },
  {
    value: "11",
    label: "Non-resident company",
    hint: "Pays the main rate on all profits.",
  },
];

export const EMPTY_COMPANY: CompanyAnswers = {
  name: "",
  registration_number: "",
  utr: "",
  company_type: "0",
  principal_activity: "",
};

const COMPANY_NUMBER = /^(?:\d{8}|[A-Z]{2}\d{6})$/;
const UTR = /^\d{10}$/;
const MAX_ASSOCIATED_COMPANIES = 999;
const MAX_PRINCIPAL_ACTIVITY = 200;
const MAX_DIRECTOR_NAME = 120;
const MAX_EMPLOYEES = 9_999_999;

export function validateCompany(values: CompanyAnswers): Validated<CompanyDetails> {
  const errors: FieldErrors = {};
  const name = values.name.trim();
  const registrationNumber = values.registration_number.replace(/\s+/g, "").toUpperCase();
  const utr = values.utr.replace(/\s+/g, "");
  const principalActivity = (values.principal_activity ?? "").trim();
  const companyType = COMPANY_TYPES.find((type) => type.value === values.company_type);
  if (!name) errors.name = "Enter the company name";
  else if (name.length > 160) errors.name = "Company name must be 160 characters or fewer";
  if (!registrationNumber) errors.registration_number = "Enter the company registration number";
  else if (!COMPANY_NUMBER.test(registrationNumber)) {
    errors.registration_number =
      "Enter a company registration number in the correct format, like 01234567 or SC123456";
  }
  if (!utr) errors.utr = "Enter the company's Unique Taxpayer Reference";
  else if (!UTR.test(utr)) {
    errors.utr = "Enter a Unique Taxpayer Reference in the correct format, like 1234567890";
  }
  if (!companyType) errors.company_type = "Select the type of company";
  if (!principalActivity) errors.principal_activity = "Enter what the company does";
  else if (principalActivity.length > MAX_PRINCIPAL_ACTIVITY) {
    errors.principal_activity = `What the company does must be ${MAX_PRINCIPAL_ACTIVITY} characters or fewer`;
  }
  if (Object.keys(errors).length > 0 || !companyType) return { ok: false, errors };
  return {
    ok: true,
    value: {
      name,
      registration_number: registrationNumber,
      utr,
      company_type: Number(companyType.value),
      principal_activity: principalActivity,
    },
  };
}

export const EMPTY_ACCOUNTS: AccountsAnswers = {
  standard: "",
  directors: [""],
  signing_director: "",
  approval_date: { day: "", month: "", year: "" },
  average_employees: "",
  trading_status: "",
  dormant: "",
  legal_form: "",
  first_period: "",
};

/** The director fields' ids, so errors can link to the right input. */
export function directorId(index: number): string {
  return `directors-${index}`;
}

function directorErrors(directors: string[]): FieldErrors {
  const errors: FieldErrors = {};
  const seen = new Set<string>();
  directors.forEach((director, index) => {
    const key = directorId(index);
    const folded = director.toLowerCase();
    if (!director) errors[key] = `Enter the name of director ${index + 1}`;
    else if (director.length > MAX_DIRECTOR_NAME) {
      errors[key] = `Director's name must be ${MAX_DIRECTOR_NAME} characters or fewer`;
    } else if (seen.has(folded)) errors[key] = `${director} is already listed`;
    seen.add(folded);
  });
  return errors;
}

function parseEmployees(raw: string) {
  if (!raw.trim()) {
    return { ok: false as const, error: "Enter the average number of employees" };
  }
  return parseCount(raw, "average number of employees", MAX_EMPLOYEES);
}

/**
 * Validate the accounts details. ``endOfPeriod`` (an ISO date), when known, is checked against
 * the approval date: accounts are approved after the period ends.
 */
export function validateAccounts(
  values: AccountsAnswers,
  endOfPeriod?: string,
): Validated<AccountsDetailsAnswered> {
  const directors = values.directors.map((director) => director.trim());
  const errors: FieldErrors = { ...directorErrors(directors), ...companyFormErrors(values) };
  const approval = parseDateParts(values.approval_date, "date the accounts were approved");
  const employees = parseEmployees(values.average_employees);
  const { standard, trading_status: tradingStatus } = values;
  if (!standard) errors.standard = "Select how the accounts were prepared";
  if (!values.signing_director || !directors.includes(values.signing_director)) {
    errors.signing_director = "Select the director who signed the accounts";
  }
  if (!approval.ok) errors.approval_date = approval.error;
  else if (endOfPeriod !== undefined && approval.value <= endOfPeriod) {
    errors.approval_date =
      "The date the accounts were approved must be after the end of the accounting period";
  }
  if (!employees.ok) errors.average_employees = employees.error;
  Object.assign(errors, activityErrors(values));
  const { legal_form: legalForm } = values;
  if (!standard || !tradingStatus || !approval.ok || !employees.ok || !legalForm) {
    return { ok: false, errors };
  }
  if (Object.keys(errors).length > 0) return { ok: false, errors };
  return {
    ok: true,
    value: {
      standard,
      approval_date: approval.value,
      directors,
      signing_director: values.signing_director,
      average_employees: employees.value,
      trading_status: tradingStatus,
      dormant: values.dormant === "yes",
      legal_form: legalForm,
    },
  };
}

/** The accounts details the user answers; comparatives come from the amount sections. */
export type AccountsDetailsAnswered = Omit<AccountsDetails, "comparatives">;

/** The directors listed, the legal form, and whether this is the first period of account. */
function companyFormErrors(values: AccountsAnswers): FieldErrors {
  const errors: FieldErrors = {};
  if (values.directors.length === 0) {
    errors.directors = "Select the company’s directors, or add a person";
  }
  if (!values.legal_form) errors.legal_form = "Select the company’s legal form";
  if (!values.first_period) {
    errors.first_period = "Select yes if this is the company’s first period of account";
  }
  return errors;
}

/** Whether the company was dormant, and whether it traded: a dormant company cannot trade. */
function activityErrors(values: AccountsAnswers): FieldErrors {
  const errors: FieldErrors = {};
  if (!values.dormant) errors.dormant = "Select yes if the company was dormant during this period";
  if (!values.trading_status) errors.trading_status = "Select whether the company traded";
  else if (values.dormant === "yes" && values.trading_status === "trading") {
    errors.trading_status =
      "A dormant company cannot be trading: select whether it has never traded or has " +
      "stopped trading, or say it was not dormant";
  }
  return errors;
}

export function validatePeriod(
  values: NonNullable<Draft["period"]>,
): Validated<CT600Return["period"]> {
  const start = parseDateParts(values.start, "start date");
  const end = parseDateParts(values.end, "end date");
  const errors: FieldErrors = {};
  if (!start.ok) errors.start = start.error;
  if (!end.ok) errors.end = end.error;
  if (start.ok && end.ok) {
    if (end.value < start.value) {
      errors.end = "End date must be the same as or after the start date";
    } else if (end.value > twelveMonthPeriodEnd(start.value)) {
      errors.end =
        "End date must be within 12 months of the start date. This service prepares the " +
        "accounts for the same period as the return, so it cannot file for a period of " +
        "account longer than 12 months.";
    }
  }
  if (!start.ok || !end.ok || Object.keys(errors).length > 0) return { ok: false, errors };
  return { ok: true, value: { start: start.value, end: end.value } };
}

export function validateAmounts<K extends AmountSectionKey>(
  section: AmountSection<K>,
  values: Record<string, string>,
  draft: Draft = {},
): Validated<AmountSections[K]> {
  const errors: FieldErrors = {};
  const parsed: Record<string, number> = {};
  for (const field of section.fields) {
    if (field.askedWhen && !field.askedWhen(values, draft)) {
      parsed[field.key] = 0;
      continue;
    }
    const raw = values[field.key] ?? "";
    const result =
      field.kind === "count"
        ? parseCount(raw, field.errorLabel, MAX_ASSOCIATED_COMPANIES)
        : parseWholePounds(raw, field.errorLabel);
    if (result.ok) parsed[field.key] = result.value;
    else errors[field.key] = result.error;
  }
  if (Object.keys(errors).length === 0 && section.check) {
    Object.assign(errors, section.check(parsed, values, draft));
  }
  if (Object.keys(errors).length > 0) return { ok: false, errors };
  return { ok: true, value: parsed as AmountSections[K] };
}

/** The saved period's end date, if the period section is complete. */
export function periodEnd(draft: Draft): string | undefined {
  return savedPeriod(draft)?.end;
}

/** The saved accounting period, if the period section is complete. */
export function savedPeriod(draft: Draft): CT600Return["period"] | undefined {
  if (!draft.period) return undefined;
  const period = validatePeriod(draft.period);
  return period.ok ? period.value : undefined;
}

type SectionValues = {
  company: CompanyDetails;
  period: CT600Return["period"];
  profit_and_loss: CT600Return["profit_and_loss"];
  tax_adjustments: CT600Return["tax_adjustments"];
  balance_sheet: CT600Return["balance_sheet"];
  accounts: AccountsDetailsAnswered;
};

/** Validate one saved section; ``null`` if it has not been saved. */
function validateSection<K extends SectionKey>(
  draft: Draft,
  key: K,
): Validated<SectionValues[K]> | null {
  const validators: { [S in SectionKey]: () => Validated<SectionValues[S]> | null } = {
    company: () => (draft.company ? validateCompany(draft.company) : null),
    period: () => (draft.period ? validatePeriod(draft.period) : null),
    profit_and_loss: () =>
      draft.profit_and_loss
        ? withComparatives(
            draft,
            PROFIT_AND_LOSS,
            validateAmounts(PROFIT_AND_LOSS, draft.profit_and_loss),
          )
        : null,
    tax_adjustments: () =>
      draft.tax_adjustments ? validateAmounts(TAX_ADJUSTMENTS, draft.tax_adjustments, draft) : null,
    balance_sheet: () =>
      draft.balance_sheet
        ? withComparatives(
            draft,
            BALANCE_SHEET,
            validateAmounts(BALANCE_SHEET, draft.balance_sheet),
          )
        : null,
    accounts: () => (draft.accounts ? validateAccounts(draft.accounts, periodEnd(draft)) : null),
  };
  return validators[key]();
}

/** A section's amounts, which also need valid comparatives unless it is the first period. */
function withComparatives<K extends "profit_and_loss" | "balance_sheet">(
  draft: Draft,
  section: AmountSection<K>,
  amounts: Validated<AmountSections[K]>,
): Validated<AmountSections[K]> {
  const problems = comparativesProblems(
    draft,
    section.key,
    section.fields,
    savedPeriod(draft)?.start,
  );
  if (Object.keys(problems).length === 0) return amounts;
  return { ok: false, errors: { ...(amounts.ok ? {} : amounts.errors), ...problems } };
}

/** Whether a section has been saved and its answers are still valid. */
export function sectionComplete(draft: Draft, key: SectionKey): boolean {
  return validateSection(draft, key)?.ok === true;
}

/** Whether the answers need HMRC's page definitions (``GET /api/schema/pages``) to be checked. */
export function needsSchema(draft: Draft): boolean {
  return (draft.chosen_pages?.length ?? 0) > 0;
}

/** Whether a chosen page has been started and its answers are complete. */
export function pageComplete(draft: Draft, page: SchemaPage): boolean {
  const raw = draft.supplementary_pages?.[page.code];
  return raw !== undefined && convertPage(page, raw).problems.length === 0;
}

/** The chosen pages' element trees; ``null`` until they are chosen and all complete. */
function supplementaryPages(
  draft: Draft,
  pages: SchemaPage[] | undefined,
): Partial<Record<PageCode, ElementTree>> | null {
  if (draft.chosen_pages === undefined) return null;
  const trees: Partial<Record<PageCode, ElementTree>> = {};
  for (const code of draft.chosen_pages) {
    const page = pages?.find((candidate) => candidate.code === code);
    const raw = draft.supplementary_pages?.[code];
    if (!page || raw === undefined) return null;
    const converted = convertPage(page, raw);
    if (converted.problems.length > 0) return null;
    trees[code] = converted.value;
  }
  return trees;
}

/**
 * The return's sections and supplementary pages, or ``null`` if any is not yet completed.
 * ``pages`` are HMRC's page definitions, needed to check the answers to any pages chosen.
 * ``toReturn`` in ``filing/payload`` adds the relief answers the pages have no box for.
 */
export function sectionsReturn(draft: Draft, pages?: SchemaPage[]): CT600Return | null {
  const supplementary = supplementaryPages(draft, pages);
  const company = validateSection(draft, "company");
  const period = validateSection(draft, "period");
  const profitAndLoss = validateSection(draft, "profit_and_loss");
  const adjustments = validateSection(draft, "tax_adjustments");
  const balanceSheet = validateSection(draft, "balance_sheet");
  const accounts = validateSection(draft, "accounts");
  if (
    !company?.ok ||
    !period?.ok ||
    !profitAndLoss?.ok ||
    !adjustments?.ok ||
    !balanceSheet?.ok ||
    !accounts?.ok ||
    supplementary === null
  ) {
    return null;
  }
  const comparatives = comparativesFor(
    draft,
    { profit_and_loss: PROFIT_AND_LOSS.fields, balance_sheet: BALANCE_SHEET.fields },
    period.value.start,
  );
  if (comparatives === undefined) return null;
  return {
    company: company.value,
    period: period.value,
    profit_and_loss: profitAndLoss.value,
    tax_adjustments: adjustments.value,
    balance_sheet: balanceSheet.value,
    accounts: { ...accounts.value, comparatives },
    supplementary_pages: supplementary,
  };
}

export function completedCount(draft: Draft): number {
  return SECTION_ORDER.filter((key) => sectionComplete(draft, key)).length;
}

const STANDARD_LABELS: Record<AccountsDetails["standard"], string> = {
  micro: "Micro-entity accounts (FRS 105)",
  small: "Small company accounts (FRS 102 section 1A)",
};

export const TRADING_STATUS_LABELS: Record<TradingStatus, string> = {
  trading: "It traded during the period",
  never_traded: "It has never traded",
  no_longer_trading: "It has stopped trading",
};

export const STANDARD_OPTIONS = (["micro", "small"] as const).map((value) => ({
  value,
  label: STANDARD_LABELS[value],
}));

export const TRADING_STATUS_OPTIONS = (
  ["trading", "never_traded", "no_longer_trading"] as const
).map((value) => ({ value, label: TRADING_STATUS_LABELS[value] }));

export const YES_NO: { value: "yes" | "no"; label: string }[] = [
  { value: "yes", label: "Yes" },
  { value: "no", label: "No" },
];

function companyTypeLabel(code: number): string {
  return COMPANY_TYPES.find((type) => type.value === String(code))?.label ?? String(code);
}

export type AnswerRow = { key: string; label: string; value: string };

/** The answers in one section, formatted for a check-your-answers summary. */
export function answerRows(ct600: CT600Return, section: SectionKey): AnswerRow[] {
  switch (section) {
    case "company":
      return [
        { key: "name", label: "Company name", value: ct600.company.name },
        {
          key: "registration_number",
          label: "Company registration number",
          value: ct600.company.registration_number,
        },
        { key: "utr", label: "Unique Taxpayer Reference", value: ct600.company.utr },
        {
          key: "company_type",
          label: "Type of company",
          value: companyTypeLabel(ct600.company.company_type),
        },
        {
          key: "principal_activity",
          label: "What the company does",
          value: ct600.company.principal_activity,
        },
      ];
    case "accounts":
      return accountsRows(ct600.accounts);
    case "period":
      return [
        { key: "start", label: "Start date", value: formatDate(ct600.period.start) },
        { key: "end", label: "End date", value: formatDate(ct600.period.end) },
      ];
    case "profit_and_loss":
      return amountRows(PROFIT_AND_LOSS, ct600.profit_and_loss);
    case "tax_adjustments":
      return amountRows(TAX_ADJUSTMENTS, ct600.tax_adjustments);
    case "balance_sheet":
      return amountRows(BALANCE_SHEET, ct600.balance_sheet);
  }
}

function accountsRows(accounts: AccountsDetails): AnswerRow[] {
  return [
    { key: "standard", label: "Accounts prepared as", value: STANDARD_LABELS[accounts.standard] },
    { key: "directors", label: "Directors", value: accounts.directors.join(", ") },
    {
      key: "signing_director",
      label: "Director who signed the accounts",
      value: accounts.signing_director,
    },
    {
      key: "approval_date",
      label: "Date the accounts were approved",
      value: formatDate(accounts.approval_date),
    },
    {
      key: "average_employees",
      label: "Average number of employees",
      value: String(accounts.average_employees),
    },
    {
      key: "legal_form",
      label: "Legal form",
      value:
        LEGAL_FORMS.find((form) => form.value === accounts.legal_form)?.label ??
        accounts.legal_form,
    },
    {
      key: "first_period",
      label: "First period of account",
      value: accounts.comparatives === null ? "Yes" : "No",
    },
    { key: "dormant", label: "Dormant during the period", value: accounts.dormant ? "Yes" : "No" },
    {
      key: "trading_status",
      label: "Trading",
      value: TRADING_STATUS_LABELS[accounts.trading_status],
    },
  ];
}

function amountRows<K extends AmountSectionKey>(
  section: AmountSection<K>,
  values: AmountSections[K],
): AnswerRow[] {
  const answers = Object.fromEntries(
    Object.entries(values).map(([key, value]) => [key, String(value)]),
  );
  // A conditional amount is shown when it was asked, or is not nil.
  const shown = section.fields.filter(
    (field) => !field.askedWhen || field.askedWhen(answers, {}) || Number(values[field.key]) !== 0,
  );
  return shown.map((field) => {
    const value = Number(values[field.key]);
    return {
      key: field.key,
      label: field.summaryLabel ?? field.label,
      value: field.kind === "count" ? String(value) : formatPounds(value),
    };
  });
}
