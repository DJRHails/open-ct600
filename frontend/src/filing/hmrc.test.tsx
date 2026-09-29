import { screen, within } from "@testing-library/react";
import type { UserEvent } from "@testing-library/user-event";
import { vi } from "vitest";

import type { HmrcProblem, ReturnComputation } from "@/api";
import { schemaPages } from "@/test-schema";
import { bodySentTo, renderApp, type Reply, stubApi } from "@/test-utils";

const PASSWORD = "correct-horse-battery-staple";

const DRAFT = {
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
  },
  chosen_pages: ["A"],
  supplementary_pages: {
    A: {
      LoansByCloseCompanies: {
        BeforeEndPeriod: "no",
        LoansInformation: {
          Loan: [{ Name: "Ada Lovelace", AmountOfLoan: "5000" }],
          TotalLoans: "5000",
          TaxChargeable: "1687.50",
        },
        TaxPayable: "1687.50",
      },
    },
  },
};

const TAX = {
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
  pages: { A: DRAFT.supplementary_pages.A.LoansByCloseCompanies },
  reliefs: {
    group_relief: "0.00",
    research_and_development_scheme: null,
    research_and_development_deduction: "0.00",
    research_and_development_credit: "0.00",
    research_and_development_payable_credit: "0.00",
    loans_to_participators_tax: "1687.50",
  },
};

const LOAN_PROBLEM: HmrcProblem = {
  code: 9466,
  message: "Box A20 must equal Box A15 multiplied by the loans to participator rate",
  box: "A20",
  page: "A",
  path: "/IRenvelope/CompanyTaxReturn/LoansByCloseCompanies/LoansInformation/TaxChargeable",
};

const ACCEPTED = {
  status: "accepted",
  environment: "test-in-live",
  correlation_id: "A1B2C3D4E5F6",
  irmark: "ZmFrZQ==",
  irmark_base32: "MZQWWZI7UEQXGYLNOBWGK",
  accepted_time: "2026-09-29T10:15:00Z",
  messages: ["Thank you for your submission"],
  receipt_xml: "<GovTalkMessage/>",
};

type Handler = (path: string, body: unknown) => Reply | undefined;

/** The service's replies: ``handler`` answers first, then a clean return with no problems. */
function stubService(handler: Handler = () => undefined) {
  return stubApi((path, body) => {
    const reply = handler(path, body);
    if (reply) return reply;
    if (path === "/schema/pages") return { status: 200, body: schemaPages() };
    if (path === "/returns/compute") return { status: 200, body: COMPUTATION };
    if (path === "/returns/validate") {
      return { status: 200, body: { valid: true, documents_attached: true, problems: [] } };
    }
    return { status: 500, body: { detail: `Unexpected request to ${path}` } };
  });
}

function seedDraft() {
  window.localStorage.setItem("open-ct600:draft:v1", JSON.stringify(DRAFT));
}

function stored(): string {
  return JSON.stringify({ ...window.localStorage }) + JSON.stringify({ ...window.sessionStorage });
}

async function declare(user: UserEvent, method: RegExp) {
  await user.type(await screen.findByLabelText("Full name"), "Ada Lovelace");
  await user.click(screen.getByRole("radio", { name: "Director" }));
  await user.click(screen.getByRole("radio", { name: method }));
  await user.click(screen.getByLabelText(/correct and complete/));
}

async function signIn(user: UserEvent) {
  await user.type(screen.getByLabelText("Government Gateway user ID"), "123456789012");
  await user.type(screen.getByLabelText("Password"), PASSWORD);
}

