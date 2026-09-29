/** Typed client for the Open CT600 API. Decimal amounts arrive as strings. */

/** ``fund`` is the authorised investment fund rate (company type 1). */
export type TaxBand = "flat" | "small" | "marginal" | "main" | "fund";

/** A slice's ring fence profits (CT600I), taxed at the ring fence rates. */
export type RingFenceSlice = {
  profits: number;
  rate: string;
  tax: string;
  marginal_relief: string;
};

export type FinancialYearSlice = {
  financial_year: number;
  start: string;
  end: string;
  days: number;
  profits: number;
  augmented_profits: string;
  lower_limit: string;
  upper_limit: string;
  band: TaxBand;
  rate: string;
  tax: string;
  /** Includes the ring fence marginal relief, if any. */
  marginal_relief: string;
  ring_fence: RingFenceSlice | null;
};

export type TaxComputation = {
  period_start: string;
  period_end: string;
  taxable_profits: number;
  augmented_profits: number;
  associated_companies: number;
  slices: FinancialYearSlice[];
  tax_before_relief: string;
  marginal_relief: string;
  tax_chargeable: string;
  effective_rate: string;
  payment_due: string;
  filing_due: string;
  may_pay_by_instalments: boolean;
};

export type BoxKind = "pounds" | "money" | "count" | "rate" | "year" | "flag";

/** A CT600 box: ``box`` is its id on the form, like "145", "80A" or "A80". */
export type CT600Box = { box: string; label: string; value: string; kind: BoxKind };

export type AccountsSummary = {
  turnover: number;
  interest_income: number;
  /** The RDEC and AVEC/VGEC credits the service adds as income; in profit before tax. */
  other_income: number;
  total_expenses: number;
  profit_before_tax: number;
  corporation_tax: string;
  profit_after_tax: string;
  called_up_share_capital_not_paid: number;
  fixed_assets: number;
  current_assets: number;
  prepayments_and_accrued_income: number;
  creditors_within_one_year: number;
  net_current_assets: number;
  total_assets_less_current_liabilities: number;
  creditors_after_one_year: number;
  provisions: number;
  accruals_and_deferred_income: number;
  net_assets: number;
  called_up_share_capital: number;
  profit_and_loss_reserve: number;
};

export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

/**
 * A supplementary page's answers as an element tree: element names as keys, lists for
 * repeating elements, "@Name" for attributes, and every value a string.
 */
export type ElementTree = { [element: string]: JsonValue };

/** A supplementary page code: "A" for CT600A, and so on (there is no O). */
export type PageCode =
  | "A"
  | "B"
  | "C"
  | "D"
  | "E"
  | "F"
  | "G"
  | "H"
  | "I"
  | "J"
  | "K"
  | "L"
  | "M"
  | "N"
  | "P";

export type ResearchAndDevelopmentScheme = "sme" | "large_company_rdec" | "merged_rdec" | "eris";

/**
 * The reliefs and credits claimed through supplementary pages (``null`` when not claimed); see
 * backend ``open_ct600.computation.ReliefsSummary``.
 */
export type ReliefsSummary = {
  group_relief: {
    claimed: number;
    claimed_for_carried_forward_losses: number;
    available: number;
    unused: number;
  } | null;
  research_and_development: {
    scheme: ResearchAndDevelopmentScheme;
    qualifying_expenditure: number;
    additional_deduction: number;
    enhanced_expenditure: number;
    rdec: string;
    notional_tax_rate: string | null;
    set_off: string;
    payable_rdec: string | null;
    payable_credit: string | null;
    credit_claimed: string | null;
    losses_surrendered: number;
    rdec_carried_forward: string;
  } | null;
  loans_to_participators: {
    tax_payable: string;
    relief_for_later_repayments: boolean;
    statutory_tax_payable: string;
    amendment_due: string;
  } | null;
  creative_industries: {
    expenditure_credit: string;
    expenditure_credit_set_off: string | null;
    expenditure_credit_payable: string | null;
    expenditure_credit_carried_forward: string;
    additional_deduction: number;
    tax_credit: string;
    tax_credit_set_off: string | null;
    tax_credit_payable: string | null;
    losses_surrendered: number;
  } | null;
};

export type ReturnComputation = {
  boxes: CT600Box[];
  tax: TaxComputation;
  accounts: AccountsSummary;
  trading_loss_arising: number;
  losses_carried_forward: number;
  pages: Partial<Record<PageCode, ElementTree>>;
  reliefs?: ReliefsSummary;
};

