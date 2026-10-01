/**
 * Bank details for a repayment (CT600 boxes 920 to 940): the account HMRC pays money due back
 * into. HMRC's guide says payable R&D and creative credits need them, and a repayment of £100
 * or less is held back without them, so they are asked whenever the computation shows money
 * due back. The checks mirror the backend's (``open_ct600.repayment``), which come from
 * HMRC's schema; the messages follow the GOV.UK bank details pattern.
 */
import type { BankDetails, CT600Box } from "@/api";
import type { FieldErrors, Validated } from "@/filing/model";

/** The bank details as typed. */
export type RepaymentAnswers = {
  bank_name: string;
  account_name: string;
  sort_code: string;
  account_number: string;
  /** Optional: blank when the account has no building society roll number. */
  building_society_reference: string;
};

export const EMPTY_REPAYMENT: RepaymentAnswers = {
  bank_name: "",
  account_name: "",
  sort_code: "",
  account_number: "",
  building_society_reference: "",
};

/** The fields in page order, so errors are listed top to bottom. */
export const REPAYMENT_FIELDS: (keyof RepaymentAnswers)[] = [
  "bank_name",
  "account_name",
  "sort_code",
  "account_number",
  "building_society_reference",
];

/**
 * Boxes that show money due back: tax overpaid (including surplus credits) and the payable R&D
 * and creative credits, as the backend's ``REPAYMENT_BOXES``.
 */
const REPAYMENT_BOXES = new Set(["605", "875", "880", "885", "886"]);

export function moneyDueBack(boxes: CT600Box[]): boolean {
  return boxes.some((box) => REPAYMENT_BOXES.has(box.box) && Number(box.value) > 0);
}

/** The characters HMRC's schema allows in names (``CT_CTstringType``). */
const ALLOWED_TEXT = /^[A-Za-z0-9 ,.()/&'\-"!%*_+:@<>?=;]*$/;
const ALLOWED_DESCRIPTION =
  "letters a to z, numbers, spaces and these characters: , . ( ) / & ' - \" ! % * _ + : @ < > ? = ;";
/** Spaces, hyphens and en dashes people write sort codes and account numbers with. */
const SEPARATORS = /[\s\-–]/g;
const DIGITS = /^\d+$/;

type TextRule = { label: string; missing: string; min: number; max: number };

const TEXT_RULES = {
  bank_name: {
    label: "Name of the bank or building society",
    missing: "Enter the name of the bank or building society",
    min: 2,
    max: 56,
  },
  account_name: {
    label: "Name on the account",
    missing: "Enter the name on the account",
    min: 2,
    max: 28,
  },
  building_society_reference: {
    label: "Building society roll number",
    missing: "",
    min: 2,
    max: 18,
  },
} satisfies Record<string, TextRule>;

function textProblem(value: string, rule: TextRule): string | null {
  if (!value) return rule.missing || null;
  if (value.length < rule.min) return `${rule.label} must be ${rule.min} characters or more`;
  if (value.length > rule.max) return `${rule.label} must be ${rule.max} characters or fewer`;
  if (!ALLOWED_TEXT.test(value)) return `${rule.label} must only include ${ALLOWED_DESCRIPTION}`;
  return null;
}

type DigitsRule = { length: number; missing: string; invalid: string; wrongLength: string };

const SORT_CODE: DigitsRule = {
  length: 6,
  missing: "Enter a sort code",
  invalid: "Enter a valid sort code like 309430",
  wrongLength: "Sort code must be 6 digits long",
};

const ACCOUNT_NUMBER: DigitsRule = {
  length: 8,
  missing: "Enter an account number",
  invalid: "Enter a valid account number like 00733445",
  wrongLength:
    "Account number must be 8 digits long. If yours is 6 or 7 digits, add zeros to the start",
};

function digits(
  value: string,
  rule: DigitsRule,
): { ok: true; value: string } | { ok: false; error: string } {
  const plain = value.replace(SEPARATORS, "");
  if (!plain) return { ok: false, error: rule.missing };
  if (!DIGITS.test(plain)) return { ok: false, error: rule.invalid };
  if (plain.length !== rule.length) return { ok: false, error: rule.wrongLength };
  return { ok: true, value: plain };
}

/** Check the bank details as HMRC's schema would, giving them in the form HMRC takes. */
export function validateRepayment(answers: RepaymentAnswers): Validated<BankDetails> {
  const trimmed = Object.fromEntries(
    REPAYMENT_FIELDS.map((field) => [field, (answers[field] ?? "").trim()]),
  ) as RepaymentAnswers;
  const errors: FieldErrors = {};
  for (const field of ["bank_name", "account_name", "building_society_reference"] as const) {
    const problem = textProblem(trimmed[field], TEXT_RULES[field]);
    if (problem) errors[field] = problem;
  }
  const sortCode = digits(trimmed.sort_code, SORT_CODE);
  const accountNumber = digits(trimmed.account_number, ACCOUNT_NUMBER);
  if (!sortCode.ok) errors.sort_code = sortCode.error;
  if (!accountNumber.ok) errors.account_number = accountNumber.error;
  if (!sortCode.ok || !accountNumber.ok || Object.keys(errors).length > 0) {
    return { ok: false, errors };
  }
  return {
    ok: true,
    value: {
      bank_name: trimmed.bank_name,
      sort_code: sortCode.value,
      account_number: accountNumber.value,
      account_name: trimmed.account_name,
      building_society_reference: trimmed.building_society_reference || null,
    },
  };
}

/** A sort code as people read it, like 30-94-30. */
export function formatSortCode(sortCode: string): string {
  return sortCode.replace(/^(\d{2})(\d{2})(\d{2})$/, "$1-$2-$3");
}