describe("checking a return with supplementary pages", () => {
  it("lists HMRC's problems with links to the field to fix", async () => {
    const mainReturn: HmrcProblem = {
      code: 9113,
      message: "You must provide a set of iXBRL accounts",
      box: null,
      page: null,
      path: "/IRenvelope/CompanyTaxReturn/ReturnInfoSummary/Accounts",
    };
    const fetchMock = stubService((path) =>
      path === "/returns/validate"
        ? {
            status: 200,
            body: { valid: false, documents_attached: false, problems: [LOAN_PROBLEM, mainReturn] },
          }
        : undefined,
    );
    seedDraft();
    renderApp("/file/check-your-answers");

    const summary = await screen.findByRole("alert");
    expect(summary).toHaveTextContent("HMRC would reject your return as it stands");
    expect(
      within(summary).getByRole("link", {
        name: `${LOAN_PROBLEM.message} (HMRC error 9466, box A20)`,
      }),
    ).toHaveAttribute(
      "href",
      "/file/supplementary-pages/A/LoansInformation?change=1&check=1&from=check" +
        "#A-LoansByCloseCompanies-LoansInformation-TaxChargeable",
    );
    expect(
      within(summary).getByRole("link", {
        name: "You must provide a set of iXBRL accounts (HMRC error 9113)",
      }),
    ).toHaveAttribute("href", "#ct600-boxes");
    expect(document.title).toBe("Error: Check your answers – Open CT600");
    expect(bodySentTo(fetchMock, "/returns/validate")).toMatchObject({
      ct600: {
        supplementary_pages: {
          A: { LoansInformation: { Loan: [{ Name: "Ada Lovelace", AmountOfLoan: "5000" }] } },
        },
      },
    });
  });

  it("shows the pages' answers and the reliefs the computation applied", async () => {
    stubService();
    seedDraft();
    renderApp("/file/check-your-answers");

    expect(await screen.findByText(/HMRC's rules found no problems/)).toBeInTheDocument();
    const card = screen
      .getByRole("heading", { name: "CT600A: Loans to participators by close companies" })
      .closest(".govuk-summary-card") as HTMLElement;
    expect(within(card).getByText("Ada Lovelace")).toBeInTheDocument();
    expect(within(card).getByRole("link", { name: /^Change/ })).toHaveAttribute(
      "href",
      "/file/supplementary-pages/A?change=1",
    );
    const reliefs = screen.getByRole("heading", { name: "Reliefs" })
      .nextElementSibling as HTMLElement;
    expect(
      within(reliefs).getByText("Tax on loans to participators (section 455)"),
    ).toBeInTheDocument();
    expect(within(reliefs).queryByText("Group relief claimed")).toBeNull();
  });

  it("says so when HMRC's rules cannot be checked", async () => {
    stubService((path) =>
      path === "/returns/validate" ? { status: 503, body: { detail: "Try later" } } : undefined,
    );
    seedDraft();
    renderApp("/file/check-your-answers");

    expect(
      await screen.findByText(/We could not check your return against HMRC's rules: Try later/),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Continue" })).toBeInTheDocument();
  });
});

describe("downloading the return's documents", () => {
  function stubDownloads() {
    const saved: { name: string; href: string }[] = [];
    const created: Blob[] = [];
    // jsdom has no object URLs; the stub is removed with the other globals after each test.
    class BlobUrls extends URL {
      static override createObjectURL = vi.fn<typeof URL.createObjectURL>((blob) => {
        created.push(blob as Blob);
        return `blob:download-${created.length}`;
      });
      static override revokeObjectURL = vi.fn<typeof URL.revokeObjectURL>();
    }
    vi.stubGlobal("URL", BlobUrls);
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (
      this: HTMLAnchorElement,
    ) {
      saved.push({ name: this.download, href: this.href });
    });
    return { saved, created };
  }

  it("saves each document under the name the service gives", async () => {
    const { saved, created } = stubDownloads();
    const fetchMock = stubService();
    const reply = fetchMock.getMockImplementation();
    fetchMock.mockImplementation(async (input, init) => {
      const path = String(input);
      if (path === "/api/returns/accounts.xhtml") {
        return new Response("<html>accounts</html>", {
          headers: {
            "Content-Disposition": 'attachment; filename="01234567-accounts-2025-03-31.xhtml"',
          },
        });
      }
      if (path === "/api/returns/ct600.xml") return new Response("<IRenvelope/>");
      if (path === "/api/returns/computations.xhtml") {
        return new Response(
          JSON.stringify({ detail: "HMRC has not published the computations taxonomy" }),
          { status: 422 },
        );
      }
      return reply ? reply(input, init) : new Response(null, { status: 500 });
    });
    seedDraft();
    const user = renderApp("/file/check-your-answers");

    await user.click(await screen.findByRole("button", { name: "Download the accounts (iXBRL)" }));
    await user.click(screen.getByRole("button", { name: "Download the CT600 return (XML)" }));
    await user.click(screen.getByRole("button", { name: "Download the tax computations (iXBRL)" }));

    expect(saved).toEqual([
      { name: "01234567-accounts-2025-03-31.xhtml", href: "blob:download-1" },
      { name: "ct600.xml", href: "blob:download-2" },
    ]);
    expect(await created[0]?.text()).toBe("<html>accounts</html>");
    expect(bodySentTo(fetchMock, "/returns/ct600.xml")).toHaveProperty(
      "ct600.company.utr",
      "1234567890",
    );
    expect(bodySentTo(fetchMock, "/returns/accounts.xhtml")).toHaveProperty(
      "company.utr",
      "1234567890",
    );
    expect(
      screen.getByRole("button", { name: "Download the tax computations (iXBRL)" }),
    ).toHaveAccessibleDescription(/computations taxonomy/);
  });
});

describe("submitting to HMRC", () => {
  it("sends a Test in Live submission and shows HMRC's receipt", async () => {
    const fetchMock = stubService((path) =>
      path === "/returns/submit-to-hmrc" ? { status: 200, body: ACCEPTED } : undefined,
    );
    seedDraft();
    const user = renderApp("/file/declaration");

    await declare(user, /Test in Live/);
    await user.click(screen.getByRole("button", { name: "Send test submission" }));
    expect(
      screen.getByRole("link", { name: "Enter your Government Gateway user ID" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toHaveAttribute("type", "password");
    expect(screen.getByLabelText("Password")).toHaveAttribute("autocomplete", "off");
    await signIn(user);
    await user.click(screen.getByRole("button", { name: "Send test submission" }));

    expect(
      await screen.findByRole("heading", { name: "HMRC accepted your test submission" }),
    ).toBeInTheDocument();
    expect(screen.getByText(ACCEPTED.irmark_base32)).toBeInTheDocument();
    expect(screen.getByText(ACCEPTED.correlation_id)).toBeInTheDocument();
    expect(screen.getByRole("main")).toHaveTextContent(
      "HMRC checked your return but has not filed it",
    );
    expect(bodySentTo(fetchMock, "/returns/submit-to-hmrc")).toMatchObject({
      environment: "test-in-live",
      gateway_user_id: "123456789012",
      gateway_password: PASSWORD,
      declaration: { name: "Ada Lovelace", capacity: "director", confirmed: true },
      ct600: { supplementary_pages: { A: { TaxPayable: "1687.50" } } },
    });
    expect(stored()).not.toContain(PASSWORD);
    expect(stored()).toContain(ACCEPTED.irmark_base32);
  });

  it("lists HMRC's business errors, linking to the answer at fault", async () => {
    stubService((path) =>
      path === "/returns/submit-to-hmrc"
        ? {
            status: 200,
            body: {
              status: "rejected",
              environment: "live",
              correlation_id: "C0RR3L4T10N",
              errors: [
                {
                  number: 9466,
                  type: "business",
                  message: LOAN_PROBLEM.message,
                  box: "A20",
                  page: "A",
                  location: LOAN_PROBLEM.path,
                },
              ],
            },
          }
        : undefined,
    );
    seedDraft();
    const user = renderApp("/file/declaration");

    await declare(user, /^Submit to HMRC/);
    await signIn(user);
    await user.click(screen.getByRole("button", { name: "Submit return" }));

    const summary = await screen.findByRole("alert");
    expect(summary).toHaveTextContent("HMRC did not accept your return");
    expect(within(summary).getByRole("link", { name: /9466, box A20/ })).toHaveAttribute(
      "href",
      expect.stringContaining("/file/supplementary-pages/A/LoansInformation"),
    );
    expect(screen.getByLabelText("Password")).toHaveValue("");
    expect(stored()).not.toContain(PASSWORD);
  });

  it("puts HMRC's refusal of the sign in details on those fields", async () => {
    stubService((path) =>
      path === "/returns/submit-to-hmrc"
        ? {
            status: 401,
            body: {
              detail: {
                error: "authentication_failed",
                message: "Authentication failure",
                correlation_id: null,
                errors: [
                  {
                    number: 1046,
                    type: "fatal",
                    message: "Authentication Failure",
                    box: null,
                    page: null,
                    location: "",
                  },
                ],
              },
            },
          }
        : undefined,
    );
    seedDraft();
    const user = renderApp("/file/declaration");

    await declare(user, /^Submit to HMRC/);
    await signIn(user);
    await user.click(screen.getByRole("button", { name: "Submit return" }));

    const summary = await screen.findByRole("alert");
    expect(summary).toHaveFocus();
    expect(
      within(summary).getByRole("link", { name: /did not accept this Government Gateway user ID/ }),
    ).toHaveAttribute("href", "#gateway_user_id");
    expect(screen.getByLabelText("Password")).toHaveAccessibleDescription(
      "Error: Enter your Government Gateway password again",
    );
    expect(screen.getByLabelText("Password")).toHaveValue("");
    expect(document.title).toBe("Error: Declaration – Open CT600");
    expect(stored()).not.toContain(PASSWORD);
  });

  it("explains when submission is switched off and keeps the demonstration receipt", async () => {
    stubService((path) => {
      if (path === "/returns/submit-to-hmrc") {
        return {
          status: 403,
          body: {
            detail: {
              error: "submission_disabled",
              message: "Submitting to HMRC is switched off on this service.",
              correlation_id: null,
              errors: [],
            },
          },
        };
      }
      if (path === "/returns/submit") {
        return {
          status: 201,
          body: {
            reference: "sub_0000000000000000000042",
            received_at: "2026-09-29T12:00:00Z",
            fingerprint: "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567",
            company: { ...DRAFT.company, company_type: 0 },
            signatory: "Ada Lovelace",
            computation: COMPUTATION,
          },
        };
      }
      return undefined;
    });
    seedDraft();
    const user = renderApp("/file/declaration");

    await declare(user, /Test in Live/);
    await signIn(user);
    await user.click(screen.getByRole("button", { name: "Send test submission" }));

    expect(
      await screen.findByRole("link", { name: /switched off on this service/ }),
    ).toHaveAttribute("href", "#method");
    await user.click(screen.getByRole("radio", { name: /demonstration receipt/ }));
    expect(screen.queryByLabelText("Password")).toBeNull();
    await user.click(screen.getByRole("button", { name: "Submit return" }));

    expect(await screen.findByRole("heading", { name: "Return submitted" })).toBeInTheDocument();
    expect(screen.getByRole("main")).toHaveTextContent("your return has not been sent to HMRC");
    expect(stored()).not.toContain(PASSWORD);
  });

  it("tells the user HMRC is still processing when it does not answer in time", async () => {
    stubService((path) =>
      path === "/returns/submit-to-hmrc"
        ? {
            status: 504,
            body: {
              detail: {
                error: "hmrc_timeout",
                message: "HMRC did not answer within 120 seconds",
                correlation_id: "5L0W5UBM15510N",
                errors: [],
              },
            },
          }
        : undefined,
    );
    seedDraft();
    const user = renderApp("/file/declaration");

    await declare(user, /^Submit to HMRC/);
    await signIn(user);
    await user.click(screen.getByRole("button", { name: "Submit return" }));

    const banner = await screen.findByRole("region", { name: "Important" });
    expect(banner).toHaveTextContent("HMRC is still processing your return");
    expect(banner).toHaveTextContent("5L0W5UBM15510N");
    expect(screen.queryByRole("alert")).toBeNull();
    expect(window.localStorage.getItem("open-ct600:draft:v1")).not.toBeNull();
    expect(stored()).not.toContain(PASSWORD);
  });

  it("shows the service's reason when it cannot send the return, like a period HMRC cannot take yet", async () => {
    const reason =
      "HMRC has not published a computations taxonomy for periods ending after 31 March 2026, so this return cannot be submitted yet.";
    stubService((path) =>
      path === "/returns/submit-to-hmrc"
        ? {
            status: 409,
            body: {
              detail: {
                error: "computations_unavailable",
                message: reason,
                correlation_id: null,
                errors: [],
              },
            },
          }
        : undefined,
    );
    seedDraft();
    const user = renderApp("/file/declaration");

    await declare(user, /^Submit to HMRC/);
    await signIn(user);
    await user.click(screen.getByRole("button", { name: "Submit return" }));

    expect(
      await screen.findByRole("link", { name: `Your return was not submitted: ${reason}` }),
    ).toBeInTheDocument();
  });

  it("lists the problems when HMRC's rules reject the return before it is sent", async () => {
    stubService((path) =>
      path === "/returns/submit-to-hmrc"
        ? {
            status: 422,
            body: {
              detail: {
                error: "invalid_return",
                message: "HMRC would reject this return.",
                correlation_id: null,
                errors: [LOAN_PROBLEM],
              },
            },
          }
        : undefined,
    );
    seedDraft();
    const user = renderApp("/file/declaration");

    await declare(user, /^Submit to HMRC/);
    await signIn(user);
    await user.click(screen.getByRole("button", { name: "Submit return" }));

    const summary = await screen.findByRole("alert");
    expect(summary).toHaveTextContent("HMRC would reject your return, so it was not sent");
    expect(within(summary).getByRole("link", { name: /HMRC error 9466/ })).toBeInTheDocument();
  });
});