export type CompanyDetails = {
  name: string;
  registration_number: string;
  utr: string;
  /** CT600 box 4: 0 is a UK trading company (or any company not otherwise listed). */
  company_type: number;
  principal_activity: string;
};

export type TradingStatus = "trading" | "never_traded" | "no_longer_trading";

export type AccountsDetails = {
  standard: "micro" | "small";
  approval_date: string;
  directors: string[];
  signing_director: string;
  average_employees: number;
  trading_status: TradingStatus;
  /** Dormant throughout the period: no turnover, expenses, income or gains, and not trading. */
  dormant: boolean;
  /** Last period's figures, shown beside this period's; null (or absent) for the first period. */
  comparatives?: Comparatives | null;
  /** Defaults to ``private-limited-company`` when absent. */
  legal_form?: LegalForm;
};

/** The legal forms the accounts can be prepared for (FRC ``LegalFormEntityDimension`` members). */
export type LegalForm =
  | "private-limited-company"
  | "private-company-limited-by-guarantee"
  | "private-unlimited-company"
  | "community-interest-company";

/** The previous period of account (up to 18 months, ending the day before this one starts). */
export type Comparatives = {
  period: { start: string; end: string };
  profit_and_loss: CT600Return["profit_and_loss"];
  balance_sheet: CT600Return["balance_sheet"];
  /**
   * The previous period's tax line in its profit and loss account, in whole pounds: a charge,
   * or a credit (e.g. from R&D tax credits) as a negative amount.
   */
  tax_on_profit: number;
  /** The previous period's average number of employees; null only when it is not known. */
  average_employees: number | null;
};

/** One company found by ``GET /api/companies-house/search``, named as Companies House does. */
export type CompanySearchResult = {
  number: string;
  name: string;
  status: string;
  address: string;
  incorporated_on: string | null;
};

/** The accounts the company last filed at Companies House, read from their iXBRL. */
export type PreviousAccounts = {
  period: { start: string; end: string };
  filed_on: string;
  standard: "micro" | "small" | null;
  dormant: boolean | null;
  /** ``ProfitAndLoss`` fields, plus ``tax`` and ``profit_after_tax`` for reference. */
  profit_and_loss: Record<string, number>;
  /** ``BalanceSheet`` fields, plus ``net_assets`` for reference. */
  balance_sheet: Record<string, number>;
  average_employees: number | null;
  directors: string[];
  principal_activity: string | null;
};

/** A company's public record from ``GET /api/companies-house/companies/{number}``. */
export type CompanyRecord = {
  number: string;
  name: string;
  status: string;
  incorporated_on: string | null;
  /** Companies House's legal form, which may be one this service does not support. */
  legal_form: string | null;
  registered_office: { lines: string[]; postcode: string | null };
  sic_codes: { code: string; description: string }[];
  principal_activity: string | null;
  /** Current directors, in Companies House's display order. */
  directors: { name: string; appointed_on: string | null }[];
  accounts: {
    reference_date: string | null;
    last_made_up_to: string | null;
    next_period: { start: string; end: string } | null;
  };
  /** The return's period: the first 12 months of the next period of account. */
  suggested_period: { start: string; end: string; note: string | null } | null;
  previous_accounts: PreviousAccounts | null;
  /** Why no previous figures could be read, such as accounts filed on paper. */
  previous_accounts_unavailable: string | null;
};

/** ``sme`` and ``rdec`` (large companies) before 1 April 2024; ``rdec`` (merged) and ``eris`` after. */
export type ResearchAndDevelopmentClaimScheme = "sme" | "rdec" | "eris";

/** The R&D claim's answers that CT600L has no box for; see backend ``reliefs.research_and_development``. */
export type ResearchAndDevelopment = {
  scheme: ResearchAndDevelopmentClaimScheme;
  company_is_sme: boolean;
  qualifying_expenditure: number;
  rdec_expenditure: number;
  intensity: string | null;
  claim_payable_credit: boolean;
  rd_workers_paye_and_nic: number | null;
  claimed_in_previous_three_years: boolean;
  claim_notification_submitted: boolean;
  additional_information_submitted: boolean;
};

/** Figures from a group relief surrendering company's own return (CT600C). */
export type SurrenderingCompany = {
  tax_reference: string;
  surrenderable_amount: number;
  surrendered_to_others: number;
  consortium_share: string | null;
};

