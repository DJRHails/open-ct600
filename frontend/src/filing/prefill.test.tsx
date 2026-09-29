import { screen, waitFor, within } from "@testing-library/react";
import type { UserEvent } from "@testing-library/user-event";

import type { CompanyRecord } from "@/api";
import { RECORD, SEARCH_RESULT } from "@/test-companies-house";
import { bodySentTo, renderApp, type Reply, stubApi } from "@/test-utils";

const DRAFT_KEY = "open-ct600:draft:v1";

type Handler = (path: string) => Reply | undefined;

/** Companies House lookup switched on, answering with the fixture unless ``handler`` does. */
function stubCompaniesHouse(handler: Handler = () => undefined) {
  return stubApi((path) => {
    const reply = handler(path);
    if (reply) return reply;
    if (path === "/companies-house/status") return { status: 200, body: { enabled: true } };
    if (path.startsWith("/companies-house/search")) {
      return { status: 200, body: { items: [SEARCH_RESULT] } };
    }
    if (path === `/companies-house/companies/${RECORD.number}`)
      return { status: 200, body: RECORD };
    return { status: 404, body: { detail: "Not Found" } };
  });
}

function savedDraft() {
  return JSON.parse(window.localStorage.getItem(DRAFT_KEY) ?? "{}");
}

async function save(user: UserEvent) {
  await user.click(screen.getByRole("button", { name: "Save and continue" }));
}

async function chooseAcme(user: UserEvent) {
  await user.type(await screen.findByRole("combobox", { name: /Find the company/ }), "acme");
  await user.click(await screen.findByRole("option", { name: /ACME WIDGETS LTD/ }));
}

describe("company details from Companies House", () => {
  it("fills in the company chosen from a search, and keeps its record for later", async () => {
    const fetchMock = stubCompaniesHouse();
    const user = renderApp("/file/company-details");

    expect(await screen.findByRole("combobox", { name: /Find the company/ })).toBeInTheDocument();
    expect(screen.queryByLabelText("Company name")).toBeNull();
    await chooseAcme(user);

    expect(await screen.findByLabelText("Company name")).toHaveValue("ACME WIDGETS LTD");
    expect(screen.getByLabelText("Company registration number")).toHaveValue("01234567");
    expect(screen.getByLabelText("What does the company do?")).toHaveValue(
      "Information technology consultancy activities",
    );
    expect(screen.getByRole("region", { name: "Important" })).toHaveTextContent(
      "We’ve filled in some answers from Companies House. Check them before you continue.",
    );
    const paths = fetchMock.mock.calls.map(([input]) => String(input));
    expect(paths).toContain("/api/companies-house/search?q=acme");
    expect(paths).toContain("/api/companies-house/companies/01234567");
    expect(savedDraft().companies_house).toEqual(RECORD);

    await user.clear(screen.getByLabelText("What does the company do?"));
    await user.type(screen.getByLabelText("What does the company do?"), "Widget consultancy");
    await user.type(screen.getByLabelText(/Unique Taxpayer Reference/), "1234567890");
    await save(user);

    expect(savedDraft().company).toMatchObject({
      name: "ACME WIDGETS LTD",
      registration_number: "01234567",
      principal_activity: "Widget consultancy",
      utr: "1234567890",
    });
  });

  it("asks for a search before saving, and offers manual entry", async () => {
    stubCompaniesHouse();
    const user = renderApp("/file/company-details");

    await screen.findByRole("combobox", { name: /Find the company/ });
    await save(user);
    expect(screen.getByRole("link", { name: /^Search for the company/ })).toHaveAttribute(
      "href",
      "#company-search",
    );

    await user.click(screen.getByRole("button", { name: "I can’t find the company" }));

    expect(screen.queryByRole("combobox")).toBeNull();
    expect(screen.getByLabelText("Company name")).toHaveValue("");
    expect(screen.queryByRole("region", { name: "Important" })).toBeNull();
  });

  it("uses the manual fields when Companies House lookup is switched off", async () => {
    stubCompaniesHouse((path) =>
      path === "/companies-house/status" ? { status: 200, body: { enabled: false } } : undefined,
    );
    renderApp("/file/company-details");

    expect(await screen.findByLabelText("Company name")).toBeInTheDocument();
    expect(screen.queryByRole("combobox")).toBeNull();
  });

  it("uses the manual fields when the service cannot say whether lookup is on", async () => {
    stubCompaniesHouse((path) =>
      path === "/companies-house/status" ? { status: 500, body: { detail: "Oops" } } : undefined,
    );
    renderApp("/file/company-details");

    expect(await screen.findByLabelText("Company name")).toBeInTheDocument();
  });

  it("explains when Companies House has no record of the company", async () => {
    stubCompaniesHouse((path) =>
      path.startsWith("/companies-house/companies/")
        ? { status: 404, body: { detail: "No such company" } }
        : undefined,
    );
    const user = renderApp("/file/company-details");

    await chooseAcme(user);

    const message = await screen.findByText(/Companies House has no company with that number/, {
      selector: ".govuk-error-message",
    });
    expect(message).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: /Find the company/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "I can’t find the company" })).toBeInTheDocument();
  });

  it("explains when Companies House is unavailable", async () => {
    stubCompaniesHouse((path) =>
      path.startsWith("/companies-house/search")
        ? { status: 503, body: { detail: "Companies House is not responding" } }
        : undefined,
    );
    const user = renderApp("/file/company-details");

    await user.type(await screen.findByRole("combobox", { name: /Find the company/ }), "acme");

    await waitFor(() =>
      expect(
        screen.getByText(/Companies House is not responding\. Try again, or enter them yourself/, {
          selector: ".govuk-error-message",
        }),
      ).toBeInTheDocument(),
    );
    const group = screen.getByRole("combobox").closest(".govuk-form-group") as HTMLElement;
    expect(group).toHaveClass("govuk-form-group--error");
    expect(within(group).getByText(/Find the company/)).toHaveTextContent(
      /Error: We could not get the company’s details/,
    );
  });

  it("shows a saved company's fields without searching again", async () => {
    stubCompaniesHouse();
    window.localStorage.setItem(
      DRAFT_KEY,
      JSON.stringify({
        company: {
          name: "ACME WIDGETS LTD",
          registration_number: "01234567",
          utr: "1234567890",
          company_type: "0",
          principal_activity: "Widgets",
        },
      }),
    );
    renderApp("/file/company-details");

    expect(screen.getByLabelText("Company name")).toHaveValue("ACME WIDGETS LTD");
    expect(screen.queryByRole("combobox")).toBeNull();
  });
});

