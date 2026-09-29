/**
 * Prefill from Companies House: whether lookup is on, and the answers a company's public record
 * gives each section. Everything prefilled stays editable, and a section is only prefilled until
 * the user saves it.
 */
import { useEffect, useState } from "react";

import { api, type CompanyRecord, type LegalForm } from "@/api";
import type { DateParts } from "@/components/forms";
import type { Draft } from "@/filing/model";
import { isoToDateParts } from "@/format";

/** The draft's company number, normalised as ``validateCompany`` does. */
function normalisedNumber(number: string): string {
  return number.replace(/\s+/g, "").toUpperCase();
}

/**
 * The Companies House record for the company being filed. A record stops applying once the
 * company number is changed to another company's, so its directors and figures never leak into
 * the wrong return.
 */
export function companyRecord(
  record: CompanyRecord | undefined,
  registrationNumber: string | undefined,
): CompanyRecord | null {
  if (!record) return null;
  if (registrationNumber === undefined) return record;
  return normalisedNumber(registrationNumber) === normalisedNumber(record.number) ? record : null;
}

/** The record for the draft's company, if one was chosen from Companies House. */
export function draftRecord(draft: Draft): CompanyRecord | null {
  return companyRecord(draft.companies_house, draft.company?.registration_number);
}

export type LookupStatus = "checking" | "enabled" | "disabled";

/** Whether Companies House lookup is switched on; off if the service cannot say. */
export function useCompaniesHouseLookup(): LookupStatus {
  const [status, setStatus] = useState<LookupStatus>("checking");
  useEffect(() => {
    let current = true;
    api.companiesHouseEnabled().then(
      (enabled) => current && setStatus(enabled ? "enabled" : "disabled"),
      () => current && setStatus("disabled"),
    );
    return () => {
      current = false;
    };
  }, []);
  return status;
}

/** The return's period from the record, and the note explaining it, if any. */
export function prefilledPeriod(
  record: CompanyRecord | null,
): { start: DateParts; end: DateParts; note: string | null } | null {
  const suggested = record?.suggested_period;
  if (!suggested) return null;
  return {
    start: isoToDateParts(suggested.start),
    end: isoToDateParts(suggested.end),
    note: suggested.note,
  };
}

export const LEGAL_FORMS: { value: LegalForm; label: string }[] = [
  { value: "private-limited-company", label: "Private company limited by shares" },
  { value: "private-company-limited-by-guarantee", label: "Private company limited by guarantee" },
  { value: "private-unlimited-company", label: "Private unlimited company" },
  { value: "community-interest-company", label: "Community interest company" },
];

/** Companies House's legal form, if it is one the accounts can be prepared for. */
export function supportedLegalForm(record: CompanyRecord | null): LegalForm | "" {
  const form = LEGAL_FORMS.find((option) => option.value === record?.legal_form);
  return form ? form.value : "";
}

/**
 * Whether this is the company's first period of account, as far as the record shows: it has
 * never filed accounts. ``""`` when there is no record to go on.
 */
export function firstPeriodFromRecord(record: CompanyRecord | null): "yes" | "no" | "" {
  if (!record) return "";
  return record.accounts.last_made_up_to === null ? "yes" : "no";
}

/** The names of the company's current directors, in Companies House's order. */
export function currentDirectors(record: CompanyRecord | null): string[] {
  return record ? record.directors.map((director) => director.name) : [];
}