/** When each loan on CT600A was made, one ISO date per row of each part, in order. */
export type ParticipatorLoanDates = {
  loans: string[];
  repaid_within_nine_months: string[];
  repaid_later: string[];
};

/** How a schema node's value is entered; see backend ``open_ct600.schema.spec.Kind``. */
export type SpecKind =
  | "group"
  | "any"
  | "pounds"
  | "money"
  | "integer"
  | "decimal"
  | "percent"
  | "date"
  | "year"
  | "yes"
  | "yesno"
  | "text"
  | "enum"
  | "binary";

/** One element (or "@attribute") of HMRC's CT600 schema, from ``GET /api/schema/pages``. */
export type SpecNode = {
  name: string;
  path: string;
  box: string | null;
  label: string;
  kind: SpecKind;
  min: number;
  max: number | null;
  choice: string | null;
  branch: string | null;
  enum: { value: string; label: string }[] | null;
  patterns: string[];
  minLength: number | null;
  maxLength: number | null;
  minValue: number | string | null;
  maxValue: number | string | null;
  choices: { id: string; min: number }[];
  children: SpecNode[];
  /**
   * The service works this element out (a total, a tax at a rate), so the user is not asked.
   * Set by the frontend from ``SchemaPage.computed``.
   */
  computed?: boolean;
};

export type SchemaPage = {
  code: PageCode;
  element: string;
  title: string;
  dormant: boolean;
  node: SpecNode;
  /**
   * The box ids the service calculates; a group whose every box is calculated is calculated
   * as a whole. Answers must leave them out.
   */
  computed: string[];
};

export type CT600Return = {
  company: CompanyDetails;
  period: { start: string; end: string };
  profit_and_loss: {
    turnover: number;
    interest_income: number;
    cost_of_sales: number;
    staff_costs: number;
    depreciation: number;
    other_expenses: number;
  };
  tax_adjustments: {
    disallowable_expenses: number;
    capital_allowances: number;
    losses_brought_forward: number;
    /** The part of ``losses_brought_forward`` that arose before 1 April 2017. */
    losses_brought_forward_before_april_2017: number;
    chargeable_gains: number;
    qualifying_donations: number;
    exempt_distributions: number;
    associated_companies: number;
  };
  balance_sheet: {
    called_up_share_capital_not_paid: number;
    fixed_assets: number;
    current_assets: number;
    prepayments_and_accrued_income: number;
    creditors_within_one_year: number;
    creditors_after_one_year: number;
    provisions: number;
    accruals_and_deferred_income: number;
    called_up_share_capital: number;
  };
  accounts: AccountsDetails;
  supplementary_pages?: Partial<Record<PageCode, ElementTree>>;
  research_and_development?: ResearchAndDevelopment | null;
  group_relief_surrenderers?: SurrenderingCompany[];
  participator_loan_dates?: ParticipatorLoanDates | null;
  creative_industries?: { additional_information_submitted: boolean } | null;
};

export type SignatoryCapacity = "director" | "company_secretary" | "authorised_agent";

export type Declaration = { name: string; capacity: SignatoryCapacity; confirmed: true };

/** The receipt for a demonstration submission: nothing is sent to HMRC. */
export type SubmissionReceipt = {
  reference: string;
  received_at: string;
  fingerprint: string;
  company: CompanyDetails;
  signatory: string;
  computation: ReturnComputation;
};

/** Where a real submission goes: HMRC's live service, or Test in Live (real data, no filing). */
export type HmrcEnvironment = "live" | "test-in-live";

export type HmrcSubmission = {
  ct600: CT600Return;
  declaration: Declaration;
  environment: HmrcEnvironment;
  gateway_user_id: string;
  gateway_password: string;
};

/**
 * HMRC accepted the return. ``irmark`` is HMRC's digest in Base64 and ``irmark_base32`` the form
 * HMRC quotes on its receipt; ``receipt_xml`` is HMRC's signed response, for the company's records.
 */
export type HmrcReceipt = {
  environment: HmrcEnvironment;
  correlation_id: string;
  irmark: string | null;
  irmark_base32: string;
  accepted_time: string | null;
  messages: string[];
  receipt_xml: string;
};

