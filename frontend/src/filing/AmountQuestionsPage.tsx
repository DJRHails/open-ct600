/**
 * A section of amounts asked as everyday questions: where an amount has a yes or no question
 * in front of it ("Did the company buy equipment, tools or vehicles for the business?"), the
 * amount is revealed on yes and is nil on no. Each question has help under it.
 */
import { useState } from "react";
import { useNavigate } from "react-router";

import { MoneyInput, Radios, TextInput } from "@/components/forms";
import { QuestionHelp } from "@/components/help";
import type { QuestionHelp as Help } from "@/content/help/types";
import { useDraft } from "@/filing/draft";
import {
  type AmountField,
  type AmountSection,
  type AmountSectionKey,
  type Draft,
  type FieldErrors,
  validateAmounts,
  YES_NO,
  type YesNo,
} from "@/filing/model";
import { useNextPage } from "@/filing/paths";
import { SectionFrame } from "@/filing/SectionFrame";
import { parseWholePounds } from "@/format";

type Values = Record<string, string>;
type Gates = Record<string, YesNo>;

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

type AmountProps<K extends AmountSectionKey> = {
  field: AmountField<K>;
  value: string;
  onChange: (value: string) => void;
  error: string | undefined;
  help: Help | undefined;
};

function Amount<K extends AmountSectionKey>({
  field,
  value,
  onChange,
  error,
  help,
}: AmountProps<K>) {
  const props = {
    id: field.key,
    label: field.label,
    hint: field.hint,
    value,
    onChange,
    error,
    help: help ? <QuestionHelp id={`${field.key}-help`} help={help} /> : undefined,
  };
  return field.kind === "count" ? (
    <TextInput {...props} width="3" inputMode="numeric" />
  ) : (
    <MoneyInput {...props} />
  );
}

type PageProps<K extends AmountSectionKey> = {
  section: AmountSection<K>;
  /** Help for each field, by its key. */
  help: Partial<Record<string, Help>>;
};

function asked<K extends AmountSectionKey>(
  section: AmountSection<K>,
  values: Values,
  draft: Draft,
) {
  return section.fields.filter((field) => field.askedWhen?.(values, draft) ?? true);
}

export function AmountQuestionsPage<K extends AmountSectionKey>({ section, help }: PageProps<K>) {
  const { draft, saveSection } = useDraft();
  const { next } = useNextPage();
  const navigate = useNavigate();
  const [values, setValues] = useState<Values>(draft[section.key] ?? {});
  const [gates, setGates] = useState<Gates>(() => initialGates(section, draft[section.key]));
  const [errors, setErrors] = useState<FieldErrors>({});
  const shown = asked(section, answeredAmounts(section, values, gates), draft);

  function save() {
    const answered = answeredAmounts(section, values, gates);
    const unanswered = gateErrors(section, values, gates);
    const result = validateAmounts(section, answered, draft);
    const found = { ...(result.ok ? {} : result.errors), ...unanswered };
    if (Object.keys(found).length > 0) {
      setErrors(found);
      return;
    }
    saveSection(section.key, answered);
    navigate(next);
  }

  const amount = (field: AmountField<K>, withHelp: boolean) => (
    <Amount
      field={field}
      value={values[field.key] ?? ""}
      onChange={(value) => setValues({ ...values, [field.key]: value })}
      error={errors[field.key]}
      help={withHelp ? help[field.key] : undefined}
    />
  );

  return (
    <SectionFrame
      title={section.title}
      errors={errors}
      fieldOrder={shown.flatMap((field) =>
        field.gate ? [gateId(field.key), field.key] : [field.key],
      )}
      onSubmit={save}
      intro={section.intro}
    >
      {shown.map((field) =>
        field.gate ? (
          <Radios
            key={field.key}
            name={gateId(field.key)}
            legend={field.gate.question}
            hint={field.gate.hint}
            options={YES_NO.map((option) =>
              option.value === "yes" ? { ...option, conditional: amount(field, false) } : option,
            )}
            value={gates[field.key] ?? ""}
            onChange={(answer) => setGates({ ...gates, [field.key]: answer })}
            error={errors[gateId(field.key)]}
            help={
              help[field.key] ? (
                <QuestionHelp id={`${field.key}-help`} help={help[field.key] as Help} />
              ) : undefined
            }
          />
        ) : (
          <div key={field.key}>{amount(field, true)}</div>
        ),
      )}
    </SectionFrame>
  );
}
