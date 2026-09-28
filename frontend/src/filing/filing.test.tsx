import { screen, within } from "@testing-library/react";
import type { UserEvent } from "@testing-library/user-event";

import type { ReturnComputation, SubmissionReceipt } from "@/api";
import { renderApp, requestBody, stubApi } from "@/test-utils";

const TAX = {
  period_start: "2024-04-01",
  period_end: "2025-03-31",
  taxable_profits: 100_000,
  augmented_profits: 100_000,
  associated_companies: 0,
  slices: [
    {
      financial_year: 2024,
      start: "2024-04-01",
      end: "2025-03-31",
      days: 365,
      profits: 100_000,
      augmented_profits: "100000.00",
      lower_limit: "50000.00",
      upper_limit: "250000.00",
      band: "marginal" as const,
      rate: "0.25",
      tax: "25000.00",
      marginal_relief: "2250.00",
    },
  ],
  tax_before_relief: "25000.00",
  marginal_relief: "2250.00",
  tax_chargeable: "22750.00",
  effective_rate: "0.2275",
  payment_due: "2026-01-01",
  filing_due: "2026-03-31",
  may_pay_by_instalments: false,
};

const COMPUTATION: ReturnComputation = {
  boxes: [{ number: 440, label: "Corporation Tax chargeable", value: "22750.00", kind: "money" }],
  tax: TAX,
  accounts: {
    turnover: 100_000,
    interest_income: 0,
    total_expenses: 0,
    profit_before_tax: 100_000,
    corporation_tax: "22750.00",
    profit_after_tax: "77250.00",
    fixed_assets: 0,
    current_assets: 0,
    creditors_within_one_year: 0,
    net_current_assets: 0,
    total_assets_less_current_liabilities: 0,
    creditors_after_one_year: 0,
    net_assets: 0,
    called_up_share_capital: 0,
    profit_and_loss_reserve: 0,
  },
  trading_loss_arising: 0,
  losses_carried_forward: 0,
};

const RECEIPT: SubmissionReceipt = {
  reference: "sub_0000000000000000000042",
  received_at: "2026-09-28T12:00:00Z",
  fingerprint: "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567",
  company: { name: "Acme Widgets Ltd", registration_number: "01234567", utr: "1234567890" },
  signatory: "Ada Lovelace",
  computation: COMPUTATION,
};

async function save(user: UserEvent) {
  await user.click(screen.getByRole("button", { name: "Save and continue" }));
}

async function fillDate(user: UserEvent, legend: string, day: string, month: string, year: string) {
  const group = screen.getByRole("group", { name: legend });
  await user.type(within(group).getByLabelText("Day"), day);
  await user.type(within(group).getByLabelText("Month"), month);
  await user.type(within(group).getByLabelText("Year"), year);
}

async function completeEverySection(user: UserEvent) {
  await user.click(screen.getByRole("link", { name: "Company details" }));
  await user.type(screen.getByLabelText("Company name"), "Acme Widgets Ltd");
  await user.type(screen.getByLabelText("Company registration number"), "01234567");
  await user.type(screen.getByLabelText(/Unique Taxpayer Reference/), "1234567890");
  await save(user);

  await user.click(screen.getByRole("link", { name: "Accounting period" }));
  await fillDate(user, "Start date", "1", "4", "2024");
  await fillDate(user, "End date", "31", "3", "2025");
  await save(user);

  await user.click(screen.getByRole("link", { name: "Profit and loss account" }));
  await user.type(screen.getByLabelText("Turnover"), "100,000");
  await save(user);

  for (const section of ["Tax adjustments", "Balance sheet"]) {
    await user.click(screen.getByRole("link", { name: section }));
    await save(user);
  }
}

