import { useState } from "react";
import { useNavigate } from "react-router";

import { Button, DateInput, Radios, TextInput } from "@/components/forms";
import { useDraft } from "@/filing/draft";
import {
  type AccountsAnswers,
  directorId,
  EMPTY_ACCOUNTS,
  type FieldErrors,
  periodEnd,
  SECTION_TITLES,
  STANDARD_OPTIONS,
  TRADING_STATUS_OPTIONS,
  validateAccounts,
} from "@/filing/model";
import { useNextPage } from "@/filing/paths";
import { SectionFrame } from "@/filing/SectionFrame";

const MAX_DIRECTORS = 50;

type DirectorsProps = {
  directors: string[];
  errors: FieldErrors;
  onChange: (directors: string[]) => void;
};

/** The GOV.UK "add another" pattern: one name per director, with remove and add buttons. */
function Directors({ directors, errors, onChange }: DirectorsProps) {
  return (
    <div className="govuk-form-group">
      <fieldset className="govuk-fieldset">
        <legend className="govuk-fieldset__legend govuk-fieldset__legend--s">Directors</legend>
        <div className="govuk-hint">Everyone who was a director during the accounting period.</div>
        {directors.map((director, index) => (
          <div key={index}>
            <TextInput
              id={directorId(index)}
              label={`Director ${index + 1} full name`}
              value={director}
              onChange={(name) => onChange(directors.map((d, i) => (i === index ? name : d)))}
              error={errors[directorId(index)]}
              autoComplete="off"
            />
            {directors.length > 1 ? (
              <Button
                type="button"
                variant="secondary"
                onClick={() => onChange(directors.filter((_, i) => i !== index))}
              >
                {"Remove "}
                <span className="govuk-visually-hidden">director {index + 1}</span>
              </Button>
            ) : null}
          </div>
        ))}
      </fieldset>
      {directors.length < MAX_DIRECTORS ? (
        <Button type="button" variant="secondary" onClick={() => onChange([...directors, ""])}>
          Add another director
        </Button>
      ) : null}
    </div>
  );
}

export function AccountsDetailsPage() {
  const { draft, saveSection } = useDraft();
  const { next } = useNextPage();
  const navigate = useNavigate();
  const [values, setValues] = useState<AccountsAnswers>({ ...EMPTY_ACCOUNTS, ...draft.accounts });
  const [errors, setErrors] = useState<FieldErrors>({});
  const named = [...new Set(values.directors.map((d) => d.trim()).filter(Boolean))];

  function save() {
    const result = validateAccounts(values, periodEnd(draft));
    if (!result.ok) {
      setErrors(result.errors);
      return;
    }
    saveSection("accounts", values);
    navigate(next);
  }

  function setDirectors(directors: string[]) {
    const stillListed = directors.map((d) => d.trim()).includes(values.signing_director);
    setValues({
      ...values,
      directors,
      signing_director: stillListed ? values.signing_director : "",
    });
  }

  return (
    <SectionFrame
      title={SECTION_TITLES.accounts}
      errors={errors}
      fieldOrder={[
        "standard",
        ...values.directors.map((_, index) => directorId(index)),
        "signing_director",
        "approval_date",
        "average_employees",
        "trading_status",
      ]}
      inputId={(field) => (field === "approval_date" ? "approval_date-day" : field)}
      onSubmit={save}
      intro="These details appear in the statutory accounts filed with your return."
    >
      <Radios
        name="standard"
        legend="How were the accounts prepared?"
        options={STANDARD_OPTIONS}
        value={values.standard}
        onChange={(standard) => setValues({ ...values, standard })}
        error={errors.standard}
      />
      <Directors directors={values.directors} errors={errors} onChange={setDirectors} />
      <Radios
        name="signing_director"
        legend="Which director signed the accounts?"
        hint={named.length === 0 ? "Enter the directors' names first." : undefined}
        options={named.map((name) => ({ value: name, label: name }))}
        value={values.signing_director}
        onChange={(director) => setValues({ ...values, signing_director: director })}
        error={errors.signing_director}
      />
      <DateInput
        id="approval_date"
        legend="When did the board approve the accounts?"
        hint="For example, 30 6 2026. This is after the accounting period ends."
        value={values.approval_date}
        onChange={(approvalDate) => setValues({ ...values, approval_date: approvalDate })}
        error={errors.approval_date}
      />
      <TextInput
        id="average_employees"
        label="Average number of employees during the period"
        hint="Include directors. Enter 0 if the company had no employees."
        value={values.average_employees}
        onChange={(employees) => setValues({ ...values, average_employees: employees })}
        error={errors.average_employees}
        width="5"
        inputMode="numeric"
      />
      <Radios
        name="trading_status"
        legend="Did the company trade?"
        options={TRADING_STATUS_OPTIONS}
        value={values.trading_status}
        onChange={(status) => setValues({ ...values, trading_status: status })}
        error={errors.trading_status}
      />
    </SectionFrame>
  );
}
