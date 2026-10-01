import { useState } from "react";
import { useNavigate } from "react-router";

import { TextInput } from "@/components/forms";
import { QuestionHelp } from "@/components/help";
import { REPAYMENT_HELP } from "@/content/help/repayment";
import { useDraft } from "@/filing/draft";
import type { FieldErrors } from "@/filing/model";
import { useNextPage } from "@/filing/paths";
import { RELIEF_TASKS } from "@/filing/payload";
import {
  EMPTY_REPAYMENT,
  REPAYMENT_FIELDS,
  type RepaymentAnswers,
  validateRepayment,
} from "@/filing/repayment";
import { SectionFrame } from "@/filing/SectionFrame";

type Field = {
  key: keyof RepaymentAnswers;
  label: string;
  hint?: string;
  width?: "5" | "10" | "20";
  numeric?: boolean;
};

/** The fields of the GOV.UK bank details pattern, with the bank's name HMRC also needs. */
const FIELDS: Field[] = [
  { key: "bank_name", label: "Name of bank or building society", width: "20" },
  { key: "account_name", label: "Name on the account", width: "20" },
  {
    key: "sort_code",
    label: "Sort code",
    hint: "Must be 6 digits long",
    width: "5",
    numeric: true,
  },
  {
    key: "account_number",
    label: "Account number",
    hint: "Must be 8 digits long. If yours is 6 or 7 digits, add zeros to the start",
    width: "10",
    numeric: true,
  },
  {
    key: "building_society_reference",
    label: "Building society roll number (if you have one)",
    hint: "You can find it on your card, statement or passbook",
    width: "10",
  },
];

/** CT600 boxes 920 to 940: the account HMRC pays money due back to the company into. */
export function RepaymentPage() {
  const { draft, saveSection } = useDraft();
  const { next } = useNextPage();
  const navigate = useNavigate();
  const [values, setValues] = useState<RepaymentAnswers>({
    ...EMPTY_REPAYMENT,
    ...draft.repayment,
  });
  const [errors, setErrors] = useState<FieldErrors>({});

  function save() {
    const result = validateRepayment(values);
    if (!result.ok) {
      setErrors(result.errors);
      return;
    }
    saveSection("repayment", values);
    navigate(next);
  }

  return (
    <SectionFrame
      title={RELIEF_TASKS.repayment.title}
      errors={errors}
      fieldOrder={REPAYMENT_FIELDS}
      onSubmit={save}
      intro="HMRC pays money due back to the company, such as a payable credit or tax it overpaid, into this account. Give the company’s own bank or building society account."
    >
      {FIELDS.map((field) => (
        <TextInput
          key={field.key}
          id={field.key}
          label={field.label}
          hint={field.hint}
          value={values[field.key]}
          onChange={(value) => setValues({ ...values, [field.key]: value })}
          error={errors[field.key]}
          width={field.width}
          inputMode={field.numeric ? "numeric" : "text"}
          spellCheck={false}
          autoComplete="off"
          help={<QuestionHelp id={`${field.key}-help`} help={REPAYMENT_HELP[field.key]} />}
        />
      ))}
    </SectionFrame>
  );
}
