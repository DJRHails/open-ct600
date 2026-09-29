import { useState } from "react";
import { useNavigate } from "react-router";

import type { CompanyRecord } from "@/api";
import { PrefilledBanner } from "@/components/content";
import { Button, Checkboxes, DateInput, Radios, TextInput } from "@/components/forms";
import { QuestionHelp } from "@/components/help";
import { ACCOUNTS_HELP, COMPARATIVES_HELP } from "@/content/help/accounts";
import {
  currentDirectors,
  draftRecord,
  firstPeriodFromRecord,
  LEGAL_FORMS,
  supportedLegalForm,
} from "@/filing/companiesHouse";
import { PREVIOUS_EMPLOYEES, validatePreviousEmployees } from "@/filing/comparatives";
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
  YES_NO,
} from "@/filing/model";
import { useNextPage } from "@/filing/paths";
import { SectionFrame } from "@/filing/SectionFrame";

const MAX_DIRECTORS = 50;

function helpFor(key: keyof AccountsAnswers) {
  return <QuestionHelp id={`${key}-help`} help={ACCOUNTS_HELP[key]} />;
}

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
      {helpFor("directors")}
    </div>
  );
}

type OfficersProps = DirectorsProps & { officers: string[] };

/**
 * The company's current directors from Companies House as tick boxes, and anyone else who was a
 * director during the period typed in with "Add another person".
 */
function Officers({ officers, directors, errors, onChange }: OfficersProps) {
  const ticked = officers.filter((officer) => directors.includes(officer));
  const others = directors.filter((director) => !officers.includes(director));
  const setOthers = (names: string[]) => onChange([...ticked, ...names]);
  const otherIndex = (index: number) => ticked.length + index;
  return (
    <div className="govuk-form-group">
      <Checkboxes
        name="directors"
        legend="Who were the company’s directors during the period?"
        legendSize="s"
        hint="Companies House lists these as its current directors. Add anyone else who was a director during the period."
        options={officers.map((officer) => ({ value: officer, label: officer }))}
        value={ticked}
        onChange={(chosen) =>
          onChange([...officers.filter((officer) => chosen.includes(officer)), ...others])
        }
        error={errors.directors}
      />
      {others.map((name, index) => (
        <div key={index}>
          <TextInput
            id={directorId(otherIndex(index))}
            label={`Other person ${index + 1} full name`}
            value={name}
            onChange={(typed) => setOthers(others.map((other, i) => (i === index ? typed : other)))}
            error={errors[directorId(otherIndex(index))]}
            autoComplete="off"
          />
          <Button
            type="button"
            variant="secondary"
            onClick={() => setOthers(others.filter((_, i) => i !== index))}
          >
            {"Remove "}
            <span className="govuk-visually-hidden">other person {index + 1}</span>
          </Button>
        </div>
      ))}
      {directors.length < MAX_DIRECTORS ? (
        <Button type="button" variant="secondary" onClick={() => setOthers([...others, ""])}>
          Add another person
        </Button>
      ) : null}
      {helpFor("directors")}
    </div>
  );
}

/** Accounts details as Companies House shows them, until the user saves their own. */
function prefilledAccounts(record: CompanyRecord | null): AccountsAnswers | null {
  if (!record) return null;
  const officers = currentDirectors(record);
  return {
    ...EMPTY_ACCOUNTS,
    directors: officers.length > 0 ? officers : EMPTY_ACCOUNTS.directors,
    legal_form: supportedLegalForm(record),
    first_period: firstPeriodFromRecord(record),
  };
}

