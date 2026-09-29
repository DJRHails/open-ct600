/**
 * When the return must be filed and the tax paid, worked out as soon as the accounting period
 * is known. The backend works them out the same way (``open_ct600.tax.payment_due_date`` and
 * ``filing_due_date``); both are tested against ``backend/tests/fixtures/deadlines.json``.
 */

/** ``iso`` plus ``months`` calendar months, on the last day of a shorter month if need be. */
function addMonths(iso: string, months: number): string {
  const [year = 0, month = 1, day = 1] = iso.split("-").map(Number);
  const monthIndex = month - 1 + months;
  const lastDay = new Date(Date.UTC(year, monthIndex + 1, 0)).getUTCDate();
  return new Date(Date.UTC(year, monthIndex, Math.min(day, lastDay))).toISOString().slice(0, 10);
}

function dayAfter(iso: string): string {
  const date = new Date(`${iso}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + 1);
  return date.toISOString().slice(0, 10);
}

/** 12 months after the period ends (https://www.gov.uk/company-tax-returns). */
export function filingDeadline(periodEnd: string): string {
  return addMonths(periodEnd, 12);
}

/**
 * 9 months and 1 day after the period ends: 9 months after the day after it, so a period
 * ending 30 June is due on 1 April (https://www.gov.uk/pay-corporation-tax).
 */
export function paymentDeadline(periodEnd: string): string {
  return addMonths(dayAfter(periodEnd), 9);
}
