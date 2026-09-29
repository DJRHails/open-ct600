import { useState } from "react";
import { Navigate, useNavigate } from "react-router";

import { Radios } from "@/components/forms";
import { useDraft } from "@/filing/draft";
import { type FieldErrors, YES_NO } from "@/filing/model";
import { TASK_LIST, useNextPage } from "@/filing/paths";
import { RELIEF_TASKS } from "@/filing/payload";
import { type CreativeAnswers, validateCreative } from "@/filing/reliefs";
import { SectionFrame } from "@/filing/SectionFrame";

/** CT600P claims need the creatives additional information form before the return. */
export function CreativeFormPage() {
  const { draft, saveSection } = useDraft();
  const { next } = useNextPage();
  const navigate = useNavigate();
  const [values, setValues] = useState<CreativeAnswers>(
    draft.creative_industries ?? { additional_information_submitted: "" },
  );
  const [errors, setErrors] = useState<FieldErrors>({});
  if (!draft.chosen_pages?.includes("P")) return <Navigate to={TASK_LIST} replace />;

  function save() {
    const result = validateCreative(values);
    if (!result.ok) {
      setErrors(result.errors);
      return;
    }
    saveSection("creative_industries", values);
    navigate(next);
  }

  return (
    <SectionFrame
      title={RELIEF_TASKS.creative_industries.title}
      errors={errors}
      fieldOrder={["additional_information_submitted"]}
      onSubmit={save}
    >
      <Radios
        name="additional_information_submitted"
        legend="Has the company submitted the creative industries additional information form for this period?"
        hint="HMRC needs it before the return for any creative industries claim, and rejects claims made without it."
        options={YES_NO}
        value={values.additional_information_submitted}
        onChange={(answer) => setValues({ additional_information_submitted: answer })}
        error={errors.additional_information_submitted}
        inline
      />
    </SectionFrame>
  );
}
