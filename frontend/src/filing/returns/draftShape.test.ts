import { draftShapeProblem } from "@/filing/returns/draftShape";
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
