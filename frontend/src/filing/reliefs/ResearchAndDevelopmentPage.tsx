import { useState } from "react";
import { useNavigate } from "react-router";

import type { ResearchAndDevelopmentClaimScheme } from "@/api";
import { MoneyInput, Radios, TextInput } from "@/components/forms";
import { useDraft } from "@/filing/draft";
import { type FieldErrors, savedPeriod, YES_NO, type YesNo } from "@/filing/model";
import { useNextPage } from "@/filing/paths";
import { RELIEF_TASKS } from "@/filing/payload";
import {
  EMPTY_RESEARCH,
  type ResearchAnswers,
  researchQuestions,
  schemesFor,
  validateResearch,
} from "@/filing/reliefs";
import { SectionFrame } from "@/filing/SectionFrame";

const SCHEMES: Record<ResearchAndDevelopmentClaimScheme, { label: string; hint: string }> = {
  sme: {
    label: "SME scheme",
    hint: "An additional deduction from profits, for small and medium-sized enterprises with periods starting before 1 April 2024.",
  },
  rdec: {
    label: "Research and development expenditure credit (RDEC)",
    hint: "A taxable credit: the merged scheme for periods starting on or after 1 April 2024, or the large company scheme before then.",
  },
  eris: {
    label: "Enhanced R&D intensive support (ERIS)",
    hint: "For loss-making SMEs that spend at least 30% of their total expenditure on R&D, for periods starting on or after 1 April 2024.",
  },
};

const FIELD_ORDER = [
  "claiming",
  "scheme",
  "company_is_sme",
  "qualifying_expenditure",
  "rdec_expenditure",
  "intensity",
  "claim_payable_credit",
  "rd_workers_paye_and_nic",
  "claimed_in_previous_three_years",
  "claim_notification_submitted",
  "additional_information_submitted",
];

type YesNoQuestion = {
  name: keyof ResearchAnswers;
  legend: string;
  hint?: string;
};

function Claim({ values, set, errors, start }: ClaimProps) {
  const shown = researchQuestions(values, start);
  const yesNo = ({ name, legend, hint }: YesNoQuestion) => (
    <Radios
      name={name}
      legend={legend}
      hint={hint}
      options={YES_NO}
      value={values[name] as YesNo}
      onChange={(answer) => set({ [name]: answer })}
      error={errors[name]}
      inline
    />
  );
  const text = (name: keyof ResearchAnswers) => ({
    id: name,
    value: values[name],
    onChange: (value: string) => set({ [name]: value }),
    error: errors[name],
  });
  return (
    <>
      <Radios
        name="scheme"
        legend="Which scheme is the company claiming under?"
        options={schemesFor(start).map((scheme) => ({ value: scheme, ...SCHEMES[scheme] }))}
        value={values.scheme}
        onChange={(scheme) => set({ scheme })}
        error={errors.scheme}
      />
      {shown.companyIsSme
        ? yesNo({
            name: "company_is_sme",
            legend: "Is the company a small or medium-sized enterprise (SME)?",
            hint: "HMRC records a merged-scheme claim as an SME claim or a large company claim.",
          })
        : null}
      <MoneyInput
        {...text("qualifying_expenditure")}
        label="Qualifying R&D expenditure"
        hint="Staff costs, subcontractors, consumables, software and other costs that qualify for relief, in whole pounds."
      />
      {shown.rdecExpenditure ? (
        <MoneyInput
          {...text("rdec_expenditure")}
          label="Expenditure the company claims RDEC on (optional)"
          hint="Work subcontracted to the company by a large company, or subsidised or capped expenditure. Enter the credit itself in box L185 or L190 of CT600L."
        />
      ) : null}
      {shown.intensity ? (
        <TextInput
          {...text("intensity")}
          label={values.scheme === "eris" ? "R&D intensity" : "R&D intensity (optional)"}
          hint="Relevant R&D expenditure as a percentage of the company's total relevant expenditure. ERIS needs at least 30%; an SME scheme claim only needs it for the R&D-intensive credit (40%)."
          suffix="%"
          width="5"
          inputMode="decimal"
        />
      ) : null}
      {shown.payableCredit
        ? yesNo({
            name: "claim_payable_credit",
            legend: "Is the company surrendering a loss for a payable tax credit?",
            hint: "If so, also complete CT600L.",
          })
        : null}
      {shown.workersPayeAndNic ? (
        <MoneyInput
          {...text("rd_workers_paye_and_nic")}
          label="PAYE and National Insurance on R&D workers (optional)"
          hint="For large company RDEC before 1 April 2024, this can limit the credit at step 3 of CT600L."
        />
      ) : null}
      {yesNo({
        name: "claimed_in_previous_three_years",
        legend: "Has the company claimed R&D relief in the 3 years before this claim?",
      })}
      {shown.notification
        ? yesNo({
            name: "claim_notification_submitted",
            legend: "Did the company send HMRC a claim notification form for this period?",
            hint: "Companies that have not claimed in the last 3 years must notify HMRC within 6 months of the end of the period.",
          })
        : null}
      {yesNo({
        name: "additional_information_submitted",
        legend: "Has the company submitted the R&D additional information form?",
        hint: "HMRC needs it before the return. It removes claims made without it.",
      })}
    </>
  );
}

type ClaimProps = {
  values: ResearchAnswers;
  set: (change: Partial<ResearchAnswers>) => void;
  errors: FieldErrors;
  start: string | undefined;
};

/** Whether the company claims R&D relief and, if so, the claim details CT600L has no box for. */
export function ResearchAndDevelopmentPage() {
  const { draft, saveSection } = useDraft();
  const { next } = useNextPage();
  const navigate = useNavigate();
  const start = savedPeriod(draft)?.start;
  const [values, setValues] = useState<ResearchAnswers>({
    ...EMPTY_RESEARCH,
    ...draft.research_and_development,
  });
  const [errors, setErrors] = useState<FieldErrors>({});
  const set = (change: Partial<ResearchAnswers>) => setValues({ ...values, ...change });

  function save() {
    const result = validateResearch(values, start);
    if (!result.ok) {
      setErrors(result.errors);
      return;
    }
    saveSection("research_and_development", values);
    navigate(next);
  }

  return (
    <SectionFrame
      title={RELIEF_TASKS.research_and_development.title}
      errors={errors}
      fieldOrder={FIELD_ORDER}
      onSubmit={save}
      intro="Research and development relief reduces tax for companies that spend money on projects seeking an advance in science or technology. Claim RDEC or a payable tax credit on supplementary page CT600L as well."
    >
      <Radios
        name="claiming"
        legend="Is the company claiming research and development (R&D) relief for this period?"
        options={YES_NO}
        value={values.claiming}
        onChange={(claiming) => set({ claiming })}
        error={errors.claiming}
        inline
      />
      {values.claiming === "yes" ? (
        <Claim values={values} set={set} errors={errors} start={start} />
      ) : null}
    </SectionFrame>
  );
}
