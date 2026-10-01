/**
 * Bank details for a repayment (CT600 boxes 920 to 940): asked only when the computation shows
 * money due back to the company, checked as HMRC's schema would, and sent with the return.
 */
import { screen, waitFor, within } from "@testing-library/react";
import type { UserEvent } from "@testing-library/user-event";

import type { ReturnComputation } from "@/api";
import { draftShapeProblem } from "@/filing/returns/draftShape";
import { EMPTY_RESEARCH } from "@/filing/reliefs";
import { schemaPages } from "@/test-schema";
import { bodySentTo, openDraft, renderApp, type Reply, seedDraft, stubApi } from "@/test-utils";

const COMPLETE = {
  company: {
    name: "Acme Widgets Ltd",
    registration_number: "01234567",
    utr: "1234567890",
    company_type: "0",
    principal_activity: "Manufacture of widgets",
  },
  period: {
    start: { day: "1", month: "4", year: "2024" },
    end: { day: "31", month: "3", year: "2025" },
  },
  profit_and_loss: { turnover: "100000" },
  tax_adjustments: {},
  balance_sheet: {},
  accounts: {
    standard: "micro",
    directors: ["Ada Lovelace"],
    signing_director: "Ada Lovelace",
    approval_date: { day: "30", month: "6", year: "2025" },
    average_employees: "1",
    trading_status: "trading",
    dormant: "no",
    legal_form: "private-limited-company",
    first_period: "yes",
  },
  chosen_pages: [],
  research_and_development: { ...EMPTY_RESEARCH, claiming: "no" },
};

const BANK = {
  bank_name: "Synthetic Bank plc",
  sort_code: "30-94-30",
  account_number: "0073 3445",
  account_name: "Acme Widgets Ltd",
  building_society_reference: "",
};

const TASK = "Bank details for repayment";
const PAGE = "/file/repayment-bank-details";

/** A computation with these boxes; the rest is enough for check your answers to show it. */
function computation(boxes: Record<string, string>): ReturnComputation {
  return {
    boxes: Object.entries(boxes).map(([box, value]) => ({ box, label: `Box ${box}`, value })),
    tax: {
      period_start: "2024-04-01",
      period_end: "2025-03-31",
      taxable_profits: 100_000,
      augmented_profits: 100_000,
      associated_companies: 0,
      slices: [],
      tax_before_relief: "25000.00",
      marginal_relief: "2250.00",
      tax_chargeable: "22750.00",
      effective_rate: "0.2275",
      payment_due: "2026-01-01",
      filing_due: "2026-03-31",
      may_pay_by_instalments: false,
    },
    accounts: {
      turnover: 100_000,
      total_expenses: 0,
      profit_before_tax: 100_000,
      corporation_tax: "0",
      profit_after_tax: "0",
    },
    trading_loss_arising: 0,
    losses_carried_forward: 0,
    pages: {},
    reliefs: {
      group_relief: null,
      research_and_development: null,
      loans_to_participators: null,
      creative_industries: null,
    },
  } as unknown as ReturnComputation;
}

const NEEDS_BANK_DETAILS: Reply = {
  status: 422,
  body: {
    detail: [
      {
        loc: ["body", "repayment"],
        msg: "Enter the bank details for HMRC to pay the money due back to the company into: HMRC pays payable credits and repayments only into the account given on the return (boxes 920 to 940)",
      },
    ],
  },
};

function stubCompute(reply: Reply) {
  return stubApi((path) => {
    if (path === "/returns/compute") return reply;
    if (path === "/schema/pages") return { status: 200, body: schemaPages() };
    if (path === "/returns/validate") return { status: 200, body: { problems: [] } };
    return { status: 404, body: { detail: "Not Found" } };
  });
}

async function save(user: UserEvent) {
  await user.click(screen.getByRole("button", { name: "Save and continue" }));
}

describe("the bank details task", () => {
  it("appears once the computation shows a payable credit, and must be done first", async () => {
    stubCompute({ status: 200, body: computation({ "875": "19720.00" }) });
    seedDraft(COMPLETE);
    renderApp("/file/tasks");

    const task = await screen.findByRole("link", { name: TASK });
    expect(task).toHaveAttribute("href", PAGE);
    expect(task).toHaveAccessibleDescription("Incomplete");
    expect(screen.getByText("Cannot start yet")).toBeVisible();
  });

  it("appears when the service says the money due back needs an account", async () => {
    stubCompute(NEEDS_BANK_DETAILS);
    seedDraft(COMPLETE);
    renderApp("/file/tasks");

    expect(await screen.findByRole("link", { name: TASK })).toHaveAccessibleDescription(
      "Incomplete",
    );
  });

  it("is not asked for when nothing is due back", async () => {
    const fetchMock = stubCompute({ status: 200, body: computation({ "600": "22750.00" }) });
    seedDraft(COMPLETE);
    renderApp("/file/tasks");

    await waitFor(() => expect(bodySentTo(fetchMock, "/returns/compute")).toBeDefined());
    await screen.findByRole("link", { name: "Check your answers and submit" });
    expect(screen.queryByRole("link", { name: TASK })).toBeNull();
  });
});

