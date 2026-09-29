import { screen } from "@testing-library/react";

import type { TaxComputation } from "@/api";
import { renderApp, requestBody, stubApi } from "@/test-utils";

describe("calculator", () => {
  it("shows the tax for the profits entered", async () => {
    const tax: TaxComputation = {
      period_start: "2026-04-01",
      period_end: "2027-03-31",
      taxable_profits: 40_000,
      augmented_profits: 40_000,
      associated_companies: 0,
      slices: [
        {
          financial_year: 2026,
          start: "2026-04-01",
          end: "2027-03-31",
          days: 365,
          profits: 40_000,
          augmented_profits: "40000.00",
          lower_limit: "50000.00",
          upper_limit: "250000.00",
          band: "small",
          rate: "0.19",
          tax: "7600.00",
          marginal_relief: "0.00",
          ring_fence: null,
        },
      ],
      tax_before_relief: "7600.00",
      marginal_relief: "0.00",
      tax_chargeable: "7600.00",
      effective_rate: "0.1900",
      payment_due: "2028-01-01",
      filing_due: "2028-03-31",
      may_pay_by_instalments: false,
    };
    const fetchMock = stubApi(() => ({ status: 200, body: tax }));
    const user = renderApp("/calculator");

    await user.type(screen.getByLabelText("Taxable profits"), "40000");
    await user.click(screen.getByRole("button", { name: "Calculate Corporation Tax" }));

    expect(await screen.findByText("£7,600.00", { selector: "strong" })).toBeInTheDocument();
    expect(screen.getByText("Small profits rate (19%)")).toBeInTheDocument();
    expect(screen.getByText("1 January 2028")).toBeInTheDocument();
    expect(requestBody(fetchMock)).toEqual({
      period_start: "2026-04-01",
      period_end: "2027-03-31",
      taxable_profits: 40_000,
      associated_companies: 0,
    });
  });
});
