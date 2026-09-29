/**
 * Amounts asked after a yes or no question in everyday words (``AmountField.gate``): the
 * amount is asked on yes and is 0 on no, so the saved amounts are what they always were.
 */
import type { AmountSection, AmountSectionKey, FieldErrors, YesNo } from "@/filing/model";
import { parseWholePounds } from "@/format";

type Values = Record<string, string>;
export type Gates = Record<string, YesNo>;

/** The id of an amount's yes or no question, which its errors link to. */
export function gateId(key: string): string {
  return `${key}-answer`;
}

/**
 * The yes or no answers implied by saved amounts: yes for an amount over 0, no otherwise,
 * and unanswered if the section has not been saved.
 */
export function initialGates<K extends AmountSectionKey>(
  section: AmountSection<K>,
  saved: Values | undefined,
): Gates {
  const gates: Gates = {};
  for (const field of section.fields) {
    if (!field.gate) continue;
    const amount = parseWholePounds(saved?.[field.key] ?? "", "amount");
    gates[field.key] = saved === undefined ? "" : amount.ok && amount.value > 0 ? "yes" : "no";
  }
  return gates;
}

/** The amounts to save: each amount whose question is answered no is 0. */
export function answeredAmounts<K extends AmountSectionKey>(
  section: AmountSection<K>,
  values: Values,
  gates: Gates,
): Values {
  const answered = { ...values };
  for (const field of section.fields) {
    if (field.gate && gates[field.key] !== "yes") answered[field.key] = "0";
  }
  return answered;
}

/** Unanswered questions, and amounts left blank after yes. */
export function gateErrors<K extends AmountSectionKey>(
  section: AmountSection<K>,
  values: Values,
  gates: Gates,
): FieldErrors {
  const errors: FieldErrors = {};
  for (const field of section.fields) {
    if (!field.gate) continue;
    if (!gates[field.key]) errors[gateId(field.key)] = field.gate.error;
    else if (gates[field.key] === "yes" && !(values[field.key] ?? "").trim()) {
      errors[field.key] = `Enter ${field.errorLabel}`;
    }
  }
  return errors;
}
