import { screen, within } from "@testing-library/react";

import type { TaxComputation } from "@/api";
import { renderApp, requestBody, stubApi } from "@/test-utils";

describe("sign up", () => {
  async function fillForm(user: ReturnType<typeof renderApp>) {
    await user.type(screen.getByLabelText("Full name"), "Ada Lovelace");
    await user.type(screen.getByLabelText("Email address"), "ada@example.com");
    await user.type(screen.getByLabelText("Company name"), "Acme Widgets Ltd");
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Create account" }));
  }

  it("registers and shows the reference", async () => {
    const fetchMock = stubApi(() => ({
      status: 201,
      body: { reference: "sgn_ABC", email: "ada@example.com" },
    }));
    const user = renderApp("/sign-up");

    await fillForm(user);

    expect(await screen.findByRole("heading", { name: "Account created" })).toBeInTheDocument();
    expect(screen.getByText("sgn_ABC")).toBeInTheDocument();
    expect(fetchMock.mock.calls[0]?.[0]).toBe("/api/signup");
    expect(requestBody(fetchMock)).toEqual({
      full_name: "Ada Lovelace",
      email: "ada@example.com",
      company_name: "Acme Widgets Ltd",
      accept_terms: true,
    });
  });

  it("checks the answers before sending anything", async () => {
    const fetchMock = stubApi(() => ({ status: 201, body: {} }));
    const user = renderApp("/sign-up");

    await user.type(screen.getByLabelText("Email address"), "not-an-email");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    const summary = within(screen.getByRole("alert"));
    expect(summary.getByText("Enter your full name")).toBeInTheDocument();
    expect(summary.getByText(/like name@example.com/)).toBeInTheDocument();
    expect(summary.getByText(/agree to the terms/)).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("says so when the webhook is down", async () => {
    stubApi(() => ({
      status: 502,
      body: { detail: "Sorry, we could not create your account right now. Try again later." },
    }));
    const user = renderApp("/sign-up");

    await fillForm(user);

    expect(
      await screen.findByRole("link", { name: /could not create your account/ }),
    ).toBeVisible();
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Create an account");
  });
});

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
