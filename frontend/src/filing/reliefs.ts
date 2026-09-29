/**
 * Answers for reliefs that the supplementary pages have no box for: the R&D claim, figures
 * from group relief surrendering companies (CT600C), the dates loans to participators were made
 * (CT600A) and the creative industries additional information form (CT600P). The checks mirror
 * the service's (``open_ct600.reliefs``), which also checks them against the computation.
 */
import type {
  ElementTree,
  JsonValue,
  ParticipatorLoanDates,
  ResearchAndDevelopment,
  ResearchAndDevelopmentClaimScheme,
  SurrenderingCompany,
} from "@/api";
import type { DateParts } from "@/components/forms";
import { type Parsed, parseDateParts, parseWholePounds } from "@/format";
import type { FieldErrors, Validated, YesNo } from "@/filing/model";

export type Period = { start: string; end: string };

/** Accounting periods starting on or after this date use merged RDEC or ERIS. */
export const MERGED_SCHEME_START = "2024-04-01";
/** Accounting periods starting on or after this date may need a claim notification. */
export const CLAIM_NOTIFICATION_START = "2023-04-01";

export type ResearchAnswers = {
  claiming: YesNo;
  scheme: ResearchAndDevelopmentClaimScheme | "";
  company_is_sme: YesNo;
  qualifying_expenditure: string;
  rdec_expenditure: string;
  intensity: string;
  claim_payable_credit: YesNo;
  rd_workers_paye_and_nic: string;
  claimed_in_previous_three_years: YesNo;
  claim_notification_submitted: YesNo;
  additional_information_submitted: YesNo;
};

export const EMPTY_RESEARCH: ResearchAnswers = {
  claiming: "",
  scheme: "",
  company_is_sme: "",
  qualifying_expenditure: "",
  rdec_expenditure: "",
  intensity: "",
  claim_payable_credit: "",
  rd_workers_paye_and_nic: "",
  claimed_in_previous_three_years: "",
  claim_notification_submitted: "",
  additional_information_submitted: "",
};

/** The schemes open to a period starting on ``start`` (all of them if it is not known yet). */
export function schemesFor(start: string | undefined): ResearchAndDevelopmentClaimScheme[] {
  if (start === undefined) return ["sme", "rdec", "eris"];
  return start >= MERGED_SCHEME_START ? ["rdec", "eris"] : ["sme", "rdec"];
}

/** Which of the claim's follow-up questions apply to these answers. */
export function researchQuestions(values: ResearchAnswers, start: string | undefined) {
  const { scheme } = values;
  const merged = start === undefined || start >= MERGED_SCHEME_START;
  const notifiable = start === undefined || start >= CLAIM_NOTIFICATION_START;
  return {
    companyIsSme: scheme === "rdec" && merged,
    rdecExpenditure: scheme === "sme",
    intensity: scheme === "sme" || scheme === "eris",
    payableCredit: scheme === "sme" || scheme === "eris",
    workersPayeAndNic: scheme === "rdec" && !merged,
    notification: notifiable && values.claimed_in_previous_three_years === "no",
  };
}

const PERCENT = /^[0-9]{1,3}(?:\.[0-9]{1,2})?$/;

/** A percentage from 0 to 100 with up to 2 decimal places, like 35 or 12.5. */
export function parsePercent(raw: string, label: string, required: boolean): Parsed<string | null> {
  const cleaned = raw.trim().replace(/%$/, "");
  if (cleaned === "")
    return required ? { ok: false, error: `Enter ${label}` } : { ok: true, value: null };
  if (!PERCENT.test(cleaned) || Number(cleaned) > 100) {
    return { ok: false, error: `Enter ${label} as a percentage from 0 to 100, like 35` };
  }
  return { ok: true, value: cleaned };
}

