/**
 * When the return must be filed and the tax paid, worked out as soon as the accounting period
 * is known. The backend works them out the same way (``open_ct600.tax.payment_due_date`` and
 * ``filing_due_date``); both are tested against ``backend/tests/fixtures/deadlines.json``.
 */
import { addDays, addMonths } from "@/format";

/** 12 months after the period ends (https://www.gov.uk/company-tax-returns). */
export function filingDeadline(periodEnd: string): string {
  return addMonths(periodEnd, 12);
}

/**
 * "The day following the expiry of nine months from the end of that period" (TMA 1970 s59D).
 * Nine months from the day after the period end, like 1 April for a period ending 30 June. When
 * that month has no such day, the nine months end with the month, so tax is due on the 1st of
 * the next: a period ending 30 May is due on 1 March, never 28 February.
 */
export function paymentDeadline(periodEnd: string): string {
  const from = addDays(periodEnd, 1);
  const due = addMonths(from, 9);
  const clamped = due.slice(8) !== from.slice(8);
  return clamped ? addDays(due, 1) : due;
}
