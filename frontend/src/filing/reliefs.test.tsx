import { screen, within } from "@testing-library/react";
import type { UserEvent } from "@testing-library/user-event";

import type { ReturnComputation } from "@/api";
import {
  EMPTY_RESEARCH,
  s455RateChanges,
  surrenderingCompanies,
  validateLoanDates,
  validateResearch,
  validateSurrenderers,
  withLoanDate,
} from "@/filing/reliefs";
import { getAt, type RawTree, setAt } from "@/filing/supplementary/answers";
import { schemaPages } from "@/test-schema";
import {
  bodySentTo,
  openDraft as saved,
  renderApp,
  type Reply,
  seedDraft as seed,
  stubApi,
} from "@/test-utils";

const SECTIONS = {
  company: {
    name: "Acme Widgets Ltd",
    registration_number: "01234567",
    utr: "1234567890",
    company_type: "0",
    principal_activity: "Manufacture of widgets",
  },
  profit_and_loss: { turnover: "100000" },
  tax_adjustments: {},
  balance_sheet: {},
  accounts: {
    standard: "micro",
    directors: ["Ada Lovelace"],
    signing_director: "Ada Lovelace",
    approval_date: { day: "30", month: "6", year: "2027" },
    average_employees: "1",
    trading_status: "trading",
    dormant: "no",
  },
};

const YEAR_TO_MARCH_2025 = {
  start: { day: "1", month: "4", year: "2024" },
  end: { day: "31", month: "3", year: "2025" },
};

/** The s455 rate rises to 35.75% for loans made from 6 April 2026. */
const CALENDAR_2026 = {
  start: { day: "1", month: "1", year: "2026" },
  end: { day: "31", month: "12", year: "2026" },
};

const LOANS = {
  LoansByCloseCompanies: {
    BeforeEndPeriod: "no",
    LoansInformation: {
      Loan: [
        { Name: "Ada Lovelace", AmountOfLoan: "5000" },
        { Name: "Charles Babbage", AmountOfLoan: "2000" },
      ],
    },
  },
};

const GROUP_RELIEF = {
  GroupAndConsortium: {
    ClaimToGroupRelief: {
      CompanyInformation: {
        Company: [{ Name: "Subsidiary Ltd", TaxReference: "9876543210", AmountClaimed: "10000" }],
      },
      ClaimAuthorisation: {
        "?CopyOfNoticesOfConsentAttached|AuthorisationForSimplifiedArrangements":
          "CopyOfNoticesOfConsentAttached",
      },
    },
  },
};

function stub(handler: (path: string) => Reply | undefined = () => undefined) {
  return stubApi((path) => {
    const reply = handler(path);
    if (reply) return reply;
    if (path === "/schema/pages") return { status: 200, body: schemaPages() };
    return { status: 404, body: { detail: "Not Found" } };
  });
}

async function save(user: UserEvent) {
  await user.click(screen.getByRole("button", { name: "Save and continue" }));
}

function question(name: RegExp | string) {
  return screen.getByRole("group", { name });
}

async function answer(user: UserEvent, name: RegExp | string, option: string) {
  await user.click(within(question(name)).getByRole("radio", { name: option }));
}

