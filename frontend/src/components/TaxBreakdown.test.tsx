import { render, screen, within } from "@testing-library/react";

import type { AccountsSummary, FinancialYearSlice, TaxComputation } from "@/api";
import { TaxBreakdownTable } from "@/components/TaxBreakdown";
import { AccountsTables } from "@/filing/ReturnViews";

const SLICE: FinancialYearSlice = {
  financial_year: 2024,
  start: "2024-04-01",
  end: "2025-03-31",
  days: 365,
  profits: 100_000,
  augmented_profits: "100000.00",
  lower_limit: "50000.00",
  upper_limit: "250000.00",
  band: "main",
  rate: "0.25",
  tax: "25000.00",
  marginal_relief: "0.00",
  ring_fence: null,
};

function tax(slice: FinancialYearSlice): TaxComputation {
  return {
    period_start: "2024-04-01",
    period_end: "2025-03-31",
    taxable_profits: 100_000,
    augmented_profits: 100_000,
    associated_companies: 0,
    slices: [slice],
    tax_before_relief: "25000.00",
    marginal_relief: "0.00",
    tax_chargeable: "25000.00",
    effective_rate: "0.25",
    payment_due: "2026-01-01",
    filing_due: "2026-03-31",
    may_pay_by_instalments: false,
  };
}

describe("the tax breakdown", () => {
  it("names the authorised investment fund rate", () => {
    render(
      <TaxBreakdownTable tax={tax({ ...SLICE, band: "fund", rate: "0.20", tax: "20000.00" })} />,
    );

    expect(screen.getByText(/^Authorised investment fund rate \(20%\)/)).toBeInTheDocument();
    expect(screen.queryByText(/undefined/)).toBeNull();
  });

  it("shows ring fence profits on their own line at the ring fence rate", () => {
    const ringFence = { profits: 50_000, rate: "0.30", tax: "15000.00", marginal_relief: "0.00" };
    render(<TaxBreakdownTable tax={tax({ ...SLICE, ring_fence: ringFence })} />);

    const row = screen.getByText(/^Ring fence profits \(30%\)/).closest("tr") as HTMLElement;
    expect(within(row).getByText("£50,000")).toBeInTheDocument();
    expect(within(row).getByText("£15,000.00")).toBeInTheDocument();
  });
});

describe("the accounts", () => {
  it("show the R&D and creative credits as other income, so the lines add up", () => {
    const accounts = {
      turnover: 100_000,
      interest_income: 0,
      other_income: 20_000,
      total_expenses: 50_000,
      profit_before_tax: 70_000,
      corporation_tax: "17500.00",
      profit_after_tax: "52500.00",
    } as AccountsSummary;
    render(<AccountsTables accounts={accounts} />);

    const row = screen.getByText(/^Other income/).closest("tr") as HTMLElement;
    expect(row).toHaveTextContent("£20,000");
  });
});
