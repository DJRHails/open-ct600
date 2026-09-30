import { afterEach, vi } from "vitest";

import type { Draft } from "@/filing/model";
import { EMPTY_RESEARCH } from "@/filing/reliefs";
import { draftShapeProblem } from "@/filing/returns/draftShape";
import { exportReturn, parseReturnFile, readReturnFile } from "@/filing/returns/returnFile";
import { RECORD } from "@/test-companies-house";

const PREVIOUS_PERIOD = {
  start: { day: "1", month: "4", year: "2024" },
  end: { day: "31", month: "3", year: "2025" },
};

const COMPARATIVES = {
  period: PREVIOUS_PERIOD,
  profit_and_loss: { turnover: "120000" },
  balance_sheet: { fixed_assets: "10000" },
  tax_on_profit: "10825",
  average_employees: "3",
};

describe("the shape of the Companies House record and comparatives", () => {
  it("accepts a draft prefilled from Companies House", () => {
    expect(draftShapeProblem({ companies_house: RECORD, comparatives: COMPARATIVES })).toBeNull();
  });

  it("accepts a record with nothing filed and comparatives not yet answered", () => {
    const record = {
      ...RECORD,
      status: null,
      incorporated_on: null,
      legal_form: null,
      registered_office: null,
      sic_codes: [{ code: "74990", description: null }],
      principal_activity: null,
      accounts: { reference_date: null, last_made_up_to: null, next_period: null },
      suggested_period: null,
      previous_accounts: null,
      previous_accounts_unavailable: "The accounts were filed on paper",
    };

    expect(draftShapeProblem({ companies_house: record, comparatives: {} })).toBeNull();
  });

  it("accepts accounts filed without a profit and loss account", () => {
    const filleted = { ...RECORD.previous_accounts, profit_and_loss: null };

    expect(draftShapeProblem({ companies_house: { ...RECORD, previous_accounts: filleted } })).toBe(
      null,
    );
  });

  it.each([
    ["a figure is text", { ...RECORD.previous_accounts, dormant: "no" }, "dormant"],
    [
      "a filed figure is text",
      { ...RECORD.previous_accounts, balance_sheet: { fixed_assets: "10000" } },
      "balance_sheet.fixed_assets",
    ],
    ["the standard is unknown", { ...RECORD.previous_accounts, standard: "large" }, "standard"],
  ])("names where the previous accounts are wrong when %s", (_case, previous, field) => {
    const draft = { companies_house: { ...RECORD, previous_accounts: previous } };

    expect(draftShapeProblem(draft)).toBe(`draft.companies_house.previous_accounts.${field}`);
  });

  it.each([
    ["a field is missing", { ...RECORD, directors: undefined }, "directors"],
    ["a field is unknown", { ...RECORD, officers: [] }, "officers"],
    ["the legal form is not one the model has", { ...RECORD, legal_form: "ltd" }, "legal_form"],
    [
      "a director is not a person",
      { ...RECORD, directors: [{ name: 1, appointed_on: null }] },
      "directors.0.name",
    ],
  ])("names where the record is wrong when %s", (_case, record, field) => {
    expect(draftShapeProblem({ companies_house: record })).toBe(`draft.companies_house.${field}`);
  });

  it.each([
    ["a figure is a number", { profit_and_loss: { turnover: 120000 } }, "profit_and_loss.turnover"],
    ["a date is incomplete", { period: { start: PREVIOUS_PERIOD.start } }, "period.end"],
    ["the tax is a number", { tax_on_profit: 10825 }, "tax_on_profit"],
    ["a part is unknown", { notes: "hello" }, "notes"],
  ])("names where the comparatives are wrong when %s", (_case, comparatives, field) => {
    expect(draftShapeProblem({ comparatives })).toBe(`draft.comparatives.${field}`);
  });
});