describe("the R&D claim's checks", () => {
  const MERGED = { ...EMPTY_RESEARCH, claiming: "yes" as const, qualifying_expenditure: "50,000" };

  it("builds a merged-scheme RDEC claim", () => {
    const claim = {
      ...MERGED,
      scheme: "rdec" as const,
      company_is_sme: "no" as const,
      claimed_in_previous_three_years: "yes" as const,
      additional_information_submitted: "yes" as const,
      intensity: "12",
    };

    expect(validateResearch(claim, "2024-04-01")).toEqual({
      ok: true,
      value: {
        scheme: "rdec",
        company_is_sme: false,
        qualifying_expenditure: 50_000,
        rdec_expenditure: 0,
        intensity: null,
        claim_payable_credit: false,
        rd_workers_paye_and_nic: null,
        claimed_in_previous_three_years: true,
        claim_notification_submitted: false,
        additional_information_submitted: true,
      },
    });
  });

  it("sends £0 of R&D workers' PAYE and NICs as 0, and a blank answer as not given", () => {
    const oldRdec = {
      ...MERGED,
      scheme: "rdec" as const,
      claimed_in_previous_three_years: "yes" as const,
      additional_information_submitted: "yes" as const,
    };
    const paye = (given: string) => {
      const result = validateResearch({ ...oldRdec, rd_workers_paye_and_nic: given }, "2023-04-01");
      return result.ok ? result.value?.rd_workers_paye_and_nic : result.errors;
    };

    expect(paye("0")).toBe(0);
    expect(paye("£1,200")).toBe(1200);
    expect(paye("")).toBeNull();
  });

  it("gives the service's reasons a claim cannot be made", () => {
    const claim = {
      ...MERGED,
      scheme: "eris" as const,
      intensity: "25",
      claim_payable_credit: "yes" as const,
      claimed_in_previous_three_years: "no" as const,
      claim_notification_submitted: "no" as const,
      additional_information_submitted: "no" as const,
    };
    const result = validateResearch(claim, "2024-04-01");
    const before = validateResearch({ ...claim, intensity: "35" }, "2023-04-01");

    expect(!result.ok && result.errors).toEqual({
      intensity: expect.stringMatching(/^ERIS needs R&D expenditure of at least 30%/),
      claim_notification_submitted: expect.stringMatching(/^Submit a claim notification form/),
      additional_information_submitted: expect.stringMatching(
        /^Submit the R&D additional information form/,
      ),
    });
    expect(!before.ok && before.errors.scheme).toMatch(/^ERIS is for periods starting on or after/);
    expect(validateResearch({ ...EMPTY_RESEARCH, claiming: "no" }, undefined)).toEqual({
      ok: true,
      value: null,
    });
  });
});

describe("the other relief answers' checks", () => {
  it("asks for loan dates only when the s455 rate changes in the period", () => {
    expect(s455RateChanges({ start: "2026-01-01", end: "2026-12-31" })).toBe(true);
    expect(s455RateChanges({ start: "2024-04-01", end: "2025-03-31" })).toBe(false);
    expect(s455RateChanges({ start: "2026-04-06", end: "2027-04-05" })).toBe(false);
  });

  it("needs each loan's date within the period", () => {
    const period = { start: "2026-01-01", end: "2026-12-31" };
    const ada = { Name: "Ada", AmountOfLoan: "5000" };
    const withAda = (year: string) =>
      withLoanDate({ LoansByCloseCompanies: { LoansInformation: { Loan: [ada] } } }, "loans", 0, {
        day: "6",
        month: "4",
        year,
      });

    expect(validateLoanDates(withAda("2026"), period)).toEqual({
      ok: true,
      value: { loans: ["2026-04-06"], repaid_within_nine_months: [], repaid_later: [] },
    });
    expect(validateLoanDates(withAda("2025"), period)).toEqual({
      ok: false,
      errors: { "loans-0": "The date the loan to Ada was made must be in this accounting period" },
    });
  });

  it("keeps each loan's date with its own row, so removing a loan cannot move dates", () => {
    const period = { start: "2026-01-01", end: "2026-12-31" };
    const loans = [
      { Name: "Ada", AmountOfLoan: "5000" },
      { Name: "Charles", AmountOfLoan: "2000" },
    ];
    let raw: RawTree = { LoansByCloseCompanies: { LoansInformation: { Loan: loans } } };
    raw = withLoanDate(raw, "loans", 0, { day: "6", month: "4", year: "2026" });
    raw = withLoanDate(raw, "loans", 1, { day: "1", month: "2", year: "2026" });
    const list = ["LoansByCloseCompanies", "LoansInformation", "Loan"];
    const withoutAda = setAt(raw, list, [getAt(raw, [...list, 1]) ?? {}]) as RawTree;

    expect(validateLoanDates(withoutAda, period)).toEqual({
      ok: true,
      value: { loans: ["2026-02-01"], repaid_within_nine_months: [], repaid_later: [] },
    });
  });

  it("takes surrendering companies from CT600C and only the figures given", () => {
    const companies = surrenderingCompanies({
      ClaimToGroupRelief: {
        CompanyInformation: {
          Company: [
            { Name: "Sub", TaxReference: "9876543210", AmountClaimed: "1" },
            { Name: "Sub again", TaxReference: "9876543210", AmountClaimed: "2" },
          ],
        },
      },
    });
    const blank = { surrenderable_amount: "", surrendered_to_others: "", consortium_share: "" };

    expect(companies).toEqual([{ reference: "9876543210", name: "Sub" }]);
    expect(validateSurrenderers({ "9876543210": blank }, companies)).toEqual({
      ok: true,
      value: [],
    });
    expect(
      validateSurrenderers(
        { "9876543210": { ...blank, surrendered_to_others: "10", consortium_share: "150" } },
        companies,
      ),
    ).toEqual({
      ok: false,
      errors: {
        "surrenderer-0-surrenderable_amount": "Enter the amount it can surrender",
        "surrenderer-0-consortium_share":
          "Enter the consortium share as a percentage from 0 to 100, like 35",
      },
    });
  });
});

