import { useState } from "react";
import { Navigate, useNavigate } from "react-router";

import type { SchemaPage } from "@/api";
import { MoneyInput, TextInput } from "@/components/forms";
import { QuestionHelp } from "@/components/help";
import { SURRENDERER_HELP } from "@/content/help/reliefs";
import { useDraft } from "@/filing/draft";
import type { FieldErrors } from "@/filing/model";
import { TASK_LIST, useNextPage } from "@/filing/paths";
import { pageTree, RELIEF_TASKS } from "@/filing/payload";
import {
  type SurrendererAnswers,
  type SurrendererFigures,
  surrendererId,
  surrenderingCompanies,
  validateSurrenderers,
} from "@/filing/reliefs";
import { SectionFrame } from "@/filing/SectionFrame";
import { SchemaGate } from "@/filing/supplementary/SchemaGate";

const TITLE = RELIEF_TASKS.group_relief_surrenderers.title;
const FIELDS: (keyof SurrendererFigures)[] = [
  "surrenderable_amount",
  "surrendered_to_others",
  "consortium_share",
];
const BLANK: SurrendererFigures = {
  surrenderable_amount: "",
  surrendered_to_others: "",
  consortium_share: "",
};

function Surrenderers({ pages }: { pages: SchemaPage[] }) {
  const { draft, saveSection } = useDraft();
  const { next } = useNextPage();
  const navigate = useNavigate();
  const ct600c = pageTree(draft, pages, "C");
  const [values, setValues] = useState<SurrendererAnswers>(draft.group_relief_surrenderers ?? {});
  const [errors, setErrors] = useState<FieldErrors>({});
  const companies = ct600c ? surrenderingCompanies(ct600c) : [];
  if (companies.length === 0) return <Navigate to={TASK_LIST} replace />;

  function save() {
    const result = validateSurrenderers(values, companies);
    if (!result.ok) {
      setErrors(result.errors);
      return;
    }
    const known = companies.map(({ reference }) => reference);
    const kept = Object.entries(values).filter(([reference]) => known.includes(reference));
    saveSection("group_relief_surrenderers", Object.fromEntries(kept));
    navigate(next);
  }

  return (
    <SectionFrame
      title={TITLE}
      errors={errors}
      fieldOrder={companies.flatMap((_, index) =>
        FIELDS.map((field) => surrendererId(index, field)),
      )}
      onSubmit={save}
      intro="If you have figures from the surrendering companies' own returns, we use them to check that each claim is no more than the company can surrender for the overlapping period. Leave a company blank if you do not have them."
    >
      {companies.map(({ reference, name }, index) => {
        const figures = values[reference] ?? BLANK;
        const field = (key: keyof SurrendererFigures) => ({
          id: surrendererId(index, key),
          value: figures[key],
          onChange: (value: string) =>
            setValues((current) => ({
              ...current,
              [reference]: { ...BLANK, ...current[reference], [key]: value },
            })),
          error: errors[surrendererId(index, key)],
          // The questions are the same for every company, so their help is under the first's.
          help:
            index === 0 ? (
              <QuestionHelp id={`${key}-help`} help={SURRENDERER_HELP[key]} />
            ) : undefined,
        });
        return (
          <div className="govuk-form-group" key={reference}>
            <fieldset className="govuk-fieldset">
              <legend className="govuk-fieldset__legend govuk-fieldset__legend--m">
                {name ? `${name} (${reference})` : reference}
              </legend>
              <MoneyInput
                {...field("surrenderable_amount")}
                label="Amount it can surrender for its accounting period (optional)"
                hint="The maximum available for surrender on its own Company Tax Return."
              />
              <MoneyInput
                {...field("surrendered_to_others")}
                label="Amount it has already surrendered to other companies (optional)"
                hint="For the part of its period that overlaps this company's accounting period."
              />
              <TextInput
                {...field("consortium_share")}
                label="Consortium share (optional)"
                hint="For consortium claims only: the lowest of this company's percentages of the surrendering company's shares, profits, assets and votes."
                suffix="%"
                width="5"
                inputMode="decimal"
              />
            </fieldset>
          </div>
        );
      })}
    </SectionFrame>
  );
}

/** Optional figures from CT600C's surrendering companies, to limit each group relief claim. */
export function SurrenderersPage() {
  return <SchemaGate title={TITLE}>{(pages) => <Surrenderers pages={pages} />}</SchemaGate>;
}
