import { useState } from "react";
import { Navigate, useNavigate } from "react-router";

import type { SchemaPage } from "@/api";
import { type DateParts, DateInput } from "@/components/forms";
import { useDraft } from "@/filing/draft";
import { type FieldErrors, savedPeriod } from "@/filing/model";
import { TASK_LIST, useNextPage } from "@/filing/paths";
import { pageTree, RELIEF_TASKS, reliefTasks } from "@/filing/payload";
import {
  LOAN_TABLES,
  loanDateId,
  type LoanDatesAnswers,
  loanRows,
  type LoanTable,
  validateLoanDates,
} from "@/filing/reliefs";
import { SectionFrame } from "@/filing/SectionFrame";
import { SchemaGate } from "@/filing/supplementary/SchemaGate";
import { formatDate } from "@/format";

const TITLE = RELIEF_TASKS.participator_loan_dates.title;
const EMPTY_DATE: DateParts = { day: "", month: "", year: "" };

function LoanDates({ pages }: { pages: SchemaPage[] }) {
  const { draft, saveSection } = useDraft();
  const { next } = useNextPage();
  const navigate = useNavigate();
  const period = savedPeriod(draft);
  const ct600a = pageTree(draft, pages, "A");
  const [values, setValues] = useState<LoanDatesAnswers>(
    () =>
      draft.participator_loan_dates ?? {
        loans: [],
        repaid_within_nine_months: [],
        repaid_later: [],
      },
  );
  const [errors, setErrors] = useState<FieldErrors>({});
  if (!ct600a || !period || !reliefTasks(draft, pages).includes("participator_loan_dates")) {
    return <Navigate to={TASK_LIST} replace />;
  }
  const rows = loanRows(ct600a);
  const order = LOAN_TABLES.flatMap(({ table }) =>
    rows[table].map((_, index) => loanDateId(table, index)),
  );

  function setDate(table: LoanTable, index: number, parts: DateParts) {
    const dates = [...values[table]];
    while (dates.length <= index) dates.push(EMPTY_DATE);
    dates[index] = parts;
    setValues({ ...values, [table]: dates });
  }

  function save() {
    if (!period) return;
    const result = validateLoanDates(values, rows, period);
    if (!result.ok) {
      setErrors(result.errors);
      return;
    }
    saveSection("participator_loan_dates", values);
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
      {LOAN_TABLES.filter(({ table }) => rows[table].length > 0).map(({ table, title }) => (
        <div key={table}>
          <h2 className="govuk-heading-m">{title}</h2>
          {rows[table].map((name, index) => (
            <DateInput
              key={loanDateId(table, index)}
              id={loanDateId(table, index)}
              legend={`When was the loan to ${name} made?`}
              hint="For example, 15 5 2026"
              value={values[table][index] ?? EMPTY_DATE}
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
