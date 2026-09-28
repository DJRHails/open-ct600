import type { DateParts } from "@/components/forms";

const POUNDS = new Intl.NumberFormat("en-GB", {
  style: "currency",
  currency: "GBP",
  maximumFractionDigits: 0,
});
const MONEY = new Intl.NumberFormat("en-GB", {
  style: "currency",
  currency: "GBP",
  minimumFractionDigits: 2,
});
const LONG_DATE = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});

/** Whole pounds, like £1,250. */
export function formatPounds(value: number | string): string {
  return POUNDS.format(withoutNegativeZero(value));
}

/** Pounds and pence, like £1,250.00. */
export function formatMoney(value: number | string): string {
  return MONEY.format(withoutNegativeZero(value));
}

/** A rate given as a fraction ("0.2275") or a percentage number (25), like 22.75%. */
export function formatPercent(value: number | string, isFraction = true): string {
  const percent = Number(value) * (isFraction ? 100 : 1);
  return `${Number(percent.toFixed(2))}%`;
}

/** An ISO date (2026-01-01) in GOV.UK style, like 1 January 2026. */
export function formatDate(iso: string): string {
  const [year, month, day] = iso.split("-").map(Number);
  return LONG_DATE.format(new Date(Date.UTC(year ?? 0, (month ?? 1) - 1, day ?? 1)));
}

export type Parsed<T> = { ok: true; value: T } | { ok: false; error: string };

const MAX_POUNDS = 99_999_999_999;

/**
 * Parse a whole-pounds amount. Commas, spaces and a leading £ are allowed.
 * An empty answer is 0 unless the field is required.
 */
export function parseWholePounds(raw: string, label: string, required = false): Parsed<number> {
  const cleaned = raw.replace(/[\s,]/g, "").replace(/^£/, "");
  if (cleaned === "") {
    return required ? { ok: false, error: `Enter ${label}` } : { ok: true, value: 0 };
  }
  if (/^-/.test(cleaned)) {
    return { ok: false, error: `${capitalise(label)} cannot be negative` };
  }
  if (/^\d+\.\d*$/.test(cleaned)) {
    return { ok: false, error: `Enter ${label} in whole pounds, without pence` };
  }
  if (!/^\d+$/.test(cleaned)) {
    return { ok: false, error: `${capitalise(label)} must be a number, like 12500` };
  }
  const value = Number(cleaned);
  if (value > MAX_POUNDS) {
    return { ok: false, error: `${capitalise(label)} must be £99,999,999,999 or less` };
  }
  return { ok: true, value };
}

/** Parse a whole count, like a number of associated companies. */
export function parseCount(raw: string, label: string, max: number): Parsed<number> {
  const cleaned = raw.trim();
  if (cleaned === "") return { ok: true, value: 0 };
  if (!/^\d+$/.test(cleaned)) {
    return { ok: false, error: `${capitalise(label)} must be a whole number, like 2` };
  }
  const value = Number(cleaned);
  if (value > max) return { ok: false, error: `${capitalise(label)} must be ${max} or fewer` };
  return { ok: true, value };
}

/** Turn GOV.UK date input parts into an ISO date, with GOV.UK-style error messages. */
export function parseDateParts(parts: DateParts, label: string): Parsed<string> {
  const day = parts.day.trim();
  const month = parts.month.trim();
  const year = parts.year.trim();
  if (!day && !month && !year) return { ok: false, error: `Enter the ${label}` };
  const missing = [!day && "day", !month && "month", !year && "year"].filter(Boolean);
  if (missing.length > 0) {
    return { ok: false, error: `${capitalise(label)} must include a ${missing.join(" and ")}` };
  }
  if (!/^\d{1,2}$/.test(day) || !/^\d{1,2}$/.test(month) || !/^\d{4}$/.test(year)) {
    return { ok: false, error: `${capitalise(label)} must be a real date` };
  }
  const date = new Date(Date.UTC(Number(year), Number(month) - 1, Number(day)));
  const isReal =
    date.getUTCFullYear() === Number(year) &&
    date.getUTCMonth() === Number(month) - 1 &&
    date.getUTCDate() === Number(day);
  if (!isReal) return { ok: false, error: `${capitalise(label)} must be a real date` };
  return { ok: true, value: date.toISOString().slice(0, 10) };
}

export function isoToDateParts(iso: string): DateParts {
  const [year = "", month = "", day = ""] = iso.split("-");
  return { day: String(Number(day)), month: String(Number(month)), year };
}

/** The last day of a twelve-month period starting on ``startIso``. */
export function twelveMonthPeriodEnd(startIso: string): string {
  const [year, month, day] = startIso.split("-").map(Number);
  if (month === 2 && day === 29) return `${(year ?? 0) + 1}-02-28`;
  const end = new Date(Date.UTC((year ?? 0) + 1, (month ?? 1) - 1, day ?? 1));
  end.setUTCDate(end.getUTCDate() - 1);
  return end.toISOString().slice(0, 10);
}

function capitalise(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** Avoid "-£0" for amounts that are zero after negation. */
function withoutNegativeZero(value: number | string): number {
  const amount = Number(value);
  return amount === 0 ? 0 : amount;
}
