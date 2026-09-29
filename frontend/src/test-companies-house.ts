/**
 * A company as the Companies House routes return it, following the API contract in
 * docs/design/companies-house-prefill.md.
 */
import type { CompanyRecord, CompanySearchResult } from "@/api";

export const SEARCH_RESULT: CompanySearchResult = {
  number: "01234567",
  name: "ACME WIDGETS LTD",
  status: "active",
  address: "1 High Street, Leeds, LS1 1AA",
  incorporated_on: "2019-05-01",
};

export const RECORD: CompanyRecord = {
  number: "01234567",
  name: "ACME WIDGETS LTD",
  status: "active",
  incorporated_on: "2019-05-01",
  legal_form: "private-limited-company",
  registered_office: { lines: ["1 High Street", "Leeds"], postcode: "LS1 1AA" },
  sic_codes: [{ code: "62020", description: "Information technology consultancy activities" }],
  principal_activity: "Information technology consultancy activities",
  directors: [
    { name: "Ada Lovelace", appointed_on: "2019-05-01" },
    { name: "Charles Babbage", appointed_on: "2021-01-04" },
  ],
  accounts: {
    reference_date: "03-31",
    last_made_up_to: "2025-03-31",
    next_period: { start: "2025-04-01", end: "2026-03-31" },
  },
  suggested_period: { start: "2025-04-01", end: "2026-03-31", note: null },
  previous_accounts: {
    period: { start: "2024-04-01", end: "2025-03-31" },
    filed_on: "2025-11-02",
    standard: "micro",
    dormant: false,
    profit_and_loss: {
      turnover: 120_000,
      interest_income: 0,
      cost_of_sales: 0,
      staff_costs: 30_000,
      depreciation: 2_000,
      other_expenses: 8_000,
      tax: 10_825,
      profit_after_tax: 49_675,
    },
    balance_sheet: {
      fixed_assets: 10_000,
      current_assets: 70_000,
      called_up_share_capital_not_paid: 0,
      prepayments_and_accrued_income: 0,
      creditors_within_one_year: 15_000,
      creditors_after_one_year: 5_000,
      provisions: 0,
      accruals_and_deferred_income: 0,
      called_up_share_capital: 100,
      net_assets: 60_000,
    },
    average_employees: 3,
    directors: ["Ada Lovelace"],
    principal_activity: "Information technology consultancy activities",
  },
  previous_accounts_unavailable: null,
};
