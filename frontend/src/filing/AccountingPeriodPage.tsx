import { useState } from "react";
import { useNavigate } from "react-router";

import { PrefilledBanner } from "@/components/content";
import { DateInput } from "@/components/forms";
import { draftRecord, prefilledPeriod } from "@/filing/companiesHouse";
import { useDraft } from "@/filing/draft";
import { type FieldErrors, SECTION_TITLES, validatePeriod } from "@/filing/model";
import { useNextPage } from "@/filing/paths";
import { SectionFrame } from "@/filing/SectionFrame";

const EMPTY_DATE = { day: "", month: "", year: "" };

export function AccountingPeriodPage() {
  const { draft, saveSection } = useDraft();
  const { next } = useNextPage();
  const navigate = useNavigate();
  // Until the period is saved, Companies House's next period of account is the starting point.
  const [prefill] = useState(() => (draft.period ? null : prefilledPeriod(draftRecord(draft))));
  const [values, setValues] = useState(
    draft.period ?? prefill ?? { start: EMPTY_DATE, end: EMPTY_DATE },
  );
  const [errors, setErrors] = useState<FieldErrors>({});

  function save() {
    const result = validatePeriod(values);
    if (!result.ok) {
      setErrors(result.errors);
      return;
    }
    saveSection("period", { start: values.start, end: values.end });
    navigate(next);
  }

  return (
    <SectionFrame
      title={SECTION_TITLES.period}
      errors={errors}
      fieldOrder={["start", "end"]}
      inputId={(field) => `${field}-day`}
      onSubmit={save}
      intro="The accounting period for Corporation Tax can be up to 12 months. It usually matches your company's financial year."
      banner={prefill ? <PrefilledBanner /> : null}
    >
      {prefill?.note ? <div className="govuk-inset-text">{prefill.note}</div> : null}
      <DateInput
        id="start"
        legend="Start date"
        hint="For example, 1 4 2025"
        value={values.start}
        onChange={(start) => setValues({ ...values, start })}
        error={errors.start}
      />
      <DateInput
        id="end"
        legend="End date"
        hint="For example, 31 3 2026"
        value={values.end}
        onChange={(end) => setValues({ ...values, end })}
        error={errors.end}
      />
    </SectionFrame>
  );
}
