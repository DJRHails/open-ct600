import { useState } from "react";
import { Navigate, useNavigate } from "react-router";

import type { SchemaPage } from "@/api";
import { type DateParts, DateInput } from "@/components/forms";
import { useDraft } from "@/filing/draft";
import { type FieldErrors, savedPeriod } from "@/filing/model";
import { TASK_LIST, useNextPage } from "@/filing/paths";
import { RELIEF_TASKS, reliefTasks } from "@/filing/payload";
import {
  draftLoans,
  LOAN_TABLES,
  loanDateId,
  type LoanTable,
  validateLoanDates,
  withLoanDate,
} from "@/filing/reliefs";
import { SectionFrame } from "@/filing/SectionFrame";
import type { RawTree } from "@/filing/supplementary/answers";
import { SchemaGate } from "@/filing/supplementary/SchemaGate";
import { formatDate } from "@/format";

const TITLE = RELIEF_TASKS.participator_loan_dates.title;

/** The date each loan was made is saved in its own CT600A row, so it moves with the row. */
function LoanDates({ pages }: { pages: SchemaPage[] }) {
  const { draft, savePageAnswers } = useDraft();
  const { next } = useNextPage();
  const navigate = useNavigate();
  const period = savedPeriod(draft);
  const [answers, setAnswers] = useState<RawTree>(() => draft.supplementary_pages?.A ?? {});
  const [errors, setErrors] = useState<FieldErrors>({});
  if (!period || !reliefTasks(draft, pages).includes("participator_loan_dates")) {
    return <Navigate to={TASK_LIST} replace />;
  }
  const loans = draftLoans(answers);
  const order = LOAN_TABLES.flatMap(({ table }) =>
    loans[table].map(({ index }) => loanDateId(table, index)),
  );

  function setDate(table: LoanTable, index: number, parts: DateParts) {
    setAnswers((current) => withLoanDate(current, table, index, parts));
  }

  function save() {
    if (!period) return;
    const result = validateLoanDates(answers, period);
    if (!result.ok) {
      setErrors(result.errors);
      return;
    }
    savePageAnswers("A", answers);
    navigate(next);
  }

  return (
    <SectionFrame
      title={TITLE}
      errors={errors}
      fieldOrder={order}
      inputId={(field) => `${field}-day`}
      onSubmit={save}
      intro={`The tax rate on loans to participators changed during this accounting period, so the rate for each loan depends on when it was made. Each date must be between ${formatDate(period.start)} and ${formatDate(period.end)}.`}
    >
      {LOAN_TABLES.filter(({ table }) => loans[table].length > 0).map(({ table, title }) => (
        <div key={table}>
          <h2 className="govuk-heading-m">{title}</h2>
          {loans[table].map(({ index, name, made }) => (
            <DateInput
              key={loanDateId(table, index)}
              id={loanDateId(table, index)}
              legend={`When was the loan to ${name} made?`}
              hint="For example, 15 5 2026"
              value={made}
              onChange={(parts) => setDate(table, index, parts)}
              error={errors[loanDateId(table, index)]}
            />
          ))}
        </div>
      ))}
    </SectionFrame>
  );
}

/** When each loan on CT600A was made: needed when the s455 rate changes during the period. */
export function LoanDatesPage() {
  return <SchemaGate title={TITLE}>{(pages) => <LoanDates pages={pages} />}</SchemaGate>;
}
