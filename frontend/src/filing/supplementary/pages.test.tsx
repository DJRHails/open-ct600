import { screen, within } from "@testing-library/react";
import type { UserEvent } from "@testing-library/user-event";

import type { PageCode } from "@/api";
import { schemaPages } from "@/test-schema";
import { renderApp, stubApi } from "@/test-utils";

const DRAFT_KEY = "open-ct600:draft:v1";

function stubSchema() {
  return stubApi((path) =>
    path === "/schema/pages"
      ? { status: 200, body: schemaPages() }
      : { status: 404, body: { detail: "Not Found" } },
  );
}

function choose(...codes: PageCode[]) {
  window.localStorage.setItem(DRAFT_KEY, JSON.stringify({ chosen_pages: codes }));
}

function savedDraft() {
  return JSON.parse(window.localStorage.getItem(DRAFT_KEY) ?? "{}");
}

async function save(user: UserEvent) {
  await user.click(screen.getByRole("button", { name: "Save and continue" }));
}

describe("choosing supplementary pages", () => {
  it("offers every page except the dormant CT600G and saves the choice", async () => {
    stubSchema();
    const user = renderApp("/file/supplementary-pages");

    const loans = await screen.findByLabelText("CT600A: Loans to participators by close companies");
    expect(loans).toHaveAccessibleDescription(/lent money to a participator/);
    expect(screen.queryByLabelText(/CT600G/)).toBeNull();
    expect(screen.getAllByRole("checkbox")).toHaveLength(15);

    await save(user);
    expect(screen.getByRole("link", { name: /select none of these/ })).toHaveAttribute(
      "href",
      "#pages",
    );

    await user.click(screen.getByLabelText("None of these"));
    await user.click(loans);
    expect(screen.getByLabelText("None of these")).not.toBeChecked();
    await user.click(screen.getByLabelText("CT600L: Research and development"));
    await save(user);

    expect(savedDraft().chosen_pages).toEqual(["A", "L"]);
    const task = screen.getByRole("link", {
      name: "CT600A: Loans to participators by close companies",
    });
    expect(task).toHaveAttribute("href", "/file/supplementary-pages/A");
    expect(task).toHaveAccessibleDescription("Incomplete");
  });

  it("forgets the answers to a page that is no longer chosen", async () => {
    stubSchema();
    window.localStorage.setItem(
      DRAFT_KEY,
      JSON.stringify({
        chosen_pages: ["A", "D"],
        supplementary_pages: { A: { LoansByCloseCompanies: {} }, D: { Insurance: {} } },
      }),
    );
    const user = renderApp("/file/supplementary-pages");

    await user.click(
      await screen.findByLabelText("CT600A: Loans to participators by close companies"),
    );
    await save(user);

    expect(savedDraft()).toMatchObject({
      chosen_pages: ["D"],
      supplementary_pages: { D: { Insurance: {} } },
    });
    expect(savedDraft().supplementary_pages.A).toBeUndefined();
  });
});

