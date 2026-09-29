import { Link, Navigate } from "react-router";

import { Panel, SummaryList, TwoThirds, usePageTitle } from "@/components/content";
import { paymentDue } from "@/components/TaxBreakdown";
import { saveFile } from "@/filing/Downloads";
import { type Receipt, useDraft } from "@/filing/draft";
import { TASK_LIST } from "@/filing/paths";
import { formatDate, formatMoney } from "@/format";

const RECEIVED_AT = new Intl.DateTimeFormat("en-GB", {
  dateStyle: "long",
  timeStyle: "short",
  timeZone: "Europe/London",
});

function PrintAndRestart() {
  return (
    <>
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
    </>
  );
}

function DemoConfirmation({ receipt }: { receipt: Extract<Receipt, { kind: "demo" }> }) {
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
      <PrintAndRestart />
    </TwoThirds>
  );
}

function HmrcConfirmation({ receipt }: { receipt: Extract<Receipt, { kind: "hmrc" }> }) {
  const test = receipt.environment === "test-in-live";
  const { period } = receipt;
  const accepted = receipt.accepted_time
    ? RECEIVED_AT.format(new Date(receipt.accepted_time))
    : "HMRC did not say";
  const filename = `hmrc-receipt-${receipt.correlation_id || receipt.irmark_base32}.xml`;
  return (
    <TwoThirds>
      <Panel title={test ? "HMRC accepted your test submission" : "Return submitted to HMRC"}>
        HMRC's receipt reference (IRmark)
        <br />
        <strong className="app-numeric">{receipt.irmark_base32}</strong>
      </Panel>
      {test ? (
        <p className="govuk-body">
          This was a test in HMRC's live service. HMRC checked your return but has{" "}
          <strong>not</strong> filed it. Submit it to HMRC when you are ready.
        </p>
      ) : (
        <p className="govuk-body">HMRC has received and accepted the company's return.</p>
      )}
      <SummaryList
        rows={[
          { key: "Company", value: receipt.company.name },
          { key: "Company registration number", value: receipt.company.registration_number },
          {
            key: "Accounting period",
            value: `${formatDate(period.start)} to ${formatDate(period.end)}`,
          },
          { key: "Signed by", value: receipt.signatory },
          { key: "Accepted by HMRC", value: accepted },
          {
            key: "Correlation ID",
            value: <code className="app-numeric">{receipt.correlation_id || "None"}</code>,
          },
        ]}
      />
      {receipt.messages.length > 0 ? (
        <div className="govuk-inset-text">
          {receipt.messages.map((message) => (
            <p className="govuk-body" key={message}>
              {message}
            </p>
          ))}
        </div>
      ) : null}
      <p className="govuk-body">
        Keep the IRmark and HMRC's signed receipt with the company's records. They prove what the
        company sent and when HMRC accepted it.
      </p>
      <p className="govuk-body app-no-print">
        <button
          type="button"
          className="govuk-link govuk-body app-link-button"
          onClick={() =>
            saveFile(new Blob([receipt.receipt_xml], { type: "application/xml" }), filename)
          }
        >
          Download HMRC's receipt (XML)
        </button>
      </p>
      <PrintAndRestart />
    </TwoThirds>
  );
}

export function ConfirmationPage() {
  const { receipt } = useDraft();
  const title =
    receipt?.kind === "hmrc" && receipt.environment === "test-in-live"
      ? "Test submission accepted"
      : "Return submitted";
  usePageTitle(title);

  if (receipt === null) return <Navigate to="/file" replace />;
  if (receipt.kind === "demo") return <DemoConfirmation receipt={receipt} />;
  return <HmrcConfirmation receipt={receipt} />;
}
