import { screen, within } from "@testing-library/react";
import type { UserEvent } from "@testing-library/user-event";

import type { ReturnComputation, SubmissionReceipt } from "@/api";
import { schemaPages } from "@/test-schema";
import { bodySentTo, renderApp, stubApi } from "@/test-utils";

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
  boxes: [{ box: "440", label: "Corporation Tax chargeable", value: "22750.00", kind: "money" }],
  tax: TAX,
  accounts: {
    turnover: 100_000,
    interest_income: 0,
    total_expenses: 0,
    profit_before_tax: 100_000,
    corporation_tax: "22750.00",
    profit_after_tax: "77250.00",
    called_up_share_capital_not_paid: 0,
    fixed_assets: 0,
    current_assets: 0,
    prepayments_and_accrued_income: 0,
    creditors_within_one_year: 0,
    net_current_assets: 0,
    total_assets_less_current_liabilities: 0,
    creditors_after_one_year: 0,
    provisions: 0,
    accruals_and_deferred_income: 0,
    net_assets: 0,
    called_up_share_capital: 0,
    profit_and_loss_reserve: 0,
  },
  trading_loss_arising: 0,
  losses_carried_forward: 0,
  pages: {},
};

const COMPANY = {
  name: "Acme Widgets Ltd",
  registration_number: "01234567",
  utr: "1234567890",
  company_type: 0,
  principal_activity: "Manufacture of widgets",
};

const RECEIPT: SubmissionReceipt = {
  reference: "sub_0000000000000000000042",
  received_at: "2026-09-28T12:00:00Z",
  fingerprint: "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567",
  company: COMPANY,
  signatory: "Ada Lovelace",
  computation: COMPUTATION,
};

/** The service's replies for a return with no supplementary pages and no HMRC problems. */
function demoReplies(path: string) {
  if (path === "/returns/compute") return { status: 200, body: COMPUTATION };
  if (path === "/schema/pages") return { status: 200, body: schemaPages() };
  if (path === "/returns/validate") {
    return { status: 200, body: { valid: true, documents_attached: true, problems: [] } };
  }
  return { status: 201, body: RECEIPT };
}

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
  await user.type(screen.getByLabelText("What does the company do?"), "Manufacture of widgets");
  expect(screen.getByLabelText("UK trading or professional company")).toBeChecked();
  await save(user);

  await user.click(screen.getByRole("link", { name: "Accounting period" }));
  await fillDate(user, "Start date", "1", "4", "2024");
  await fillDate(user, "End date", "31", "3", "2025");
  await save(user);

  await user.click(screen.getByRole("link", { name: "Profit and loss account" }));
  await user.type(screen.getByLabelText("Turnover"), "100,000");
  await save(user);

  await user.click(screen.getByRole("link", { name: "Tax adjustments" }));
  await save(user);

  await user.click(screen.getByRole("link", { name: "Balance sheet" }));
  await user.type(screen.getByLabelText("Prepayments and accrued income"), "1,000");
  await user.type(screen.getByLabelText("Provisions for liabilities"), "500");
  await save(user);

  await user.click(screen.getByRole("link", { name: "Accounts details" }));
  await completeAccountsDetails(user);

  await user.click(screen.getByRole("link", { name: "Choose supplementary pages" }));
  await user.click(await screen.findByLabelText("None of these"));
  await save(user);
}

async function completeAccountsDetails(user: UserEvent) {
  await user.click(screen.getByLabelText(/Micro-entity accounts/));
  await user.type(screen.getByLabelText("Director 1 full name"), "Ada Lovelace");
  await user.click(screen.getByRole("radio", { name: "Ada Lovelace" }));
  await fillDate(user, "When did the board approve the accounts?", "30", "6", "2025");
  await user.type(screen.getByLabelText("Average number of employees during the period"), "1");
  await user.click(screen.getByLabelText("It traded during the period"));
  await save(user);
}

