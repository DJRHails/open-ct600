import { useState } from "react";
import { useNavigate } from "react-router";

import { MoneyInput, TextInput } from "@/components/forms";
import { useDraft } from "@/filing/draft";
import {
  type AmountSection,
  type AmountSectionKey,
  type FieldErrors,
  validateAmounts,
} from "@/filing/model";
import { useNextPage } from "@/filing/paths";
import { SectionFrame } from "@/filing/SectionFrame";

/** A section of the return made up of amounts: profit and loss, adjustments, balance sheet. */
export function AmountSectionPage<K extends AmountSectionKey>({
  section,
}: {
  section: AmountSection<K>;
}) {
  const { draft, saveSection } = useDraft();
  const { next } = useNextPage();
  const navigate = useNavigate();
  const [values, setValues] = useState<Record<string, string>>(draft[section.key] ?? {});
  const [errors, setErrors] = useState<FieldErrors>({});

  function save() {
    const result = validateAmounts(section, values);
    if (!result.ok) {
      setErrors(result.errors);
      return;
    }
    saveSection(section.key, values);
    navigate(next);
  }

  return (
    <SectionFrame
      title={section.title}
      errors={errors}
      fieldOrder={section.fields.map((field) => field.key)}
      onSubmit={save}
      intro={section.intro}
    >
      {section.fields.map((field) => {
        const props = {
          id: field.key,
          label: field.label,
          hint: field.hint,
          value: values[field.key] ?? "",
          onChange: (value: string) => setValues({ ...values, [field.key]: value }),
          error: errors[field.key],
        };
        return field.kind === "count" ? (
          <TextInput key={field.key} {...props} width="3" inputMode="numeric" />
        ) : (
          <MoneyInput key={field.key} {...props} />
        );
      })}
    </SectionFrame>
  );
}
