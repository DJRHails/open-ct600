import { filingDeadline, paymentDeadline } from "@/filing/deadlines";
import { formatDate } from "@/format";

/**
 * The deadlines for an accounting period. Companies with profits over £1.5 million usually
 * pay in instalments instead (https://www.gov.uk/pay-corporation-tax).
 */
export function Deadlines({ periodEnd }: { periodEnd: string }) {
  return (
    <div className="govuk-inset-text" data-testid="deadlines">
      <p className="govuk-body">
        File your return by <strong>{formatDate(filingDeadline(periodEnd))}</strong>.
      </p>
      <p className="govuk-body">
        Pay Corporation Tax by <strong>{formatDate(paymentDeadline(periodEnd))}</strong>. If the
        company's profits are over £1.5 million, it usually pays in instalments instead.
      </p>
    </div>
  );
}