const COMPANY = {
  name: "ACME WIDGETS LTD",
  registration_number: "01234567",
  utr: "1234567890",
  company_type: "0",
  principal_activity: "Widgets",
};

/** Accounts details saved for a company past its first period of account. */
const ACCOUNTS = {
  standard: "micro",
  directors: ["Ada Lovelace"],
  signing_director: "Ada Lovelace",
  approval_date: { day: "30", month: "6", year: "2026" },
  average_employees: "3",
  trading_status: "trading",
  dormant: "no",
  legal_form: "private-limited-company",
  first_period: "no",
};

function seed(draft: object) {
  window.localStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
}

function withRecord(record: CompanyRecord = RECORD, extra: object = {}) {
  seed({ companies_house: record, company: COMPANY, ...extra });
}

function line(name: string) {
  return screen.getByRole("group", { name });
}

describe("later sections from the Companies House record", () => {
  it("prefills the accounting period, with its note", async () => {
    stubCompaniesHouse();
    const note = "The period of account is 18 months, so this return covers its first 12 months.";
    withRecord({ ...RECORD, suggested_period: { start: "2025-04-01", end: "2026-03-31", note } });
    const user = renderApp("/file/accounting-period");

    const start = line("Start date");
    expect(within(start).getByLabelText("Day")).toHaveValue("1");
    expect(within(start).getByLabelText("Month")).toHaveValue("4");
    expect(within(start).getByLabelText("Year")).toHaveValue("2025");
    expect(within(line("End date")).getByLabelText("Year")).toHaveValue("2026");
    expect(screen.getByText(note)).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Important" })).toBeInTheDocument();

    await user.clear(within(line("End date")).getByLabelText("Day"));
    await user.type(within(line("End date")).getByLabelText("Day"), "30");
    await save(user);

    expect(savedDraft().period).toEqual({
      start: { day: "1", month: "4", year: "2025" },
      end: { day: "30", month: "3", year: "2026" },
    });
  });

  it("does not use a record for a different company", () => {
    stubCompaniesHouse();
    seed({ companies_house: RECORD, company: { ...COMPANY, registration_number: "SC123456" } });
    renderApp("/file/accounting-period");

    expect(within(line("Start date")).getByLabelText("Day")).toHaveValue("");
    expect(screen.queryByRole("region", { name: "Important" })).toBeNull();
  });

  it("lists the current directors to choose from, and anyone else added", async () => {
    stubCompaniesHouse();
    withRecord();
    const user = renderApp("/file/accounts-details");

    const directors = line("Who were the company’s directors during the period?");
    expect(within(directors).getByLabelText("Ada Lovelace")).toBeChecked();
    expect(within(directors).getByLabelText("Charles Babbage")).toBeChecked();
    expect(screen.getByLabelText("Private company limited by shares")).toBeChecked();
    const first = line("Is this the company’s first period of account?");
    expect(within(first).getByLabelText("No")).toBeChecked();
    expect(screen.getByRole("region", { name: "Important" })).toBeInTheDocument();

    await user.click(within(directors).getByLabelText("Charles Babbage"));
    await user.click(screen.getByRole("button", { name: "Add another person" }));
    await user.type(screen.getByLabelText("Other person 1 full name"), "Grace Hopper");
    const signing = line("Which director signed the accounts?");
    expect(
      within(signing)
        .getAllByRole("radio")
        .map((radio) => radio.getAttribute("value")),
    ).toEqual(["Ada Lovelace", "Grace Hopper"]);

    await user.click(within(directors).getByLabelText("Ada Lovelace"));
    await user.clear(screen.getByLabelText("Other person 1 full name"));
    await user.click(screen.getByRole("button", { name: "Remove other person 1" }));
    await save(user);
    expect(
      screen.getByRole("link", { name: "Select the company’s directors, or add a person" }),
    ).toHaveAttribute("href", "#directors");

    await user.click(within(directors).getByLabelText("Ada Lovelace"));
    await user.click(screen.getByLabelText(/Micro-entity accounts/));
    await user.click(
      within(line("Which director signed the accounts?")).getByLabelText("Ada Lovelace"),
    );
    const approval = line("When did the board approve the accounts?");
    await user.type(within(approval).getByLabelText("Day"), "30");
    await user.type(within(approval).getByLabelText("Month"), "6");
    await user.type(within(approval).getByLabelText("Year"), "2026");
    await user.type(screen.getByLabelText("Average number of employees during the period"), "3");
    await user.click(
      within(line("Was the company dormant during this period?")).getByLabelText("No"),
    );
    await user.click(screen.getByLabelText("It traded during the period"));
    await save(user);

    expect(savedDraft().accounts).toMatchObject({
      directors: ["Ada Lovelace"],
      signing_director: "Ada Lovelace",
      legal_form: "private-limited-company",
      first_period: "no",
    });
  });

  it("types directors in when the record lists none", () => {
    stubCompaniesHouse();
    withRecord({ ...RECORD, directors: [] });
    renderApp("/file/accounts-details");

    expect(screen.getByLabelText("Director 1 full name")).toHaveValue("");
  });
});