/**
 * One reason HMRC rejects (or would reject) a return: HMRC's error code and message, the
 * CT600 box and supplementary page where there is one, and where HMRC places the fault, like
 * ``/IRenvelope/CompanyTaxReturn/LoansByCloseCompanies/LoansInformation/Loan[2]/Name``.
 */
export type HmrcProblem = {
  code: number | null;
  message: string;
  box: string | null;
  page: PageCode | null;
  path: string | null;
};

export type ValidationResult = {
  valid: boolean;
  documents_attached: boolean;
  problems: HmrcProblem[];
};

/** An error as HMRC's Transaction Engine reports it, before it becomes an ``HmrcProblem``. */
type HmrcError = {
  number: number | null;
  type: string;
  message: string;
  box: string | null;
  page: PageCode | null;
  location: string | null;
};

export type HmrcOutcome =
  | ({ status: "accepted" } & HmrcReceipt)
  | {
      status: "rejected";
      environment: HmrcEnvironment;
      correlation_id: string;
      problems: HmrcProblem[];
    };

type HmrcReply =
  | ({ status: "accepted" } & HmrcReceipt)
  | {
      status: "rejected";
      environment: HmrcEnvironment;
      correlation_id: string;
      errors: HmrcError[];
    };

function fromHmrcError(error: HmrcError): HmrcProblem {
  const { number, message, box, page, location } = error;
  return { code: number, message, box, page, path: location };
}

/**
 * The typed ``detail.error`` codes the submission routes give, among others:
 *
 * - ``submission_disabled``: this deployment has no HMRC vendor ID or has not enabled submission
 * - ``authentication_failed``: HMRC refused the Government Gateway user ID or password
 * - ``invalid_return``: HMRC's rules reject the return; nothing was sent
 * - ``hmrc_timeout``: HMRC has not answered yet; the return may still be accepted
 */
export type ErrorCode =
  | "submission_disabled"
  | "authentication_failed"
  | "invalid_return"
  | "hmrc_timeout";

export type CalculatorRequest = {
  period_start: string;
  period_end: string;
  taxable_profits: number;
  associated_companies: number;
};

/** A problem with one input, located by its path in the request body. */
export type FieldProblem = { path: string[]; message: string };

type ErrorDetails = {
  problems?: FieldProblem[];
  code?: string | null;
  correlationId?: string | null;
  hmrcErrors?: HmrcProblem[];
};

export class ApiError extends Error {
  readonly status: number;
  readonly problems: FieldProblem[];
  /** The typed error code, when the service gave one. */
  readonly code: string | null;
  /** HMRC's identifier for the submission, when it has one. */
  readonly correlationId: string | null;
  readonly hmrcErrors: HmrcProblem[];

  constructor(status: number, message: string, details: ErrorDetails = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.problems = details.problems ?? [];
    this.code = details.code ?? null;
    this.correlationId = details.correlationId ?? null;
    this.hmrcErrors = details.hmrcErrors ?? [];
  }
}

type ValidationDetail = { loc: (string | number)[]; msg: string };

/** ``errors`` are ``HmrcProblem``s for ``invalid_return`` and HMRC's own errors otherwise. */
type TypedDetail = {
  error: string;
  message: string;
  correlation_id?: string | null;
  errors?: (HmrcProblem | HmrcError)[];
};

function toProblems(detail: ValidationDetail[]): FieldProblem[] {
  return detail.map((item) => ({
    path: item.loc.slice(1).map(String),
    message: item.msg.replace(/^Value error, /, ""),
  }));
}

function isTypedDetail(detail: unknown): detail is TypedDetail {
  if (typeof detail !== "object" || detail === null) return false;
  const candidate = detail as Record<string, unknown>;
  return typeof candidate.error === "string" && typeof candidate.message === "string";
}

function toHmrcProblem(error: HmrcProblem | HmrcError): HmrcProblem {
  return "number" in error ? fromHmrcError(error) : error;
}

function toApiError(status: number, payload: unknown): ApiError {
  const detail = (payload as { detail?: unknown } | null)?.detail;
  if (status === 422 && Array.isArray(detail)) {
    const problems = toProblems(detail as ValidationDetail[]);
    return new ApiError(422, problems[0]?.message ?? "Check your answers", { problems });
  }
  if (isTypedDetail(detail)) {
    return new ApiError(status, detail.message, {
      code: detail.error,
      correlationId: detail.correlation_id ?? null,
      hmrcErrors: (detail.errors ?? []).map(toHmrcProblem),
    });
  }
  const message = typeof detail === "string" ? detail : `The service returned ${status}`;
  return new ApiError(status, message);
}

