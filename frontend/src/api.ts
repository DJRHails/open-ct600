/** Typed client for the Open CT600 API. Decimal amounts arrive as strings. */

export type TaxBand = "flat" | "small" | "marginal" | "main";

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
  marginal_relief: string;
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

export type ReturnComputation = {
  boxes: CT600Box[];
  tax: TaxComputation;
  accounts: AccountsSummary;
  trading_loss_arising: number;
  losses_carried_forward: number;
  pages: Partial<Record<PageCode, ElementTree>>;
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
};

export type SchemaPage = {
  code: PageCode;
  element: string;
  title: string;
  dormant: boolean;
  node: SpecNode;
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
};

export type SignatoryCapacity = "director" | "company_secretary" | "authorised_agent";

export type Declaration = { name: string; capacity: SignatoryCapacity; confirmed: true };

export type SubmissionReceipt = {
  reference: string;
  received_at: string;
  fingerprint: string;
  company: CompanyDetails;
  signatory: string;
  computation: ReturnComputation;
};

export type CalculatorRequest = {
  period_start: string;
  period_end: string;
  taxable_profits: number;
  associated_companies: number;
};

/** A problem with one input, located by its path in the request body. */
export type FieldProblem = { path: string[]; message: string };

export class ApiError extends Error {
  readonly status: number;
  readonly problems: FieldProblem[];

  constructor(status: number, message: string, problems: FieldProblem[] = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.problems = problems;
  }
}

type ValidationDetail = { loc: (string | number)[]; msg: string };

function toProblems(detail: ValidationDetail[]): FieldProblem[] {
  return detail.map((item) => ({
    path: item.loc.slice(1).map(String),
    message: item.msg.replace(/^Value error, /, ""),
  }));
}

function post<T>(path: string, body: unknown): Promise<T> {
  return send<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

async function send<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, init);
  } catch (error) {
    throw new ApiError(0, `Could not reach the Open CT600 service: ${String(error)}`);
  }
  const payload: unknown = await response.json().catch(() => null);
  if (response.ok) return payload as T;

  const detail = (payload as { detail?: unknown } | null)?.detail;
  if (response.status === 422 && Array.isArray(detail)) {
    const problems = toProblems(detail as ValidationDetail[]);
    throw new ApiError(422, problems[0]?.message ?? "Check your answers", problems);
  }
  const message = typeof detail === "string" ? detail : `The service returned ${response.status}`;
  throw new ApiError(response.status, message);
}

export const api = {
  calculate: (request: CalculatorRequest) => post<TaxComputation>("/calculator", request),
  computeReturn: (ct600: CT600Return) => post<ReturnComputation>("/returns/compute", ct600),
  submitReturn: (ct600: CT600Return, declaration: Declaration) =>
    post<SubmissionReceipt>("/returns/submit", { ct600, declaration }),
  schemaPages: () => send<SchemaPage[]>("/schema/pages"),
};
