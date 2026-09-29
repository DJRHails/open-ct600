import { screen, waitFor, within } from "@testing-library/react";
import type { UserEvent } from "@testing-library/user-event";

import { RECORD, SEARCH_RESULT } from "@/test-companies-house";
import { renderApp, type Reply, stubApi } from "@/test-utils";

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