function jsonRequest(body: unknown): RequestInit {
  return {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

async function request(path: string, init?: RequestInit): Promise<Response> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, init);
  } catch (error) {
    throw new ApiError(0, `Could not reach the Open CT600 service: ${String(error)}`);
  }
  if (response.ok) return response;
  const payload: unknown = await response.json().catch(() => null);
  throw toApiError(response.status, payload);
}

async function send<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await request(path, init);
  return (await response.json()) as T;
}

function post<T>(path: string, body: unknown): Promise<T> {
  return send<T>(path, jsonRequest(body));
}

/** A document the service generates from the return. */
export type ReturnDocument = "accounts" | "computations" | "ct600";

/** Where each document comes from, and the file name to use if the service gives none. */
const DOCUMENTS: Record<ReturnDocument, { path: string; filename: string }> = {
  accounts: { path: "/returns/accounts.xhtml", filename: "accounts.xhtml" },
  computations: { path: "/returns/computations.xhtml", filename: "computations.xhtml" },
  ct600: { path: "/returns/ct600.xml", filename: "ct600.xml" },
};

const FILENAME = /filename="?(?<name>[^";]+)"?/;

/** Every route that works on a whole return (downloads and validation) takes ``{ct600}``. */
async function download(document: ReturnDocument, ct600: CT600Return) {
  const { path, filename } = DOCUMENTS[document];
  const response = await request(path, jsonRequest({ ct600 }));
  const disposition = response.headers.get("Content-Disposition") ?? "";
  const named = FILENAME.exec(disposition)?.groups?.name;
  return { blob: await response.blob(), filename: named ?? filename };
}

/**
 * Whether this deployment can send returns to HMRC, and to which of its services
 * (``GET /api/submission``: ``{"enabled", "environments"}``). Nothing that asks for Government
 * Gateway credentials is shown unless it can.
 */
export type SubmissionStatus = { enabled: boolean; environments: HmrcEnvironment[] };

const HMRC_ENVIRONMENTS: HmrcEnvironment[] = ["test-in-live", "live"];

async function submissionStatus(): Promise<SubmissionStatus> {
  const reply = await send<unknown>("/submission");
  const status =
    typeof reply === "object" && reply !== null ? (reply as Record<string, unknown>) : {};
  const listed: unknown[] = Array.isArray(status.environments) ? status.environments : [];
  const environments = HMRC_ENVIRONMENTS.filter((environment) => listed.includes(environment));
  return { enabled: status.enabled === true && environments.length > 0, environments };
}

async function submitToHmrc(submission: HmrcSubmission): Promise<HmrcOutcome> {
  const reply = await post<HmrcReply>("/returns/submit-to-hmrc", submission);
  if (reply.status === "accepted") return reply;
  const { environment, correlation_id: correlationId, errors } = reply;
  return {
    status: "rejected",
    environment,
    correlation_id: correlationId,
    problems: errors.map(fromHmrcError),
  };
}

/** Whether Companies House lookup is switched on; off if the service cannot say. */
async function companiesHouseEnabled(): Promise<boolean> {
  const reply = await send<unknown>("/companies-house/status");
  return (
    typeof reply === "object" && reply !== null && (reply as { enabled?: unknown }).enabled === true
  );
}

async function searchCompanies(query: string): Promise<CompanySearchResult[]> {
  const params = new URLSearchParams({ q: query });
  const reply = await send<{ items: CompanySearchResult[] }>(`/companies-house/search?${params}`);
  return reply.items;
}

export const api = {
  companiesHouseEnabled,
  searchCompanies,
  company: (number: string) =>
    send<CompanyRecord>(`/companies-house/companies/${encodeURIComponent(number)}`),
  calculate: (body: CalculatorRequest) => post<TaxComputation>("/calculator", body),
  computeReturn: (ct600: CT600Return) => post<ReturnComputation>("/returns/compute", ct600),
  validateReturn: (ct600: CT600Return) => post<ValidationResult>("/returns/validate", { ct600 }),
  download,
  submitReturn: (ct600: CT600Return, declaration: Declaration) =>
    post<SubmissionReceipt>("/returns/submit", { ct600, declaration }),
  submitToHmrc,
  schemaPages: () => send<SchemaPage[]>("/schema/pages"),
  submissionStatus,
};
