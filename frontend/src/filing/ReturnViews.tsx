import type { AccountsSummary, CT600Box } from "@/api";
import { formatMoney, formatPercent, formatPounds } from "@/format";

function formatBox(box: CT600Box): string {
  switch (box.kind) {
    case "pounds":
      return formatPounds(box.value);
    case "money":
      return formatMoney(box.value);
    case "rate":
      return formatPercent(box.value, false);
    case "flag":
      return Number(box.value) === 1 ? "Yes" : "No";
    case "count":
    case "year":
      return String(Number(box.value));
  }
}

/** The CT600 boxes the answers produce, as HMRC's form numbers them. */
export function CT600BoxesTable({ boxes }: { boxes: CT600Box[] }) {
  return (
    <table className="govuk-table">
      <caption className="govuk-table__caption govuk-table__caption--m">Your CT600 boxes</caption>
      <thead className="govuk-table__head">
        <tr className="govuk-table__row">
          <th scope="col" className="govuk-table__header">
            Box
          </th>
          <th scope="col" className="govuk-table__header">
            Description
          </th>
          <th scope="col" className="govuk-table__header govuk-table__header--numeric">
            Value
          </th>
        </tr>
      </thead>
      <tbody className="govuk-table__body">
        {boxes.map((box) => (
          <tr className="govuk-table__row" key={box.box}>
            <th scope="row" className="govuk-table__header">
              {box.box}
            </th>
            <td className="govuk-table__cell">{box.label}</td>
            <td className="govuk-table__cell govuk-table__cell--numeric app-numeric">
              {formatBox(box)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

type Line = { label: string; value: string; total?: boolean };

function StatementTable({ caption, lines }: { caption: string; lines: Line[] }) {
  return (
    <table className="govuk-table">
      <caption className="govuk-table__caption govuk-table__caption--s">{caption}</caption>
      <tbody className="govuk-table__body">
        {lines.map((line) => (
          <tr className="govuk-table__row" key={line.label}>
            <th scope="row" className={line.total ? "govuk-table__header" : "govuk-table__cell"}>
              {line.label}
            </th>
            <td className="govuk-table__cell govuk-table__cell--numeric app-numeric">
              {line.total ? <strong>{line.value}</strong> : line.value}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** Micro-entity profit and loss account and balance sheet built from the answers. */
export function AccountsTables({ accounts }: { accounts: AccountsSummary }) {
  return (
    <>
      <StatementTable
        caption="Profit and loss account"
        lines={[
          { label: "Turnover", value: formatPounds(accounts.turnover) },
          { label: "Interest received", value: formatPounds(accounts.interest_income) },
          ...(accounts.other_income
            ? [
                {
                  label: "Other income (R&D and creative expenditure credits)",
                  value: formatPounds(accounts.other_income),
                },
              ]
            : []),
          { label: "Expenses", value: formatPounds(-accounts.total_expenses) },
          {
            label: "Profit before tax",
            value: formatPounds(accounts.profit_before_tax),
            total: true,
          },
          { label: "Corporation Tax", value: formatMoney(-Number(accounts.corporation_tax)) },
          { label: "Profit after tax", value: formatMoney(accounts.profit_after_tax), total: true },
        ]}
      />
      <StatementTable
        caption="Balance sheet"
        lines={[
          {
            label: "Called up share capital not paid",
            value: formatPounds(accounts.called_up_share_capital_not_paid),
          },
          { label: "Fixed assets", value: formatPounds(accounts.fixed_assets) },
          { label: "Current assets", value: formatPounds(accounts.current_assets) },
          {
            label: "Prepayments and accrued income",
            value: formatPounds(accounts.prepayments_and_accrued_income),
          },
          {
            label: "Creditors: amounts falling due within one year",
            value: formatPounds(-accounts.creditors_within_one_year),
          },
          { label: "Net current assets", value: formatPounds(accounts.net_current_assets) },
          {
            label: "Total assets less current liabilities",
            value: formatPounds(accounts.total_assets_less_current_liabilities),
          },
          {
            label: "Creditors: amounts falling due after more than one year",
            value: formatPounds(-accounts.creditors_after_one_year),
          },
          { label: "Provisions for liabilities", value: formatPounds(-accounts.provisions) },
          {
            label: "Accruals and deferred income",
            value: formatPounds(-accounts.accruals_and_deferred_income),
          },
          { label: "Net assets", value: formatPounds(accounts.net_assets), total: true },
          {
            label: "Called up share capital",
            value: formatPounds(accounts.called_up_share_capital),
          },
          {
            label: "Profit and loss reserve",
            value: formatPounds(accounts.profit_and_loss_reserve),
          },
          { label: "Total equity", value: formatPounds(accounts.net_assets), total: true },
        ]}
      />
    </>
  );
}