describe("the previous period's figures (comparatives)", () => {
  it("are prefilled from the accounts last filed, and can be changed", async () => {
    stubCompaniesHouse();
    withRecord();
    const user = renderApp("/file/profit-and-loss");

    expect(
      screen.getByText(
        "From the accounts filed on 2 November 2025 for the period ending 31 March 2025.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Important" })).toBeInTheDocument();
    const start = line("When did the previous period of account start?");
    expect(within(start).getByLabelText("Year")).toHaveValue("2024");
    const turnover = line("Turnover");
    expect(within(turnover).getByLabelText("Previous period")).toHaveValue("120000");
    expect(within(turnover).getByLabelText("This period")).toHaveValue("");

    await user.clear(within(turnover).getByLabelText("Previous period"));
    await user.type(within(turnover).getByLabelText("Previous period"), "125,000");
    await user.type(within(turnover).getByLabelText("This period"), "150,000");
    await save(user);

    expect(savedDraft().profit_and_loss).toMatchObject({ turnover: "150,000" });
    expect(savedDraft().comparatives).toMatchObject({
      period: {
        start: { day: "1", month: "4", year: "2024" },
        end: { day: "31", month: "3", year: "2025" },
      },
      profit_and_loss: { turnover: "125,000", staff_costs: "30000" },
    });
    expect(savedDraft().comparatives.profit_and_loss).not.toHaveProperty("tax");
  });

  it("show the balance sheet at the previous period's end", () => {
    stubCompaniesHouse();
    withRecord();
    renderApp("/file/balance-sheet");

    expect(
      screen.getByText("The previous period’s balance sheet is at 31 March 2025."),
    ).toBeInTheDocument();
    expect(within(line("Fixed assets")).getByLabelText("Previous period")).toHaveValue("10000");
  });

  it("explain why the filed accounts could not be read, and are typed in", async () => {
    stubCompaniesHouse();
    const reason = "The latest accounts were filed on paper, so their figures can’t be read.";
    withRecord({ ...RECORD, previous_accounts: null, previous_accounts_unavailable: reason });
    const user = renderApp("/file/profit-and-loss");

    expect(
      screen.getByText(`${reason} Enter last period’s figures from the company’s accounts.`),
    ).toBeInTheDocument();
    expect(within(line("Turnover")).getByLabelText("Previous period")).toHaveValue("");
    await user.type(within(line("Turnover")).getByLabelText("Previous period"), "12.5");
    await save(user);

    expect(
      screen.getByRole("link", { name: "Enter the start date of the previous period" }),
    ).toHaveAttribute("href", "#previous_start-day");
    expect(
      screen.getByRole("link", {
        name: "Enter previous period’s turnover in whole pounds, without pence",
      }),
    ).toHaveAttribute("href", "#previous-turnover");
  });

  it("are not asked for the company's first period of account", () => {
    stubCompaniesHouse();
    withRecord(RECORD, { accounts: { first_period: "yes" } });
    renderApp("/file/profit-and-loss");

    expect(screen.getByLabelText("Turnover")).toBeInTheDocument();
    expect(screen.queryByLabelText("Previous period")).toBeNull();
    expect(screen.queryByText(/From the accounts filed on/)).toBeNull();
  });

  it("are sent with the accounts and shown in check your answers", async () => {
    const fetchMock = stubCompaniesHouse((path) =>
      path === "/returns/compute" ? { status: 422, body: { detail: [] } } : undefined,
    );
    seed({
      companies_house: RECORD,
      company: COMPANY,
      period: {
        start: { day: "1", month: "4", year: "2025" },
        end: { day: "31", month: "3", year: "2026" },
      },
      profit_and_loss: { turnover: "150000" },
      tax_adjustments: {},
      balance_sheet: { fixed_assets: "9000" },
      accounts: ACCOUNTS,
      comparatives: {
        period: {
          start: { day: "1", month: "4", year: "2024" },
          end: { day: "31", month: "3", year: "2025" },
        },
        profit_and_loss: { turnover: "120,000" },
        balance_sheet: { fixed_assets: "10000" },
      },
      chosen_pages: [],
      research_and_development: { claiming: "no" },
    });
    renderApp("/file/check-your-answers");

    const card = (await screen.findByRole("heading", { name: "Previous period" })).closest(
      ".govuk-summary-card",
    ) as HTMLElement;
    expect(card).toHaveTextContent("1 April 2024 to 31 March 2025");
    expect(within(card).getByText("£120,000")).toBeInTheDocument();
    expect(bodySentTo(fetchMock, "/returns/compute")).toMatchObject({
      accounts: {
        legal_form: "private-limited-company",
        comparatives: {
          period: { start: "2024-04-01", end: "2025-03-31" },
          profit_and_loss: { turnover: 120_000, staff_costs: 0 },
          balance_sheet: { fixed_assets: 10_000, current_assets: 0 },
        },
      },
    });
  });

  it("reopen the profit and loss account once the company says it is not its first period", () => {
    stubCompaniesHouse();
    seed({ profit_and_loss: { turnover: "150000" }, accounts: ACCOUNTS });
    renderApp("/file/tasks");

    expect(
      screen.getByRole("link", { name: "Profit and loss account" }),
    ).toHaveAccessibleDescription("Incomplete");
  });
});