function schemeErrors(values: ResearchAnswers, start: string | undefined): FieldErrors {
  const errors: FieldErrors = {};
  if (!values.scheme) errors.scheme = "Select the R&D scheme the company is claiming under";
  else if (!schemesFor(start).includes(values.scheme)) {
    errors.scheme =
      values.scheme === "sme"
        ? "The SME scheme ended for periods starting on or after 1 April 2024: claim merged-scheme RDEC, or ERIS if the company is an R&D-intensive SME"
        : "ERIS is for periods starting on or after 1 April 2024: claim under the SME scheme instead";
  }
  return errors;
}

function formErrors(values: ResearchAnswers, notification: boolean): FieldErrors {
  const errors: FieldErrors = {};
  if (!values.claimed_in_previous_three_years) {
    errors.claimed_in_previous_three_years =
      "Select yes if the company has claimed R&D relief in the last 3 years";
  }
  if (notification && values.claim_notification_submitted !== "yes") {
    errors.claim_notification_submitted =
      values.claim_notification_submitted === "no"
        ? "Submit a claim notification form before you claim: the company has not claimed R&D relief in the last 3 years, so HMRC only accepts the claim if it was notified within 6 months of the period's end"
        : "Select yes if the company submitted a claim notification form";
  }
  if (values.additional_information_submitted !== "yes") {
    errors.additional_information_submitted =
      values.additional_information_submitted === "no"
        ? "Submit the R&D additional information form before you file this return: HMRC removes claims made without it"
        : "Select yes if the company submitted the R&D additional information form";
  }
  return errors;
}

type Amounts = {
  qualifying: Parsed<number>;
  rdec: Parsed<number>;
  intensity: Parsed<string | null>;
  workers: Parsed<number>;
};

function parseAmounts(
  values: ResearchAnswers,
  shown: ReturnType<typeof researchQuestions>,
): Amounts {
  const optional = (raw: string, label: string, asked: boolean) =>
    asked ? parseWholePounds(raw, label) : ({ ok: true, value: 0 } as const);
  return {
    qualifying: parseWholePounds(
      values.qualifying_expenditure,
      "the qualifying R&D expenditure",
      true,
    ),
    rdec: optional(
      values.rdec_expenditure,
      "the expenditure RDEC is claimed on",
      shown.rdecExpenditure,
    ),
    intensity: shown.intensity
      ? parsePercent(values.intensity, "the R&D intensity", values.scheme === "eris")
      : { ok: true, value: null },
    workers: optional(
      values.rd_workers_paye_and_nic,
      "the R&D workers' PAYE and NICs",
      shown.workersPayeAndNic,
    ),
  };
}

function amountErrors(amounts: Amounts, scheme: ResearchAnswers["scheme"]): FieldErrors {
  const errors: FieldErrors = {};
  if (!amounts.qualifying.ok) errors.qualifying_expenditure = amounts.qualifying.error;
  if (!amounts.rdec.ok) errors.rdec_expenditure = amounts.rdec.error;
  if (!amounts.workers.ok) errors.rd_workers_paye_and_nic = amounts.workers.error;
  if (!amounts.intensity.ok) errors.intensity = amounts.intensity.error;
  else if (scheme === "eris" && Number(amounts.intensity.value) < 30) {
    errors.intensity =
      "ERIS needs R&D expenditure of at least 30% of the company's total relevant expenditure: enter the percentage, or claim merged-scheme RDEC";
  }
  return errors;
}