describe("relief tasks", () => {
  it("asks for an R&D claim with the questions that apply to the period", async () => {
    stub();
    seed({ ...SECTIONS, period: YEAR_TO_MARCH_2025, chosen_pages: [] });
    const user = renderApp("/file/tasks");

    const task = screen.getByRole("link", { name: "Research and development relief" });
    expect(task).toHaveAccessibleDescription("Incomplete");
    await user.click(task);
    await answer(user, /claiming research and development/, "Yes");

    const schemes = within(question("Which scheme is the company claiming under?")).getAllByRole(
      "radio",
    );
    expect(schemes.map((radio) => radio.getAttribute("value"))).toEqual(["rdec", "eris"]);
    await user.click(
      within(question("Which scheme is the company claiming under?")).getByLabelText(/RDEC/),
    );
    await answer(user, /small or medium-sized enterprise/, "No");
    await user.type(screen.getByLabelText("Qualifying R&D expenditure"), "50,000");
    expect(screen.queryByLabelText(/PAYE and National Insurance/)).toBeNull();
    await answer(user, /claimed R&D relief in the 3 years/, "No");
    await answer(user, /claim notification form/, "No");
    await answer(user, /additional information form/, "Yes");
    await save(user);

    expect(screen.getByRole("link", { name: /^Submit a claim notification form/ })).toHaveAttribute(
      "href",
      "#claim_notification_submitted",
    );
    await answer(user, /claim notification form/, "Yes");
    await save(user);

    expect(
      screen.getByRole("link", { name: "Research and development relief" }),
    ).toHaveAccessibleDescription("Completed");
    expect(saved().research_and_development).toMatchObject({
      claiming: "yes",
      scheme: "rdec",
      qualifying_expenditure: "50,000",
      claim_notification_submitted: "yes",
    });
  });

  it("asks when each CT600A loan was made when the s455 rate changes, and sends the dates", async () => {
    const fetchMock = stub((path) =>
      path === "/returns/compute" ? { status: 422, body: { detail: [] } } : undefined,
    );
    seed({
      ...SECTIONS,
      period: CALENDAR_2026,
      chosen_pages: ["A"],
      supplementary_pages: { A: LOANS },
      research_and_development: { ...EMPTY_RESEARCH, claiming: "no" },
    });
    const user = renderApp("/file/tasks");

    await user.click(await screen.findByRole("link", { name: "CT600A: when the loans were made" }));
    await user.type(
      within(question("When was the loan to Ada Lovelace made?")).getByLabelText("Day"),
      "6",
    );
    await user.type(
      within(question("When was the loan to Ada Lovelace made?")).getByLabelText("Month"),
      "4",
    );
    await user.type(
      within(question("When was the loan to Ada Lovelace made?")).getByLabelText("Year"),
      "2025",
    );
    await save(user);

    expect(
      screen.getByRole("link", { name: /loan to Ada Lovelace was made must be in this/ }),
    ).toHaveAttribute("href", "#loans-0-day");
    expect(
      screen.getByRole("link", { name: /Enter the date the loan to Charles Babbage/ }),
    ).toBeInTheDocument();
    const ada = within(question("When was the loan to Ada Lovelace made?")).getByLabelText("Year");
    await user.clear(ada);
    await user.type(ada, "2026");
    const charles = question("When was the loan to Charles Babbage made?");
    await user.type(within(charles).getByLabelText("Day"), "1");
    await user.type(within(charles).getByLabelText("Month"), "2");
    await user.type(within(charles).getByLabelText("Year"), "2026");
    await save(user);

    expect(
      screen.getByRole("link", { name: "CT600A: when the loans were made" }),
    ).toHaveAccessibleDescription("Completed");
    await user.click(screen.getByRole("link", { name: "Check your answers and submit" }));
    expect(
      await screen.findByRole("heading", { name: "CT600A: when the loans were made" }),
    ).toBeInTheDocument();
    expect(bodySentTo(fetchMock, "/returns/compute")).toMatchObject({
      participator_loan_dates: {
        loans: ["2026-04-06", "2026-02-01"],
        repaid_within_nine_months: [],
        repaid_later: [],
      },
    });

    await user.click(screen.getByRole("link", { name: /^Change ct600a: loans/i }));
    await user.click(screen.getByRole("link", { name: /^Change loans information/i }));
    await user.click(screen.getByRole("button", { name: "Remove loan 1" }));
    await save(user);
    await user.click(await screen.findByRole("button", { name: "Continue" }));

    expect(await screen.findByText("1 February 2026")).toBeInTheDocument();
    expect(bodySentTo(fetchMock, "/returns/compute")).toMatchObject({
      participator_loan_dates: { loans: ["2026-02-01"] },
    });
  });

  it("asks again for loan dates saved by position in an older draft", async () => {
    stub();
    seed({
      ...SECTIONS,
      period: CALENDAR_2026,
      chosen_pages: ["A"],
      supplementary_pages: { A: LOANS },
      research_and_development: { ...EMPTY_RESEARCH, claiming: "no" },
      participator_loan_dates: {
        loans: [
          { day: "6", month: "4", year: "2026" },
          { day: "1", month: "2", year: "2026" },
        ],
        repaid_within_nine_months: [],
        repaid_later: [],
      },
    });
    renderApp("/file/tasks");

    expect(
      await screen.findByRole("link", { name: "CT600A: when the loans were made" }),
    ).toHaveAccessibleDescription("Incomplete");
  });

  it("does not ask for loan dates when the rate is the same all period", async () => {
    stub();
    seed({
      ...SECTIONS,
      period: YEAR_TO_MARCH_2025,
      chosen_pages: ["A"],
      supplementary_pages: { A: LOANS },
    });
    renderApp("/file/tasks");

    expect(
      await screen.findByRole("link", { name: /^CT600A: Loans to participators/ }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "CT600A: when the loans were made" })).toBeNull();
  });

  it("takes figures for CT600C's surrendering companies, all optional", async () => {
    const fetchMock = stub((path) =>
      path === "/returns/compute" ? { status: 422, body: { detail: [] } } : undefined,
    );
    seed({
      ...SECTIONS,
      period: YEAR_TO_MARCH_2025,
      chosen_pages: ["C"],
      supplementary_pages: { C: GROUP_RELIEF },
      research_and_development: { ...EMPTY_RESEARCH, claiming: "no" },
    });
    const user = renderApp("/file/group-relief-surrenderers");

    const company = await screen.findByRole("group", { name: "Subsidiary Ltd (9876543210)" });
    await user.type(within(company).getByLabelText(/already surrendered/), "1000");
    await save(user);
    expect(screen.getByRole("link", { name: "Enter the amount it can surrender" })).toHaveAttribute(
      "href",
      "#surrenderer-0-surrenderable_amount",
    );

    await user.type(
      within(company).getByLabelText(/can surrender for its accounting period/),
      "40,000",
    );
    await save(user);

    expect(
      screen.getByRole("link", { name: "CT600C: surrendering companies' figures" }),
    ).toHaveAccessibleDescription("Completed");
    await user.click(screen.getByRole("link", { name: "Check your answers and submit" }));
    await screen.findByRole("heading", { name: "CT600C: surrendering companies' figures" });
    expect(bodySentTo(fetchMock, "/returns/compute")).toMatchObject({
      group_relief_surrenderers: [
        {
          tax_reference: "9876543210",
          surrenderable_amount: 40_000,
          surrendered_to_others: 1_000,
          consortium_share: null,
        },
      ],
    });
  });

  it("needs the creatives additional information form for CT600P", async () => {
    stub();
    seed({ ...SECTIONS, period: YEAR_TO_MARCH_2025, chosen_pages: ["P"] });
    const user = renderApp("/file/tasks");

    await user.click(
      await screen.findByRole("link", { name: "CT600P: additional information form" }),
    );
    await answer(user, /creative industries additional information form/, "No");
    await save(user);
    expect(
      screen.getByRole("link", { name: /^Submit the creatives additional information form/ }),
    ).toBeInTheDocument();

    await answer(user, /creative industries additional information form/, "Yes");
    await save(user);
    expect(
      screen.getByRole("link", { name: "CT600P: additional information form" }),
    ).toHaveAccessibleDescription("Completed");
  });
});