describe("filing a return", () => {
  it("goes from the task list to a submitted return", async () => {
    const fetchMock = stubApi(demoReplies);
    const user = renderApp("/file/tasks");

    expect(screen.getByText("Cannot start yet")).toBeInTheDocument();
    await completeEverySection(user);
    expect(screen.getByText("You have completed 7 of 7 sections.")).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: "Check your answers and submit" }));
    expect(await screen.findByText("£22,750.00", { selector: "strong" })).toBeInTheDocument();
    expect(screen.getByText("Micro-entity accounts (FRS 105)")).toBeInTheDocument();
    expect(await screen.findByText(/HMRC's rules found no problems/)).toBeInTheDocument();
    expect(bodySentTo(fetchMock, "/returns/compute")).toMatchObject({
      company: COMPANY,
      period: { start: "2024-04-01", end: "2025-03-31" },
      profit_and_loss: { turnover: 100_000, staff_costs: 0 },
      balance_sheet: { prepayments_and_accrued_income: 1_000, provisions: 500 },
      accounts: {
        standard: "micro",
        directors: ["Ada Lovelace"],
        signing_director: "Ada Lovelace",
        approval_date: "2025-06-30",
        average_employees: 1,
        trading_status: "trading",
      },
      supplementary_pages: {},
    });
    expect(bodySentTo(fetchMock, "/returns/validate")).toMatchObject({
      ct600: { company: COMPANY },
    });

    await user.click(screen.getByRole("link", { name: "Continue" }));
    await user.type(screen.getByLabelText("Full name"), "Ada Lovelace");
    await user.click(screen.getByLabelText("Director"));
    await user.click(screen.getByLabelText(/demonstration receipt/));
    await user.click(screen.getByLabelText(/correct and complete/));
    await user.click(screen.getByRole("button", { name: "Submit return" }));

    expect(await screen.findByRole("heading", { name: "Return submitted" })).toBeInTheDocument();
    expect(screen.getByText(RECEIPT.reference)).toBeInTheDocument();
    expect(bodySentTo(fetchMock, "/returns/submit")).toMatchObject({
      declaration: { name: "Ada Lovelace", capacity: "director", confirmed: true },
    });
    expect(window.localStorage.getItem("open-ct600:draft:v1")).toBeNull();

    await user.click(screen.getByRole("link", { name: "Start another return" }));
    expect(screen.getByText("You have completed 0 of 7 sections.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Delete your answers" }));
    expect(window.sessionStorage.getItem("open-ct600:receipt:v2")).toBeNull();
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
        company: { ...COMPANY, company_type: "0" },
        period: {
          start: { day: "1", month: "4", year: "2027" },
          end: { day: "31", month: "3", year: "2028" },
        },
        profit_and_loss: {},
        tax_adjustments: {},
        balance_sheet: {},
        accounts: {
          standard: "micro",
          directors: ["Ada Lovelace"],
          signing_director: "Ada Lovelace",
          approval_date: { day: "1", month: "6", year: "2028" },
          average_employees: "1",
          trading_status: "trading",
        },
        chosen_pages: [],
      }),
    );
    renderApp("/file/check-your-answers");

    const link = await screen.findByRole("link", { name: /have not been set yet/ });
    expect(link).toHaveAttribute("href", "/file/accounting-period?change=1");
  });

  it("collects accounts details with directors added and removed", async () => {
    const user = renderApp("/file/accounts-details");

    await save(user);
    const summary = screen.getByRole("alert");
    for (const message of [
      "Select how the accounts were prepared",
      "Enter the name of director 1",
      "Select the director who signed the accounts",
      "Enter the date the accounts were approved",
      "Enter the average number of employees",
      "Select whether the company traded",
    ]) {
      expect(within(summary).getByRole("link", { name: message })).toBeInTheDocument();
    }
    expect(within(summary).getByRole("link", { name: /date the accounts/ })).toHaveAttribute(
      "href",
      "#approval_date-day",
    );
    expect(screen.getByText("Enter the directors' names first.")).toBeInTheDocument();

    await user.type(screen.getByLabelText("Director 1 full name"), "Ada Lovelace");
    await user.click(screen.getByRole("button", { name: "Add another director" }));
    await user.type(screen.getByLabelText("Director 2 full name"), "Charles Babbage");
    await user.click(screen.getByRole("radio", { name: "Charles Babbage" }));
    await user.click(screen.getByRole("button", { name: "Remove director 2" }));

    expect(screen.queryByLabelText("Director 2 full name")).toBeNull();
    expect(screen.queryByRole("radio", { name: "Charles Babbage" })).toBeNull();
    expect(screen.getByRole("radio", { name: "Ada Lovelace" })).not.toBeChecked();

    await user.click(screen.getByLabelText(/Small company accounts/));
    await user.click(screen.getByRole("radio", { name: "Ada Lovelace" }));
    await fillDate(user, "When did the board approve the accounts?", "30", "6", "2025");
    await user.type(screen.getByLabelText("Average number of employees during the period"), "0");
    await user.click(screen.getByLabelText("It has never traded"));
    await save(user);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Company Tax Return");
    const saved = JSON.parse(window.localStorage.getItem("open-ct600:draft:v1") ?? "{}");
    expect(saved.accounts).toMatchObject({
      directors: ["Ada Lovelace"],
      signing_director: "Ada Lovelace",
      standard: "small",
      trading_status: "never_traded",
    });
  });

  it("does not show check your answers until every section is complete", () => {
    renderApp("/file/check-your-answers");

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Company Tax Return");
  });
});
