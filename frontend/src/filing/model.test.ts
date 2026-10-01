import {
  COMPANY_TYPES,
  completedCount,
  EMPTY_ACCOUNTS,
  sectionComplete,
  validateAccounts,
  validateCompany,
  validateAmounts,
  validatePeriod,
  type Draft,
  TAX_ADJUSTMENTS,
} from "@/filing/model";
import { toReturn } from "@/filing/payload";
import { EMPTY_RESEARCH } from "@/filing/reliefs";

const COMPANY = {
  name: " Acme Widgets Ltd ",
  registration_number: "sc 123456",
  utr: "12345 67890",
  company_type: "0",
  principal_activity: " Software development ",
};

const ACCOUNTS = {
  standard: "micro" as const,
  directors: ["Ada Lovelace", " Charles Babbage "],
  signing_director: "Ada Lovelace",
  approval_date: { day: "30", month: "6", year: "2025" },
  average_employees: "2",
  trading_status: "trading" as const,
  dormant: "no" as const,
  legal_form: "private-limited-company" as const,
  first_period: "yes" as const,
};

const COMPLETE = {
  company: COMPANY,
  period: {
    start: { day: "1", month: "4", year: "2024" },
    end: { day: "31", month: "3", year: "2025" },
  },
  profit_and_loss: { turnover: "120,000", staff_costs: "30000" },
  tax_adjustments: { associated_companies: "1" },
  balance_sheet: { prepayments_and_accrued_income: "1,000", provisions: "500" },
  accounts: ACCOUNTS,
  chosen_pages: [],
  research_and_development: { ...EMPTY_RESEARCH, claiming: "no" },
} satisfies Draft;

describe("COMPANY_TYPES", () => {
  it("uses HMRC's box 4 codes and offers only the types the service can tax", () => {
    const labels = Object.fromEntries(COMPANY_TYPES.map((type) => [type.value, type.label]));

    expect(labels["2"]).toBe("Close investment-holding company");
    expect(Object.keys(labels)).toEqual(["0", "1", "2", "3", "4", "6", "7", "8", "9", "11"]);
    expect(COMPANY_TYPES[0]?.hint).toMatch(/community interest companies/);
  });

  it.each(["5", "10"])("refuses unsupported type %s", (code) => {
    const result = validateCompany({ ...COMPANY, company_type: code });

    expect(!result.ok && result.errors.company_type).toBe("Select the type of company");
  });
});

describe("validateCompany", () => {
  it("normalises identifiers and reads the company type code", () => {
    expect(validateCompany({ ...COMPANY, company_type: "8" })).toEqual({
      ok: true,
      value: {
        name: "Acme Widgets Ltd",
        registration_number: "SC123456",
        utr: "1234567890",
        company_type: 8,
        principal_activity: "Software development",
      },
    });
  });

  it("explains every problem", () => {
    const result = validateCompany({
      name: "",
      registration_number: "123",
      utr: "abc",
      company_type: "12",
      principal_activity: "",
    });

    expect(result).toEqual({
      ok: false,
      errors: {
        name: "Enter the company name",
        registration_number:
          "Enter a company registration number in the correct format, like 01234567 or SC123456",
        utr: "Enter a Unique Taxpayer Reference in the correct format, like 1234567890",
        company_type: "Select the type of company",
        principal_activity: "Enter what the company does",
      },
    });
  });
});

describe("validatePeriod", () => {
  it("rejects a period longer than 12 months", () => {
    const result = validatePeriod({
      start: { day: "1", month: "4", year: "2024" },
      end: { day: "1", month: "4", year: "2025" },
    });

    expect(result.ok).toBe(false);
    expect(!result.ok && result.errors.end).toMatch(/within 12 months/);
    expect(!result.ok && result.errors.end).not.toMatch(/Split/);
  });

  it("rejects an end date before the start date", () => {
    const result = validatePeriod({
      start: { day: "1", month: "4", year: "2024" },
      end: { day: "31", month: "3", year: "2024" },
    });

    expect(!result.ok && result.errors.end).toBe(
      "End date must be the same as or after the start date",
    );
  });
});