describe("checking a return with reliefs", () => {
  const COMPLETE = {
    ...SECTIONS,
    period: YEAR_TO_MARCH_2025,
    chosen_pages: ["A"],
    supplementary_pages: { A: LOANS },
    research_and_development: {
      ...EMPTY_RESEARCH,
      claiming: "yes",
      scheme: "rdec",
      company_is_sme: "no",
      qualifying_expenditure: "50000",
      claimed_in_previous_three_years: "yes",
      additional_information_submitted: "yes",
    },
  };

  it("sends the user to the relief task the service rejected", async () => {
    stub((path) =>
      path === "/returns/compute"
        ? {
            status: 422,
            body: {
              detail: [
                {
                  loc: ["body", "research_and_development", "scheme"],
                  msg: "Value error, Add CT600L: it is needed for RDEC and for payable R&D tax credits",
                },
              ],
            },
          }
        : undefined,
    );
    seed(COMPLETE);
    renderApp("/file/check-your-answers");

    expect(await screen.findByRole("link", { name: /^Add CT600L/ })).toHaveAttribute(
      "href",
      "/file/research-and-development?change=1",
    );
    const card = screen
      .getByRole("heading", { name: "Research and development relief" })
      .closest(".govuk-summary-card") as HTMLElement;
    expect(
      within(card).getByText("Research and development expenditure credit (RDEC)"),
    ).toBeInTheDocument();
    expect(within(card).getByText("£50,000")).toBeInTheDocument();
  });

  it("shows the boxes the service calculates as its answers, not the user's", async () => {
    const computation = {
      boxes: [],
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
      pages: {
        A: {
          ...LOANS.LoansByCloseCompanies,
          LoansInformation: { ...LOANS.LoansByCloseCompanies.LoansInformation, TotalLoans: "7000" },
          TaxPayable: "2362.50",
        },
      },
      reliefs: {
        group_relief: null,
        research_and_development: null,
        loans_to_participators: null,
        creative_industries: null,
      },
    } as unknown as ReturnComputation;
    stub((path) => (path === "/returns/compute" ? { status: 200, body: computation } : undefined));
    seed(COMPLETE);
    renderApp("/file/check-your-answers");

    const payable = (await screen.findByText(/^£2,362\.50/)).closest("div") as HTMLElement;
    const card = screen
      .getByRole("heading", { name: "CT600A: Loans to participators by close companies" })
      .closest(".govuk-summary-card") as HTMLElement;
    expect(card).toContainElement(payable);
    expect(payable).toHaveTextContent("Tax payable s419");
    expect(payable).toHaveTextContent("Worked out for you");
    expect(within(card).getByText("Ada Lovelace").closest("div")).not.toHaveTextContent(
      "Worked out for you",
    );
  });
});