describe("filing a return", () => {
  it("goes from the task list to a submitted return", async () => {
    const fetchMock = stubApi((path) =>
      path === "/returns/compute"
        ? { status: 200, body: COMPUTATION }
        : { status: 201, body: RECEIPT },
    );
    const user = renderApp("/file/tasks");

    expect(screen.getByText("Cannot start yet")).toBeInTheDocument();
    await completeEverySection(user);
    expect(screen.getByText("You have completed 5 of 5 sections.")).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: "Check your answers and submit" }));
    expect(await screen.findByText("£22,750.00", { selector: "strong" })).toBeInTheDocument();
    expect(requestBody(fetchMock)).toMatchObject({
      company: { registration_number: "01234567" },
      period: { start: "2024-04-01", end: "2025-03-31" },
      profit_and_loss: { turnover: 100_000, staff_costs: 0 },
    });

    await user.click(screen.getByRole("link", { name: "Continue" }));
    await user.type(screen.getByLabelText("Full name"), "Ada Lovelace");
    await user.click(screen.getByLabelText("Director"));
    await user.click(screen.getByLabelText(/correct and complete/));
    await user.click(screen.getByRole("button", { name: "Submit return" }));

    expect(await screen.findByRole("heading", { name: "Return submitted" })).toBeInTheDocument();
    expect(screen.getByText(RECEIPT.reference)).toBeInTheDocument();
    expect(requestBody(fetchMock, 1)).toMatchObject({
      declaration: { name: "Ada Lovelace", capacity: "director", confirmed: true },
    });
    expect(window.localStorage.getItem("open-ct600:draft:v1")).toBeNull();

    await user.click(screen.getByRole("link", { name: "Start another return" }));
    expect(screen.getByText("You have completed 0 of 5 sections.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Delete your answers" }));
    expect(window.sessionStorage.getItem("open-ct600:receipt:v1")).toBeNull();
    expect(screen.queryByRole("button", { name: "Delete your answers" })).toBeNull();
  });

  it("returns focus to the error summary when the same errors happen again", async () => {
    const user = renderApp("/file/company-details");

    await save(user);
    await user.click(screen.getByLabelText("Company name"));
    expect(screen.getByRole("alert")).not.toHaveFocus();
    await save(user);

    expect(screen.getByRole("alert")).toHaveFocus();
  });

  it("shows GOV.UK errors and keeps the section incomplete", async () => {
    const user = renderApp("/file/company-details");

    await user.type(screen.getByLabelText("Company registration number"), "123");
    await save(user);

    const summary = screen.getByRole("alert");
    expect(summary).toHaveFocus();
    expect(within(summary).getByRole("link", { name: "Enter the company name" })).toHaveAttribute(
      "href",
      "#name",
    );
    expect(screen.getByLabelText("Company registration number")).toHaveAccessibleDescription(
      expect.stringContaining("in the correct format"),
    );
    expect(document.title).toBe("Error: Company details – Open CT600");
    expect(window.localStorage.getItem("open-ct600:draft:v1")).toBeNull();
  });

  it("sends the user back to the section the service rejected", async () => {
    stubApi(() => ({
      status: 422,
      body: {
        detail: [
          {
            loc: ["body", "period"],
            msg: "Value error, Rates for the financial year starting 1 April 2027 have not been set yet.",
          },
        ],
      },
    }));
    window.localStorage.setItem(
      "open-ct600:draft:v1",
      JSON.stringify({
        company: { name: "Acme", registration_number: "01234567", utr: "1234567890" },
        period: {
          start: { day: "1", month: "4", year: "2027" },
          end: { day: "31", month: "3", year: "2028" },
        },
        profit_and_loss: {},
        tax_adjustments: {},
        balance_sheet: {},
      }),
    );
    renderApp("/file/check-your-answers");

    const link = await screen.findByRole("link", { name: /have not been set yet/ });
    expect(link).toHaveAttribute("href", "/file/accounting-period?change=1");
  });

  it("does not show check your answers until every section is complete", () => {
    renderApp("/file/check-your-answers");

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Company Tax Return");
  });
});