describe("validateAccounts", () => {
  it("builds the accounts details, trimming names", () => {
    expect(validateAccounts(ACCOUNTS, "2025-03-31")).toEqual({
      ok: true,
      value: {
        standard: "micro",
        approval_date: "2025-06-30",
        directors: ["Ada Lovelace", "Charles Babbage"],
        signing_director: "Ada Lovelace",
        average_employees: 2,
        trading_status: "trading",
        dormant: false,
        legal_form: "private-limited-company",
      },
    });
  });

  it("explains every problem with an empty answer", () => {
    const result = validateAccounts(EMPTY_ACCOUNTS);

    expect(result).toEqual({
      ok: false,
      errors: {
        "directors-0": "Enter the name of director 1",
        standard: "Select how the accounts were prepared",
        signing_director: "Select the director who signed the accounts",
        approval_date: "Enter the date the accounts were approved",
        average_employees: "Enter the average number of employees",
        dormant: "Select yes if the company was dormant during this period",
        legal_form: "Select the company’s legal form",
        first_period: "Select yes if this is the company’s first period of account",
        trading_status: "Select whether the company traded",
      },
    });
  });

  it("treats an answer that is not one of the choices as not answered", () => {
    const result = validateAccounts({
      ...ACCOUNTS,
      standard: "bogus",
      trading_status: "x",
      dormant: "maybe",
      legal_form: "plc",
      first_period: "sometimes",
    } as unknown as typeof ACCOUNTS);

    expect(result).toEqual({
      ok: false,
      errors: {
        standard: "Select how the accounts were prepared",
        dormant: "Select yes if the company was dormant during this period",
        legal_form: "Select the company’s legal form",
        first_period: "Select yes if this is the company’s first period of account",
        trading_status: "Select whether the company traded",
      },
    });
  });

  it("does not let a dormant company be trading", () => {
    const dormantTrading = validateAccounts({ ...ACCOUNTS, dormant: "yes" });
    const dormantStopped = validateAccounts({
      ...ACCOUNTS,
      dormant: "yes",
      trading_status: "no_longer_trading",
    });

    expect(!dormantTrading.ok && dormantTrading.errors.trading_status).toMatch(
      /^A dormant company cannot be trading/,
    );
    expect(dormantStopped.ok && dormantStopped.value.dormant).toBe(true);
  });

  it("rejects a director listed twice", () => {
    const result = validateAccounts({ ...ACCOUNTS, directors: ["Ada Lovelace", "ada lovelace"] });

    expect(!result.ok && result.errors["directors-1"]).toBe("ada lovelace is already listed");
  });

  it("needs the signing director to be one of the directors", () => {
    const result = validateAccounts({ ...ACCOUNTS, signing_director: "Grace Hopper" });

    expect(!result.ok && result.errors.signing_director).toBe(
      "Select the director who signed the accounts",
    );
  });

  it("needs the accounts approved after the period ends", () => {
    const approvedOnLastDay = { day: "31", month: "3", year: "2025" };
    const result = validateAccounts(
      { ...ACCOUNTS, approval_date: approvedOnLastDay },
      "2025-03-31",
    );

    expect(!result.ok && result.errors.approval_date).toMatch(/after the end of the accounting/);
  });
});

