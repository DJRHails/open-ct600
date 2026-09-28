import { toReturn, validateCompany, validatePeriod, type Draft } from "@/filing/model";

const COMPLETE = {
  company: { name: " Acme Widgets Ltd ", registration_number: "sc 123456", utr: "12345 67890" },
  period: {
    start: { day: "1", month: "4", year: "2024" },
    end: { day: "31", month: "3", year: "2025" },
  },
  profit_and_loss: { turnover: "120,000", staff_costs: "30000" },
  tax_adjustments: { associated_companies: "1" },
  balance_sheet: {},
} satisfies Draft;

describe("validateCompany", () => {
  it("normalises identifiers", () => {
    expect(validateCompany(COMPLETE.company)).toEqual({
      ok: true,
      value: { name: "Acme Widgets Ltd", registration_number: "SC123456", utr: "1234567890" },
    });
  });

  it("explains every problem", () => {
    const result = validateCompany({ name: "", registration_number: "123", utr: "abc" });

    expect(result).toEqual({
      ok: false,
      errors: {
        name: "Enter the company name",
        registration_number:
          "Enter a company registration number in the correct format, like 01234567 or SC123456",
        utr: "Enter a Unique Taxpayer Reference in the correct format, like 1234567890",
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

describe("toReturn", () => {
  it("is null until every section is complete", () => {
    expect(
      toReturn({
        company: COMPLETE.company,
        period: COMPLETE.period,
        profit_and_loss: COMPLETE.profit_and_loss,
        tax_adjustments: COMPLETE.tax_adjustments,
      }),
    ).toBeNull();
  });

  it("builds the full API payload, treating blank amounts as zero", () => {
    expect(toReturn(COMPLETE)).toEqual({
      company: { name: "Acme Widgets Ltd", registration_number: "SC123456", utr: "1234567890" },
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
        chargeable_gains: 0,
        qualifying_donations: 0,
        exempt_distributions: 0,
        associated_companies: 1,
      },
      balance_sheet: {
        fixed_assets: 0,
        current_assets: 0,
        creditors_within_one_year: 0,
        creditors_after_one_year: 0,
        called_up_share_capital: 0,
      },
    });
  });
});