/** Check the R&D claim; ``null`` when the company is not claiming. ``start`` is box 30. */
export function validateResearch(
  values: ResearchAnswers,
  start: string | undefined,
): Validated<ResearchAndDevelopment | null> {
  if (!values.claiming) {
    return { ok: false, errors: { claiming: "Select yes if the company is claiming R&D relief" } };
  }
  if (values.claiming === "no") return { ok: true, value: null };
  const shown = researchQuestions(values, start);
  const amounts = parseAmounts(values, shown);
  const errors: FieldErrors = {
    ...schemeErrors(values, start),
    ...amountErrors(amounts, values.scheme),
    ...formErrors(values, shown.notification),
  };
  if (shown.companyIsSme && !values.company_is_sme) {
    errors.company_is_sme = "Select yes if the company is a small or medium-sized enterprise";
  }
  if (shown.payableCredit && !values.claim_payable_credit) {
    errors.claim_payable_credit = "Select yes if the company is claiming a payable tax credit";
  }
  const { qualifying, rdec, intensity, workers } = amounts;
  if (!values.scheme || !qualifying.ok || !rdec.ok || !intensity.ok || !workers.ok) {
    return { ok: false, errors };
  }
  if (Object.keys(errors).length > 0) return { ok: false, errors };
  return {
    ok: true,
    value: {
      scheme: values.scheme,
      company_is_sme: shown.companyIsSme && values.company_is_sme === "yes",
      qualifying_expenditure: qualifying.value,
      rdec_expenditure: rdec.value,
      intensity: intensity.value,
      claim_payable_credit: shown.payableCredit && values.claim_payable_credit === "yes",
      rd_workers_paye_and_nic: shown.workersPayeAndNic && workers.value > 0 ? workers.value : null,
      claimed_in_previous_three_years: values.claimed_in_previous_three_years === "yes",
      claim_notification_submitted: shown.notification,
      additional_information_submitted: true,
    },
  };
}

/** The three parts of CT600A whose rows each record a loan. */
export type LoanTable = keyof ParticipatorLoanDates;
export type LoanDatesAnswers = Record<LoanTable, DateParts[]>;

export const LOAN_TABLES: { table: LoanTable; group: string; title: string }[] = [
  { table: "loans", group: "LoansInformation", title: "Loans made during the period" },
  {
    table: "repaid_within_nine_months",
    group: "ReliefEarlierThan",
    title: "Loans repaid, released or written off within 9 months of the period end",
  },
  {
    table: "repaid_later",
    group: "LoanLaterReliefNow",
    title: "Loans repaid, released or written off later",
  },
];

/**
 * When the s455 rate on loans to participators changed (backend
 * ``reliefs.loans_to_participators.S455_RATES``): 32.5%, 33.75% and 35.75% from these dates.
 */
export const S455_RATE_CHANGES = ["2016-04-06", "2022-04-06", "2026-04-06"];

/** Loan dates are only needed when the s455 rate changes during the period. */
export function s455RateChanges(period: Period): boolean {
  return S455_RATE_CHANGES.some((date) => period.start < date && date <= period.end);
}

function records(value: JsonValue | undefined): ElementTree[] {
  const items = Array.isArray(value) ? value : value === undefined ? [] : [value];
  return items.filter(
    (item): item is ElementTree =>
      typeof item === "object" && item !== null && !Array.isArray(item),
  );
}

/** The participators named in each part of a CT600A element tree, one per row. */
export function loanRows(ct600a: ElementTree): Record<LoanTable, string[]> {
  const rows = (group: string) =>
    records(records(ct600a[group])[0]?.Loan).map((loan) => String(loan.Name ?? ""));
  return {
    loans: rows("LoansInformation"),
    repaid_within_nine_months: rows("ReliefEarlierThan"),
    repaid_later: rows("LoanLaterReliefNow"),
  };
}

export function loanDateId(table: LoanTable, index: number): string {
  return `${table}-${index}`;
}

/** Check a date for every row of CT600A, each within the accounting period. */
export function validateLoanDates(
  values: LoanDatesAnswers | undefined,
  rows: Record<LoanTable, string[]>,
  period: Period,
): Validated<ParticipatorLoanDates> {
  const errors: FieldErrors = {};
  const dates: ParticipatorLoanDates = {
    loans: [],
    repaid_within_nine_months: [],
    repaid_later: [],
  };
  for (const { table } of LOAN_TABLES) {
    rows[table].forEach((name, index) => {
      const parts = values?.[table][index] ?? { day: "", month: "", year: "" };
      const parsed = parseDateParts(parts, `date the loan to ${name} was made`);
      const key = loanDateId(table, index);
      if (!parsed.ok) errors[key] = parsed.error;
      else if (parsed.value < period.start || parsed.value > period.end) {
        errors[key] = `The date the loan to ${name} was made must be in this accounting period`;
      } else dates[table].push(parsed.value);
    });
  }
  return Object.keys(errors).length > 0 ? { ok: false, errors } : { ok: true, value: dates };
}