describe("trading losses brought forward from before 1 April 2017", () => {
  const PRE_2017 = "losses_brought_forward_before_april_2017";
  const CLAIMS_CARRIED_FORWARD_GROUP_RELIEF: Draft = {
    chosen_pages: ["C"],
    supplementary_pages: {
      C: {
        GroupAndConsortium: {
          GroupReliefForCarriedForwardLosses: {
            CompanyInformation: {
              Company: [{ Name: "Sub Ltd", TaxReference: "9876543210", AmountClaimed: "5000" }],
            },
          },
        },
      },
    },
  };

  it("are part of the trading losses brought forward", () => {
    const result = validateAmounts(TAX_ADJUSTMENTS, {
      losses_brought_forward: "10,000",
      [PRE_2017]: "12,000",
    });
    const within = validateAmounts(TAX_ADJUSTMENTS, {
      losses_brought_forward: "10,000",
      [PRE_2017]: "4,000",
    });

    expect(!result.ok && result.errors[PRE_2017]).toBe(
      "Losses from before 1 April 2017 are part of the trading losses brought forward, so cannot be more than them",
    );
    expect(within.ok && within.value[PRE_2017]).toBe(4_000);
  });

  it("are not asked, and are nil, without losses brought forward or a claim for them", () => {
    const result = validateAmounts(TAX_ADJUSTMENTS, { [PRE_2017]: "500" });

    expect(result.ok && result.value[PRE_2017]).toBe(0);
  });

  it("must be answered when the company claims group relief for carried-forward losses", () => {
    const values = { losses_brought_forward: "20,000" };
    const blank = validateAmounts(TAX_ADJUSTMENTS, values, CLAIMS_CARRIED_FORWARD_GROUP_RELIEF);
    const nil = validateAmounts(
      TAX_ADJUSTMENTS,
      { ...values, [PRE_2017]: "0" },
      CLAIMS_CARRIED_FORWARD_GROUP_RELIEF,
    );

    expect(!blank.ok && blank.errors[PRE_2017]).toBe(
      "Enter how much of the trading losses brought forward arose before 1 April 2017, or 0 if none",
    );
    expect(nil.ok).toBe(true);
    expect(validateAmounts(TAX_ADJUSTMENTS, values).ok).toBe(true);
    const savedBeforeTheClaim = { ...CLAIMS_CARRIED_FORWARD_GROUP_RELIEF, tax_adjustments: values };
    expect(sectionComplete(savedBeforeTheClaim, "tax_adjustments")).toBe(false);
  });
});

describe("toReturn", () => {
  it("is null until every section is complete", () => {
    const { accounts: _, ...withoutAccounts } = COMPLETE;

    expect(toReturn(withoutAccounts)).toBeNull();
    expect(completedCount(withoutAccounts)).toBe(5);
  });

  it("is null until the user says which supplementary pages apply", () => {
    const { chosen_pages: _, ...unanswered } = COMPLETE;

    expect(toReturn(unanswered)).toBeNull();
  });

  it("is null until the user says whether the company claims R&D relief", () => {
    const { research_and_development: _, ...unanswered } = COMPLETE;

    expect(toReturn(unanswered)).toBeNull();
  });

  it("builds the full API payload, treating blank amounts as zero", () => {
    expect(toReturn(COMPLETE)).toEqual({
      company: {
        name: "Acme Widgets Ltd",
        registration_number: "SC123456",
        utr: "1234567890",
        company_type: 0,
        principal_activity: "Software development",
      },
      period: { start: "2024-04-01", end: "2025-03-31" },
      profit_and_loss: {
        turnover: 120_000,
        interest_income: 0,
        cost_of_sales: 0,
        staff_costs: 30_000,
        depreciation: 0,
        other_expenses: 0,
      },
      tax_adjustments: {
        disallowable_expenses: 0,
        capital_allowances: 0,
        losses_brought_forward: 0,
        losses_brought_forward_before_april_2017: 0,
        chargeable_gains: 0,
        qualifying_donations: 0,
        exempt_distributions: 0,
        associated_companies: 1,
      },
      balance_sheet: {
        called_up_share_capital_not_paid: 0,
        fixed_assets: 0,
        current_assets: 0,
        prepayments_and_accrued_income: 1_000,
        creditors_within_one_year: 0,
        creditors_after_one_year: 0,
        provisions: 500,
        accruals_and_deferred_income: 0,
        called_up_share_capital: 0,
      },
      accounts: {
        standard: "micro",
        approval_date: "2025-06-30",
        directors: ["Ada Lovelace", "Charles Babbage"],
        signing_director: "Ada Lovelace",
        average_employees: 2,
        trading_status: "trading",
        dormant: false,
        legal_form: "private-limited-company",
        comparatives: null,
      },
      supplementary_pages: {},
      research_and_development: null,
      participator_loan_dates: null,
      group_relief_surrenderers: [],
      creative_industries: null,
      repayment: null,
    });
  });

  it("treats a section saved before its questions changed as incomplete", () => {
    const { company_type: _, principal_activity: __, ...oldCompany } = COMPANY;
    const saved = { ...COMPLETE, company: oldCompany } as unknown as Draft;

    expect(sectionComplete(saved, "company")).toBe(false);
    expect(toReturn(saved)).toBeNull();
  });
});
