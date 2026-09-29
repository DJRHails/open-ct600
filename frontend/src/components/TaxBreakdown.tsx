import type { ReactNode } from "react";

import type { FinancialYearSlice, TaxBand, TaxComputation } from "@/api";
import { SummaryList } from "@/components/content";
import { formatDate, formatMoney, formatPercent, formatPounds } from "@/format";

const BAND_LABELS: Record<TaxBand, string> = {
  flat: "Single rate",
  small: "Small profits rate",
  marginal: "Main rate less marginal relief",
  main: "Main rate",
  fund: "Authorised investment fund rate",
};

/** When the tax must be paid: a date, or quarterly instalments for large companies. */
export function paymentDue(tax: TaxComputation): string {
  if (tax.may_pay_by_instalments) {
    return (
      "Profits are over the £1.5 million large company threshold, so you'll usually pay " +
      "in quarterly instalments during and after the period"
    );
  }
  return formatDate(tax.payment_due);
}

/** The tax due, when it must be paid, and when the return must be filed. */
export function TaxSummary({ tax }: { tax: TaxComputation }) {
  return (
    <SummaryList
      rows={[
        { key: "Profits chargeable to Corporation Tax", value: formatPounds(tax.taxable_profits) },
        {
          key: "Corporation Tax before marginal relief",
          value: formatMoney(tax.tax_before_relief),
        },
        { key: "Marginal relief", value: formatMoney(tax.marginal_relief) },
        {
          key: "Corporation Tax to pay",
          value: <strong>{formatMoney(tax.tax_chargeable)}</strong>,
        },
        { key: "Effective rate", value: formatPercent(tax.effective_rate) },
        { key: "Pay by", value: paymentDue(tax) },
        { key: "File your return by", value: formatDate(tax.filing_due) },
      ]}
    />
  );
}

/** One row per financial year the accounting period falls in. */
export function TaxBreakdownTable({ tax }: { tax: TaxComputation }) {
  return (
    <table className="govuk-table">
      <caption className="govuk-table__caption govuk-table__caption--m">
        How your tax is worked out
      </caption>
      <thead className="govuk-table__head">
        <tr className="govuk-table__row">
          <th scope="col" className="govuk-table__header">
            Financial year
          </th>
          <th scope="col" className="govuk-table__header">
            Rate applied
          </th>
          <th scope="col" className="govuk-table__header govuk-table__header--numeric">
            Profits
          </th>
          <th scope="col" className="govuk-table__header govuk-table__header--numeric">
            Tax
          </th>
          <th scope="col" className="govuk-table__header govuk-table__header--numeric">
            Marginal relief
          </th>
        </tr>
      </thead>
      <tbody className="govuk-table__body">{tax.slices.flatMap(sliceRows)}</tbody>
    </table>
  );
}

/** Bands with one rate and no lower and upper limits. */
const UNLIMITED_BANDS: TaxBand[] = ["flat", "fund"];

type RowProps = {
  slice: FinancialYearSlice;
  label: ReactNode;
  profits: number;
  tax: string;
  marginalRelief: number | string;
};

function Row({ slice, label, profits, tax, marginalRelief }: RowProps) {
  return (
    <tr className="govuk-table__row">
      <th scope="row" className="govuk-table__header">
        {slice.financial_year} to {slice.financial_year + 1}
        <span className="govuk-body-s govuk-!-display-block govuk-!-margin-bottom-0">
          {formatDate(slice.start)} to {formatDate(slice.end)} ({slice.days} days)
        </span>
      </th>
      <td className="govuk-table__cell">{label}</td>
      <td className="govuk-table__cell govuk-table__cell--numeric app-numeric">
        {formatPounds(profits)}
      </td>
      <td className="govuk-table__cell govuk-table__cell--numeric app-numeric">
        {formatMoney(tax)}
      </td>
      <td className="govuk-table__cell govuk-table__cell--numeric app-numeric">
        {formatMoney(marginalRelief)}
      </td>
    </tr>
  );
}

/**
 * A slice's lines, as on the CT600: its ordinary profits, then any ring fence profits at the
 * ring fence rate. The ordinary line is left out when a ring fence company has no other profits.
 */
function sliceRows(slice: FinancialYearSlice) {
  const ringFence = slice.ring_fence;
  const rows: ReactNode[] = [];
  if (slice.profits || !ringFence) {
    const ordinaryRelief = Number(slice.marginal_relief) - Number(ringFence?.marginal_relief ?? 0);
    rows.push(
      <Row
        key={`${slice.financial_year}-ordinary`}
        slice={slice}
        label={
          <>
            {BAND_LABELS[slice.band]} ({formatPercent(slice.rate)})
            {UNLIMITED_BANDS.includes(slice.band) ? null : (
              <span className="govuk-body-s govuk-!-display-block govuk-!-margin-bottom-0">
                Limits {formatPounds(slice.lower_limit)} to {formatPounds(slice.upper_limit)}
              </span>
            )}
          </>
        }
        profits={slice.profits}
        tax={slice.tax}
        marginalRelief={ordinaryRelief.toFixed(2)}
      />,
    );
  }
  if (ringFence) {
    rows.push(
      <Row
        key={`${slice.financial_year}-ring-fence`}
        slice={slice}
        label={`Ring fence profits (${formatPercent(ringFence.rate)})`}
        profits={ringFence.profits}
        tax={ringFence.tax}
        marginalRelief={ringFence.marginal_relief}
      />,
    );
  }
  return rows;
}