describe("the bank details page", () => {
  it("follows the GOV.UK bank details pattern and explains details HMRC would refuse", async () => {
    stubCompute({ status: 200, body: computation({ "875": "19720.00" }) });
    seedDraft(COMPLETE);
    const user = renderApp(PAGE);

    expect(screen.getByRole("heading", { level: 1, name: TASK })).toBeVisible();
    expect(screen.getByLabelText("Sort code")).toHaveAccessibleDescription("Must be 6 digits long");
    expect(screen.getByLabelText("Sort code")).toHaveAttribute("inputmode", "numeric");
    expect(screen.getByLabelText("Account number")).toHaveAccessibleDescription(
      "Must be 8 digits long. If yours is 6 or 7 digits, add zeros to the start",
    );
    expect(screen.getByLabelText("Building society roll number (if you have one)")).toBeVisible();

    await save(user);
    const summary = screen.getByRole("alert");
    expect(
      within(summary)
        .getAllByRole("link")
        .map((link) => link.textContent),
    ).toEqual([
      "Enter the name of the bank or building society",
      "Enter the name on the account",
      "Enter a sort code",
      "Enter an account number",
    ]);

    await user.type(screen.getByLabelText("Name of bank or building society"), "Synthetic Bank");
    await user.type(screen.getByLabelText("Name on the account"), "Acme Widgets Ltd");
    await user.type(screen.getByLabelText("Sort code"), "30-94");
    await user.type(screen.getByLabelText("Account number"), "7334450");
    await save(user);
    expect(
      within(screen.getByRole("alert"))
        .getAllByRole("link")
        .map((link) => link.textContent),
    ).toEqual([
      "Sort code must be 6 digits long",
      "Account number must be 8 digits long. If yours is 6 or 7 digits, add zeros to the start",
    ]);

    await user.clear(screen.getByLabelText("Sort code"));
    await user.type(screen.getByLabelText("Sort code"), "30 94 30");
    await user.clear(screen.getByLabelText("Account number"));
    await user.type(screen.getByLabelText("Account number"), "00733445");
    await save(user);

    expect(openDraft().repayment).toEqual({
      bank_name: "Synthetic Bank",
      account_name: "Acme Widgets Ltd",
      sort_code: "30 94 30",
      account_number: "00733445",
      building_society_reference: "",
    });
    expect(await screen.findByRole("link", { name: TASK })).toHaveAccessibleDescription(
      "Completed",
    );
  });
});

describe("check your answers", () => {
  it("sends the bank details with the return and shows them", async () => {
    const fetchMock = stubCompute({ status: 200, body: computation({ "875": "19720.00" }) });
    seedDraft({ ...COMPLETE, repayment: BANK });
    renderApp("/file/check-your-answers");

    const card = (await screen.findByRole("heading", { name: TASK })).closest(
      ".govuk-summary-card",
    ) as HTMLElement;
    expect(within(card).getByText("30-94-30")).toBeVisible();
    expect(within(card).getByText("00733445")).toBeVisible();
    expect(within(card).getByRole("link", { name: /Change/ })).toHaveAttribute(
      "href",
      `${PAGE}?change=1`,
    );
    expect(bodySentTo(fetchMock, "/returns/compute")).toMatchObject({
      repayment: {
        bank_name: "Synthetic Bank plc",
        sort_code: "309430",
        account_number: "00733445",
        account_name: "Acme Widgets Ltd",
        building_society_reference: null,
      },
    });
  });

  it("links the service's problem to the bank details page", async () => {
    stubCompute(NEEDS_BANK_DETAILS);
    seedDraft(COMPLETE);
    renderApp("/file/check-your-answers");

    expect(
      await screen.findByRole("link", { name: /^Enter the bank details for HMRC to pay/ }),
    ).toHaveAttribute("href", `${PAGE}?change=1`);
  });
});

describe("saved returns with bank details", () => {
  it("import them, and refuse ones that are not text", () => {
    expect(draftShapeProblem({ repayment: BANK })).toBeNull();
    expect(draftShapeProblem({ repayment: { ...BANK, sort_code: 309430 } })).toBe(
      "draft.repayment.sort_code",
    );
  });
});
