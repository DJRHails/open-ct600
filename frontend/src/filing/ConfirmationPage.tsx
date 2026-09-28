import { Link, Navigate } from "react-router";

import { Panel, SummaryList, TwoThirds, usePageTitle } from "@/components/content";
import { paymentDue } from "@/components/TaxBreakdown";
import { useDraft } from "@/filing/draft";
import { TASK_LIST } from "@/filing/paths";
import { formatDate, formatMoney } from "@/format";

const RECEIVED_AT = new Intl.DateTimeFormat("en-GB", {
  dateStyle: "long",
  timeStyle: "short",
  timeZone: "Europe/London",
});

export function ConfirmationPage() {
  usePageTitle("Return submitted");
  const { receipt } = useDraft();

  if (receipt === null) return <Navigate to="/file" replace />;
  const { tax } = receipt.computation;
  return (
    <TwoThirds>
      <Panel title="Return submitted">
        Your reference number
        <br />
        <strong>{receipt.reference}</strong>
      </Panel>
      <p className="govuk-body">
        This was a demonstration: your return has <strong>not</strong> been sent to HMRC.
      </p>
      <SummaryList
        rows={[
          { key: "Company", value: receipt.company.name },
          { key: "Company registration number", value: receipt.company.registration_number },
          {
            key: "Accounting period",
            value: `${formatDate(tax.period_start)} to ${formatDate(tax.period_end)}`,
          },
          { key: "Corporation Tax to pay", value: formatMoney(tax.tax_chargeable) },
          { key: "Pay by", value: paymentDue(tax) },
          { key: "Signed by", value: receipt.signatory },
          { key: "Received", value: RECEIVED_AT.format(new Date(receipt.received_at)) },
          {
            key: "Return fingerprint",
            value: <code className="app-numeric">{receipt.fingerprint}</code>,
          },
        ]}
      />
      <p className="govuk-body">
        The fingerprint identifies exactly what you declared. Keep it with your records.
      </p>

      <h2 className="govuk-heading-m">What happens next</h2>
      <p className="govuk-body">
        To file this return for real, enter the same figures in HMRC-recognised software or give
        them to your accountant. The return is due by {formatDate(tax.filing_due)}, but Corporation
        Tax must be paid earlier, as shown under ‘Pay by’.
      </p>
      <p className="govuk-body app-no-print">
        <button
          type="button"
          className="govuk-link govuk-body app-link-button"
          onClick={() => window.print()}
        >
          Print this page
        </button>
      </p>
      <p className="govuk-body app-no-print">
        <Link className="govuk-link" to={TASK_LIST}>
          Start another return
        </Link>
      </p>
    </TwoThirds>
  );
}