export function AccountsDetailsPage() {
  const { draft, saveSection } = useDraft();
  const { next } = useNextPage();
  const navigate = useNavigate();
  const record = draftRecord(draft);
  const officers = currentDirectors(record);
  const [prefill] = useState(() => (draft.accounts ? null : prefilledAccounts(record)));
  const [values, setValues] = useState<AccountsAnswers>({
    ...EMPTY_ACCOUNTS,
    ...(draft.accounts ?? prefill),
  });
  const [errors, setErrors] = useState<FieldErrors>({});
  const [previousEmployees, setPreviousEmployees] = useState(() => {
    const filed = record?.previous_accounts?.average_employees;
    return draft.comparatives?.average_employees ?? (filed == null ? "" : String(filed));
  });
  const named = [...new Set(values.directors.map((d) => d.trim()).filter(Boolean))];

  function save() {
    const result = validateAccounts(values, periodEnd(draft));
    const previous = validatePreviousEmployees(previousEmployees);
    const previousError = values.first_period === "no" && !previous.ok ? previous.error : null;
    if (!result.ok || previousError) {
      setErrors({
        ...(result.ok ? {} : result.errors),
        ...(previousError ? { [PREVIOUS_EMPLOYEES]: previousError } : {}),
      });
      return;
    }
    saveSection("accounts", values);
    if (values.first_period === "no") {
      saveSection("comparatives", { ...draft.comparatives, average_employees: previousEmployees });
    }
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
        "legal_form",
        "first_period",
        "directors",
        ...values.directors.map((_, index) => directorId(index)),
        "signing_director",
        "approval_date",
        "average_employees",
        PREVIOUS_EMPLOYEES,
        "dormant",
        "trading_status",
      ]}
      inputId={(field) => (field === "approval_date" ? "approval_date-day" : field)}
      onSubmit={save}
      intro="These details appear in the statutory accounts filed with your return."
      banner={prefill ? <PrefilledBanner /> : null}
    >
      <Radios
        name="standard"
        legend="How were the accounts prepared?"
        options={STANDARD_OPTIONS}
        value={values.standard}
        onChange={(standard) => setValues({ ...values, standard })}
        error={errors.standard}
        help={helpFor("standard")}
      />
      <Radios
        name="legal_form"
        legend="What is the company’s legal form?"
        hint="It’s on the company’s certificate of incorporation."
        options={LEGAL_FORMS}
        value={values.legal_form}
        onChange={(legalForm) => setValues({ ...values, legal_form: legalForm })}
        error={errors.legal_form}
        help={helpFor("legal_form")}
      />
      <Radios
        name="first_period"
        legend="Is this the company’s first period of account?"
        hint="Its first accounts since it was set up. After that, the accounts show last period’s figures beside this period’s, which you enter with the profit and loss account and balance sheet."
        options={YES_NO}
        value={values.first_period}
        onChange={(firstPeriod) => setValues({ ...values, first_period: firstPeriod })}
        error={errors.first_period}
        help={helpFor("first_period")}
        inline
      />
      {officers.length > 0 ? (
        <Officers
          officers={officers}
          directors={values.directors}
          errors={errors}
          onChange={setDirectors}
        />
      ) : (
        <Directors directors={values.directors} errors={errors} onChange={setDirectors} />
      )}
      <Radios
        name="signing_director"
        legend="Which director signed the accounts?"
        hint={named.length === 0 ? "Enter the directors' names first." : undefined}
        options={named.map((name) => ({ value: name, label: name }))}
        value={values.signing_director}
        onChange={(director) => setValues({ ...values, signing_director: director })}
        error={errors.signing_director}
        help={helpFor("signing_director")}
      />
      <DateInput
        id="approval_date"
        legend="When did the board approve the accounts?"
        hint="For example, 30 6 2026. This is after the accounting period ends."
        value={values.approval_date}
        onChange={(approvalDate) => setValues({ ...values, approval_date: approvalDate })}
        error={errors.approval_date}
        help={helpFor("approval_date")}
      />
      <TextInput
        id="average_employees"
        label="Average number of employees during the period"
        hint="Include directors. Enter 0 if the company had no employees."
        value={values.average_employees}
        onChange={(employees) => setValues({ ...values, average_employees: employees })}
        error={errors.average_employees}
        help={helpFor("average_employees")}
        width="5"
        inputMode="numeric"
      />
      {values.first_period === "no" ? (
        <TextInput
          id={PREVIOUS_EMPLOYEES}
          label="Average number of employees during the previous period (optional)"
          hint="The accounts show it beside this period’s."
          value={previousEmployees}
          onChange={setPreviousEmployees}
          error={errors[PREVIOUS_EMPLOYEES]}
          help={
            <QuestionHelp
              id="previous-employees-help"
              help={COMPARATIVES_HELP.previous_employees}
            />
          }
          width="5"
          inputMode="numeric"
        />
      ) : null}
      <Radios
        name="dormant"
        legend="Was the company dormant during this period?"
        hint="A dormant company had no significant accounting transactions: no turnover, expenses, income or gains. It files dormant accounts and has no Corporation Tax to pay."
        options={YES_NO}
        value={values.dormant}
        onChange={(dormant) => setValues({ ...values, dormant })}
        error={errors.dormant}
        help={helpFor("dormant")}
        inline
      />
      <Radios
        name="trading_status"
        legend="Did the company trade?"
        options={TRADING_STATUS_OPTIONS}
        value={values.trading_status}
        onChange={(status) => setValues({ ...values, trading_status: status })}
        error={errors.trading_status}
        help={helpFor("trading_status")}
      />
    </SectionFrame>
  );
}
