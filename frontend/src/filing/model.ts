/**
 * The draft return: what the user has typed, section by section, and how each section
 * is validated and turned into the API payload.
 *
 * A section is stored only once it validates, so "saved" means "completed".
 */
import type { CompanyDetails, CT600Return } from "@/api";
import type { DateParts } from "@/components/forms";
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
export type SectionKey = "company" | "period" | AmountSectionKey;

export type Draft = {
  company?: { name: string; registration_number: string; utr: string };
  period?: { start: DateParts; end: DateParts };
  profit_and_loss?: Record<string, string>;
  tax_adjustments?: Record<string, string>;
  balance_sheet?: Record<string, string>;
};

export type FieldErrors = Record<string, string>;
export type Validated<T> = { ok: true; value: T } | { ok: false; errors: FieldErrors };

export type AmountField<K extends AmountSectionKey> = {
  key: keyof AmountSections[K] & string;
  label: string;
  errorLabel: string;
  hint?: string;
  kind?: "count";
};

export type AmountSection<K extends AmountSectionKey> = {
  key: K;
  slug: string;
  title: string;
  intro: string;
  fields: AmountField<K>[];
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
};

export const BALANCE_SHEET: AmountSection<"balance_sheet"> = {
  key: "balance_sheet",
  slug: "balance-sheet",
  title: "Balance sheet",
  intro:
    "Enter your company's balance sheet at the end of the accounting period, in whole pounds. " +
    "Leave a box blank if the amount is zero.",
  fields: [
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
      hint: "Cash at bank, money owed to the company, stock and prepayments.",
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
};

export const SECTION_SLUGS: Record<SectionKey, string> = {
  company: "company-details",
  period: "accounting-period",
  profit_and_loss: PROFIT_AND_LOSS.slug,
  tax_adjustments: TAX_ADJUSTMENTS.slug,
  balance_sheet: BALANCE_SHEET.slug,
};

export const SECTION_ORDER: SectionKey[] = [
  "company",
  "period",
  "profit_and_loss",
  "tax_adjustments",
  "balance_sheet",
];

const COMPANY_NUMBER = /^(?:\d{8}|[A-Z]{2}\d{6})$/;
const UTR = /^\d{10}$/;
const MAX_ASSOCIATED_COMPANIES = 999;

export function validateCompany(values: NonNullable<Draft["company"]>): Validated<CompanyDetails> {
  const errors: FieldErrors = {};
  const name = values.name.trim();
  const registrationNumber = values.registration_number.replace(/\s+/g, "").toUpperCase();
  const utr = values.utr.replace(/\s+/g, "");
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
  if (Object.keys(errors).length > 0) return { ok: false, errors };
  return { ok: true, value: { name, registration_number: registrationNumber, utr } };
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
        "End date must be within 12 months of the start date. " +
        "Split a longer period of account into two returns.";
    }
  }
  if (!start.ok || !end.ok || Object.keys(errors).length > 0) return { ok: false, errors };
  return { ok: true, value: { start: start.value, end: end.value } };
}

export function validateAmounts<K extends AmountSectionKey>(
  section: AmountSection<K>,
  values: Record<string, string>,
): Validated<AmountSections[K]> {
  const errors: FieldErrors = {};
  const parsed: Record<string, number> = {};
  for (const field of section.fields) {
    const raw = values[field.key] ?? "";
    const result =
      field.kind === "count"
        ? parseCount(raw, field.errorLabel, MAX_ASSOCIATED_COMPANIES)
        : parseWholePounds(raw, field.errorLabel);
    if (result.ok) parsed[field.key] = result.value;
    else errors[field.key] = result.error;
  }
  if (Object.keys(errors).length > 0) return { ok: false, errors };
  return { ok: true, value: parsed as AmountSections[K] };
}

/** Build the API payload, or ``null`` if any section is not yet completed. */
export function toReturn(draft: Draft): CT600Return | null {
  if (!draft.company || !draft.period) return null;
  if (!draft.profit_and_loss || !draft.tax_adjustments || !draft.balance_sheet) return null;
  const company = validateCompany(draft.company);
  const period = validatePeriod(draft.period);
  const profitAndLoss = validateAmounts(PROFIT_AND_LOSS, draft.profit_and_loss);
  const adjustments = validateAmounts(TAX_ADJUSTMENTS, draft.tax_adjustments);
  const balanceSheet = validateAmounts(BALANCE_SHEET, draft.balance_sheet);
  if (!company.ok || !period.ok || !profitAndLoss.ok || !adjustments.ok || !balanceSheet.ok) {
    return null;
  }
  return {
    company: company.value,
    period: period.value,
    profit_and_loss: profitAndLoss.value,
    tax_adjustments: adjustments.value,
    balance_sheet: balanceSheet.value,
  };
}

export function completedCount(draft: Draft): number {
  return SECTION_ORDER.filter((key) => draft[key] !== undefined).length;
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
      ];
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

function amountRows<K extends AmountSectionKey>(
  section: AmountSection<K>,
  values: AmountSections[K],
): AnswerRow[] {
  return section.fields.map((field) => {
    const value = Number(values[field.key]);
    return {
      key: field.key,
      label: field.label,
      value: field.kind === "count" ? String(value) : formatPounds(value),
    };
  });
}
