# Design: prefill from Companies House and previous filings

Status: agreed 2026-09-29.

**Goal:** the user types part of a company's name or number, picks the company, and the return fills itself in from public records. Directors are chosen from the company's current officers rather than typed. Last year's figures come from the accounts the company last filed at Companies House. Everything prefilled stays editable and is labelled with where it came from.

## Decisions

| Decision | Why |
| --- | --- |
| Use the official [Companies House public data API](https://developer-specs.company-information.service.gov.uk/) and Document API, proxied by our backend with the key in `COMPANIES_HOUSE_API_KEY` | It is the supported route; scraping the website is brittle and discouraged. The key stays server-side. |
| Without a key, lookup is switched off and the forms work exactly as today (manual entry) | The same "off unless configured" stance as HMRC submission. `GET /api/companies-house/status` says which. |
| Public company data may be cached in memory for up to 10 minutes; nothing is written to disk | Stays within Companies House's rate limit (600 requests per 5 minutes per key) while keeping "the API stores nothing about you". |
| "Previous filings" means the **accounts filed at Companies House for the period before the suggested return** (electronic iXBRL filings via the Document API), found by the made-up date in the filing history | They are public and machine-readable. CT600 returns are not public. Paper/PDF-only filings give no figures, and we say so. |
| The suggested return is for a period that **has ended**: the period Companies House expects accounts for next once it has ended, otherwise the period of the accounts last filed | Accounts are usually filed at Companies House (9 months) before the return (12 months), so the return is often for the period the filed accounts cover. The rules and edge cases (first period, overdue accounts, changed reference date) are in `companies_house/periods.py`. |
| Last year's figures become **comparatives** (a new, compliance-required part of the accounts) | The Companies Act requires comparatives after the first period. Our accounts currently have none. |
| A Companies House period of account can be up to 18 months; a Corporation Tax period cannot exceed 12 | The suggested return period is the first 12 months, with a note that the rest needs a second return. |

## API contract (backend: `open_ct600/companies_house/`)

```
GET /api/companies-house/status
  → {"enabled": bool}

GET /api/companies-house/search?q=<2..160 chars>
  → {"items": [{"number": "01234567", "name": "ACME WIDGETS LTD", "status": "active",
                "address": "1 High Street, Leeds, LS1 1AA", "incorporated_on": "2019-05-01"}]}
     at most 20 items; names as Companies House returns them

GET /api/companies-house/companies/{number}
  → {
      "number": "01234567", "name": "ACME WIDGETS LTD", "status": "active",
      "incorporated_on": "2019-05-01",
      "legal_form": "private-limited-company" | "private-company-limited-by-guarantee" | "public-limited-company" | … | null,
      "registered_office": {"lines": ["1 High Street", "Leeds"], "postcode": "LS1 1AA"},
      "sic_codes": [{"code": "62020", "description": "Information technology consultancy activities"}],
      "principal_activity": "Information technology consultancy activities",   # from the first SIC code
      "directors": [{"name": "Ada Lovelace", "appointed_on": "2019-05-01"}],   # current directors only, display order
      "accounts": {"reference_date": "03-31", "last_made_up_to": "2025-03-31" | null,
                   "next_period": {"start": "2025-04-01", "end": "2026-03-31"} | null},
      "suggested_period": {"start": "2025-04-01", "end": "2026-03-31", "note": null | "…"} | null,
      "previous_accounts": null | {
          "period": {"start": "2024-04-01", "end": "2025-03-31"},
          "filed_on": "2025-11-02",
          "standard": "micro" | "small" | null,
          "dormant": bool | null,
          "profit_and_loss": {"turnover": 120000, "interest_income": 0, "cost_of_sales": 0, "staff_costs": 30000,
                              "depreciation": 2000, "other_expenses": 8000, "tax": 10825, "profit_after_tax": 49675},
          "balance_sheet": {"fixed_assets": 10000, "current_assets": 70000, "called_up_share_capital_not_paid": 0,
                            "prepayments_and_accrued_income": 0, "creditors_within_one_year": 15000,
                            "creditors_after_one_year": 5000, "provisions": 0, "accruals_and_deferred_income": 0,
                            "called_up_share_capital": 100, "net_assets": 60000},
          "average_employees": 3 | null,
          "directors": ["Ada Lovelace"],
          "principal_activity": "…" | null
      },
      "previous_accounts_unavailable": null | "The previous period's accounts were filed on paper, so their figures can't be read."
    }
  404 when Companies House has no such company; 503 with a clear message when Companies House is unavailable.
```

Field names in `previous_accounts.profit_and_loss` and `.balance_sheet` match `ProfitAndLoss` and
`BalanceSheet` in `ct600.py`, so the frontend can copy them into comparatives without mapping.

## Model additions (backend: `ct600.py`, `ixbrl/accounts.py`)

```python
class Comparatives:                      # last period's figures, shown beside this period's in the accounts
    period: ReturnPeriod                 # the previous period of account
    profit_and_loss: ProfitAndLoss
    balance_sheet: BalanceSheet

AccountsDetails.comparatives: Comparatives | None = None   # None = the company's first period of account
AccountsDetails.legal_form: LegalForm = "private-limited-company"   # FRC LegalFormEntityDimension members we support
```

The iXBRL accounts gain a previous-period duration context and instant context, render a second
column, and tag the comparatives; the legal form uses the chosen dimension member. Arelle must pass
with zero warnings, and the TPVS suite must still pass.

## Frontend

- Company details: a GOV.UK-style accessible typeahead (alphagov's `accessible-autocomplete`) searching
  by name or number. Choosing a company fetches its record, fills in name, number and principal
  activity, and keeps the record in the draft for later sections. An "I can't find the company"
  link and the disabled state fall back to today's manual fields.
- Accounting period: prefilled from `suggested_period`, with its note.
- Accounts details: directors as a checkbox list of current directors (plus "Add another person"),
  signing director chosen from them, legal form, first-period question; prefilled from the record.
- Profit and loss / balance sheet: a "Previous period" column, prefilled from `previous_accounts`
  with a notice naming the filing ("From the accounts filed on 2 November 2025 for the period ending
  31 March 2025"). Hidden when the user says this is the company's first period.
- A GOV.UK notification banner on each prefilled section: "We've filled in some answers from
  Companies House. Check them before you continue."