/** Accounts details as saved before the legal form and first period were asked (#23). */
const ACCOUNTS_BEFORE_LEGAL_FORM = {
  standard: "micro",
  directors: ["Jane Smith"],
  signing_director: "Jane Smith",
  approval_date: { day: "1", month: "6", year: "2026" },
  average_employees: "1",
  trading_status: "trading",
  dormant: "no",
};

describe("returns saved before the legal form and first period were asked", () => {
  it("imports them, with those two answers blank", async () => {
    const { blob } = exportReturn({ accounts: ACCOUNTS_BEFORE_LEGAL_FORM } as Draft, "now");

    const imported = parseReturnFile(await blob.text());

    expect(imported).toEqual({
      ok: true,
      draft: { accounts: { ...ACCOUNTS_BEFORE_LEGAL_FORM, legal_form: "", first_period: "" } },
    });
  });

  it("still refuses accounts missing any other answer", () => {
    const { dormant: _dormant, ...withoutDormant } = ACCOUNTS_BEFORE_LEGAL_FORM;

    expect(draftShapeProblem({ accounts: withoutDormant })).toBe("draft.accounts.dormant");
  });
});

describe("import files that could hurt the page", () => {
  it("refuses answers nested too deeply to check, with a clear error", () => {
    const depth = 200_000;
    const nested = `${"[".repeat(depth)}${"]".repeat(depth)}`;
    const text = `{"format":"open-ct600-return","version":1,"draft":{"supplementary_pages":{"A":{"x":${nested}}}}}`;

    const imported = parseReturnFile(text);

    expect(imported.ok).toBe(false);
    expect(!imported.ok && imported.error).toMatch(
      /^The selected file has been changed or is damaged, so it cannot be imported\. The problem is in draft\.supplementary_pages\.A\.x(\.0)+$/,
    );
  });

  it("says when the chosen file cannot be read", async () => {
    const file = new File(["{}"], "return.json", { type: "application/json" });
    vi.spyOn(file, "text").mockRejectedValue(
      new DOMException("The file was moved.", "NotFoundError"),
    );

    expect(await readReturnFile(file)).toEqual({
      ok: false,
      error: "The selected file could not be read. Choose the file again",
    });
  });
});

describe("answers that must be one of the choices offered", () => {
  it.each([
    ["accounts", { ...ACCOUNTS_BEFORE_LEGAL_FORM, standard: "bogus" }, "standard"],
    ["accounts", { ...ACCOUNTS_BEFORE_LEGAL_FORM, trading_status: "x" }, "trading_status"],
    ["accounts", { ...ACCOUNTS_BEFORE_LEGAL_FORM, dormant: "maybe" }, "dormant"],
    ["accounts", { ...ACCOUNTS_BEFORE_LEGAL_FORM, legal_form: "plc" }, "legal_form"],
    ["accounts", { ...ACCOUNTS_BEFORE_LEGAL_FORM, first_period: "sometimes" }, "first_period"],
    [
      "company",
      {
        name: "Acme",
        registration_number: "01234567",
        utr: "",
        company_type: "99",
        principal_activity: "",
      },
      "company_type",
    ],
    ["research_and_development", { ...EMPTY_RESEARCH, scheme: "grant" }, "scheme"],
    ["research_and_development", { ...EMPTY_RESEARCH, claiming: "y" }, "claiming"],
    [
      "creative_industries",
      { additional_information_submitted: "Y" },
      "additional_information_submitted",
    ],
  ])("refuses %s answers that are not a choice offered", (part, answers, field) => {
    expect(draftShapeProblem({ [part]: answers })).toBe(`draft.${part}.${field}`);
  });

  it("accepts choices not yet made", () => {
    expect(
      draftShapeProblem({
        accounts: { ...ACCOUNTS_BEFORE_LEGAL_FORM, standard: "", trading_status: "", dormant: "" },
        research_and_development: EMPTY_RESEARCH,
      }),
    ).toBeNull();
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});