describe("a supplementary page form", () => {
  it("asks CT600A screen by screen, with loans added and removed", async () => {
    stubSchema();
    choose("A");
    const user = renderApp("/file/supplementary-pages/A");

    const question = await screen.findByRole("group", {
      name: /Have loans made during the period/,
    });
    expect(question).toHaveAccessibleDescription("Box A5");
    await save(user);
    expect(document.title).toMatch(/^Error: Loans to participators by close companies/);
    expect(screen.getByRole("link", { name: /Select have loans made/ })).toHaveAttribute(
      "href",
      "#A-LoansByCloseCompanies-BeforeEndPeriod",
    );
    await user.click(within(question).getByLabelText("No"));
    await save(user);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Loans information");
    const first = screen.getByRole("group", { name: "Loan 1" });
    await user.type(
      within(first).getByLabelText("Name of participator or associate"),
      "Ada Lovelace",
    );
    await user.type(within(first).getByLabelText("Amount of loan"), "5,000");
    await user.click(screen.getByRole("button", { name: "Add another loan" }));
    const second = screen.getByRole("group", { name: "Loan 2" });
    expect(within(second).getByText("Loan 2")).toHaveFocus();
    await user.type(within(second).getByLabelText("Name of participator or associate"), "C£");
    expect(screen.queryByLabelText(/^Total Loans within S419/)).toBeNull();
    await save(user);

    const summary = screen.getByRole("alert");
    expect(
      within(summary).getByRole("link", {
        name: "Name of participator or associate contains a character that is not allowed (loan 2)",
      }),
    ).toHaveAttribute("href", "#A-LoansByCloseCompanies-LoansInformation-Loan-1-Name");
    expect(
      within(summary).getByRole("link", { name: "Enter amount of loan (loan 2)" }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Remove loan 2" }));
    expect(screen.queryByRole("group", { name: "Loan 2" })).toBeNull();
    await save(user);
    await save(user);
    await save(user);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(/\(continued\)/);
    expect(screen.queryByLabelText("Tax payable s419")).toBeNull();
    await save(user);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Check your answers for CT600A",
    );
    expect(screen.getByText("Ada Lovelace")).toBeInTheDocument();
    expect(screen.getByText("£5,000")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Continue" }));

    expect(screen.getByRole("link", { name: /^CT600A/ })).toHaveAccessibleDescription("Completed");
    expect(savedDraft().supplementary_pages.A.LoansByCloseCompanies.LoansInformation.Loan).toEqual([
      { Name: "Ada Lovelace", AmountOfLoan: "5,000" },
    ]);
  });

  it("summarises saved loans with change and remove", async () => {
    stubSchema();
    window.localStorage.setItem(
      DRAFT_KEY,
      JSON.stringify({
        chosen_pages: ["A"],
        supplementary_pages: {
          A: {
            LoansByCloseCompanies: {
              LoansInformation: {
                Loan: [
                  { Name: "Ada Lovelace", AmountOfLoan: "5000" },
                  { Name: "Charles Babbage", AmountOfLoan: "2000" },
                ],
              },
            },
          },
        },
      }),
    );
    const user = renderApp("/file/supplementary-pages/A/LoansInformation");

    expect(await screen.findByRole("heading", { name: "Loan 2", level: 3 })).toBeInTheDocument();
    expect(screen.getByText("Charles Babbage")).toBeInTheDocument();
    expect(screen.queryByRole("group", { name: "Loan 1" })).toBeNull();

    await user.click(screen.getByRole("button", { name: "Change loan 1" }));
    expect(screen.getByRole("group", { name: "Loan 1" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Remove loan 2" }));
    expect(screen.queryByText("Charles Babbage")).toBeNull();
  });

  it("reveals the questions for the branch of a choice", async () => {
    stubSchema();
    choose("F");
    const user = renderApp("/file/supplementary-pages/F/RelevantShippingProfits");

    const accounts = await screen.findByRole("group", { name: /^The profit or loss as shown/ });
    expect(within(accounts).queryByRole("textbox", { name: "Loss" })).toBeNull();
    await user.click(within(accounts).getByRole("radio", { name: "Loss" }));
    const loss = within(accounts).getByRole("textbox", { name: "Loss" });
    expect(loss).toHaveAccessibleDescription("Box F55B");
    await save(user);

    expect(screen.getByRole("link", { name: "Enter loss" })).toHaveAttribute(
      "href",
      "#F-TonnageTax-TonnageTax-RelevantShippingProfits-Other-Loss",
    );
    await user.type(loss, "1200");
    await save(user);
    expect(
      savedDraft().supplementary_pages.F.TonnageTax.TonnageTax.RelevantShippingProfits,
    ).toEqual({
      Other: { "?Profit|Loss": "Loss", Loss: "1200" },
    });
  });

  it("asks enumerations as radios with HMRC's labels", async () => {
    stubSchema();
    choose("F");
    const user = renderApp("/file/supplementary-pages/F");

    const certificate = await screen.findByRole("group", { name: /training certificate/ });
    await user.click(within(certificate).getByRole("radio", { name: "Not applicable" }));
    await save(user);

    expect(
      screen.getByRole("link", { name: /Select the company met the prescribed limit/ }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /training certificate/ })).toBeNull();
  });

  it("shows the problem to fix when arriving from a link to a field", async () => {
    stubSchema();
    window.localStorage.setItem(
      DRAFT_KEY,
      JSON.stringify({
        chosen_pages: ["A"],
        supplementary_pages: { A: { LoansByCloseCompanies: { TotalLoansOutstanding: "12.345" } } },
      }),
    );
    renderApp("/file/supplementary-pages/A/TotalLoansOutstanding?change=1&check=1");

    const summary = await screen.findByRole("alert");
    expect(summary).toHaveFocus();
    expect(
      within(summary).getByRole("link", {
        name: /Total loans outstanding must be a whole number of pounds/,
      }),
    ).toBeInTheDocument();
  });
});