/** A surrendering company named on CT600C, by its tax reference. */
export type Surrenderer = { reference: string; name: string };

export type SurrendererFigures = {
  surrenderable_amount: string;
  surrendered_to_others: string;
  consortium_share: string;
};
export type SurrendererAnswers = Record<string, SurrendererFigures>;

/** The companies CT600C claims group relief from, once each (C5 and C125 rows). */
export function surrenderingCompanies(ct600c: ElementTree): Surrenderer[] {
  const claims = ["ClaimToGroupRelief", "GroupReliefForCarriedForwardLosses"];
  const companies = claims.flatMap((claim) =>
    records(records(records(ct600c[claim])[0]?.CompanyInformation)[0]?.Company),
  );
  const found = new Map<string, string>();
  for (const company of companies) {
    const reference = String(company.TaxReference ?? "").trim();
    if (reference && !found.has(reference)) found.set(reference, String(company.Name ?? ""));
  }
  return [...found].map(([reference, name]) => ({ reference, name }));
}

export function surrendererId(index: number, field: keyof SurrendererFigures): string {
  return `surrenderer-${index}-${field}`;
}

function checkSurrenderer(
  figures: SurrendererFigures,
  index: number,
  errors: FieldErrors,
): Omit<SurrenderingCompany, "tax_reference"> | null {
  const given = Object.values(figures).some((value) => value.trim() !== "");
  if (!given) return null;
  const available = parseWholePounds(
    figures.surrenderable_amount,
    "the amount it can surrender",
    true,
  );
  const surrendered = parseWholePounds(
    figures.surrendered_to_others,
    "the amount already surrendered",
  );
  const share = parsePercent(figures.consortium_share, "the consortium share", false);
  if (!available.ok) errors[surrendererId(index, "surrenderable_amount")] = available.error;
  if (!surrendered.ok) errors[surrendererId(index, "surrendered_to_others")] = surrendered.error;
  if (!share.ok) errors[surrendererId(index, "consortium_share")] = share.error;
  else if (share.value !== null && Number(share.value) === 0) {
    errors[surrendererId(index, "consortium_share")] = "The consortium share must be more than 0%";
  }
  if (!available.ok || !surrendered.ok || !share.ok) return null;
  return {
    surrenderable_amount: available.value,
    surrendered_to_others: surrendered.value,
    consortium_share: share.value,
  };
}

/** Check the figures given for any of CT600C's surrendering companies (all are optional). */
export function validateSurrenderers(
  values: SurrendererAnswers,
  companies: Surrenderer[],
): Validated<SurrenderingCompany[]> {
  const errors: FieldErrors = {};
  const found: SurrenderingCompany[] = [];
  companies.forEach(({ reference }, index) => {
    const figures = values[reference];
    const checked = figures ? checkSurrenderer(figures, index, errors) : null;
    if (checked) found.push({ tax_reference: reference, ...checked });
  });
  return Object.keys(errors).length > 0 ? { ok: false, errors } : { ok: true, value: found };
}

export type CreativeAnswers = { additional_information_submitted: YesNo };

/** CT600P claims need the creatives additional information form before the return (box 658). */
export function validateCreative(
  values: CreativeAnswers,
): Validated<{ additional_information_submitted: true }> {
  const answer = values.additional_information_submitted;
  if (answer === "yes") return { ok: true, value: { additional_information_submitted: true } };
  const error =
    answer === "no"
      ? "Submit the creatives additional information form before you file this return: HMRC rejects creative industries claims made without it"
      : "Select yes if the company submitted the creatives additional information form";
  return { ok: false, errors: { additional_information_submitted: error } };
}
