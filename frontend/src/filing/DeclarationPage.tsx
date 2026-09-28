import { type FormEvent, useMemo, useState } from "react";
import { Navigate } from "react-router";

import { api, ApiError, type SignatoryCapacity } from "@/api";
import { BackLink, TwoThirds, usePageTitle, WarningText } from "@/components/content";
import {
  Button,
  Checkbox,
  type ErrorItem,
  ErrorSummary,
  Radios,
  TextInput,
} from "@/components/forms";
import { useDraft } from "@/filing/draft";
import { type FieldErrors, toReturn } from "@/filing/model";
import { CHECK_ANSWERS, CONFIRMATION, TASK_LIST } from "@/filing/paths";

const CAPACITIES: { value: SignatoryCapacity; label: string }[] = [
  { value: "director", label: "Director" },
  { value: "company_secretary", label: "Company secretary" },
  { value: "authorised_agent", label: "Agent authorised by the company" },
];

const FIELD_ORDER = ["name", "capacity", "confirmed"] as const;

function validate(name: string, capacity: string, confirmed: boolean): FieldErrors {
  const errors: FieldErrors = {};
  if (!name.trim()) errors.name = "Enter your full name";
  if (!capacity) errors.capacity = "Select the capacity in which you are signing";
  if (!confirmed)
    errors.confirmed = "Confirm that the information you have given is correct and complete";
  return errors;
}

function submissionErrors(error: unknown): { fields: FieldErrors; general: ErrorItem[] } {
  if (error instanceof ApiError && error.problems.length > 0) {
    const fields: FieldErrors = {};
    const general: ErrorItem[] = [];
    for (const problem of error.problems) {
      const [section, field] = problem.path;
      if (section === "declaration" && field) fields[field] = problem.message;
      else general.push({ href: CHECK_ANSWERS, text: problem.message });
    }
    return { fields, general };
  }
  const message = error instanceof Error ? error.message : String(error);
  return {
    fields: {},
    general: [{ href: "#main-content", text: `Your return was not submitted: ${message}` }],
  };
}

export function DeclarationPage() {
  const { draft, recordSubmission } = useDraft();
  const ct600 = useMemo(() => toReturn(draft), [draft]);
  const [name, setName] = useState("");
  const [capacity, setCapacity] = useState<SignatoryCapacity | "">("");
  const [confirmed, setConfirmed] = useState(false);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [general, setGeneral] = useState<ErrorItem[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [attempt, setAttempt] = useState(0);

  const summary = [
    ...FIELD_ORDER.filter((field) => errors[field]).map((field) => ({
      href: `#${field}`,
      text: errors[field] ?? "",
    })),
    ...general,
  ];
  usePageTitle("Declaration", summary.length > 0);

  // Submitting clears the draft, so a submitted return has no draft left to show.
  if (ct600 === null) return <Navigate to={submitted ? CONFIRMATION : TASK_LIST} replace />;
  const ready = ct600;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const found = validate(name, capacity, confirmed);
    setErrors(found);
    setGeneral([]);
    setAttempt(attempt + 1);
    if (Object.keys(found).length > 0 || capacity === "") return;
    setSubmitting(true);
    try {
      const receipt = await api.submitReturn(ready, {
        name: name.trim(),
        capacity,
        confirmed: true,
      });
      setSubmitted(true);
      recordSubmission(receipt);
    } catch (error) {
      const problems = submissionErrors(error);
      setErrors(problems.fields);
      setGeneral(problems.general);
      setSubmitting(false);
    }
  }

  return (
    <>
      <BackLink to={CHECK_ANSWERS} />
      <TwoThirds>
        <ErrorSummary key={attempt} errors={summary} />
        <span className="govuk-caption-l">{ct600.company.name}</span>
        <h1 className="govuk-heading-l">Declaration</h1>
        <p className="govuk-body">
          The return must be signed by a director, the company secretary or an agent the company has
          authorised.
        </p>
        <form onSubmit={submit} noValidate>
          <TextInput
            id="name"
            label="Full name"
            value={name}
            onChange={setName}
            error={errors.name}
            autoComplete="name"
          />
          <Radios
            name="capacity"
            legend="In what capacity are you signing?"
            options={CAPACITIES}
            value={capacity}
            onChange={setCapacity}
            error={errors.capacity}
          />
          <Checkbox
            id="confirmed"
            label="The information I have given in this Company Tax Return is correct and complete to the best of my knowledge and belief."
            checked={confirmed}
            onChange={setConfirmed}
            error={errors.confirmed}
          />
          <WarningText>
            This is a demonstration. Your return will not be sent to HMRC. Giving false information
            in a real return can lead to a penalty or prosecution.
          </WarningText>
          <Button disabled={submitting} aria-disabled={submitting}>
            Submit return
          </Button>
        </form>
      </TwoThirds>
    </>
  );
}
