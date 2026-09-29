import { type ReactNode, useState } from "react";
import { useNavigate } from "react-router";

import { PrefilledBanner } from "@/components/content";
import { DateInput, MoneyInput, TextInput } from "@/components/forms";
import { draftRecord } from "@/filing/companiesHouse";
import {
  type ComparativesAnswers,
  type ComparativeSection,
  comparativesAsked,
  comparativesProblems,
  filedComparatives,
  filingDescription,
  firstPeriod,
  PREVIOUS_END,
  PREVIOUS_START,
  previousFigureId,
  validatePreviousPeriod,
} from "@/filing/comparatives";
import { useDraft } from "@/filing/draft";
import {
  type AmountField,
  type AmountSection,
  type AmountSectionKey,
  type FieldErrors,
  validateAmounts,
} from "@/filing/model";
import { useNextPage } from "@/filing/paths";
import { SectionFrame } from "@/filing/SectionFrame";
import { formatDate } from "@/format";

const EMPTY_DATE = { day: "", month: "", year: "" };

function isComparative(key: AmountSectionKey): key is ComparativeSection {
  return key === "profit_and_loss" || key === "balance_sheet";
}

type ColumnsProps = {
  field: AmountField<AmountSectionKey>;
  current: string;
  previous: string;
  onCurrent: (value: string) => void;
  onPrevious: (value: string) => void;
  errors: FieldErrors;
};

/** One line of the accounts with this period's figure beside the previous period's. */
function Columns({ field, current, previous, onCurrent, onPrevious, errors }: ColumnsProps) {
  const hintId = `${field.key}-line-hint`;
  return (
    <div className="govuk-form-group">
      <fieldset className="govuk-fieldset" aria-describedby={field.hint ? hintId : undefined}>
        <legend className="govuk-fieldset__legend govuk-fieldset__legend--s">{field.label}</legend>
        {field.hint ? (
          <div className="govuk-hint" id={hintId}>
            {field.hint}
          </div>
        ) : null}
        <div className="app-comparative-columns">
          <MoneyInput
            id={field.key}
            label="This period"
            value={current}
            onChange={onCurrent}
            error={errors[field.key]}
          />
          <MoneyInput
            id={previousFigureId(field.key)}
            label="Previous period"
            value={previous}
            onChange={onPrevious}
            error={errors[previousFigureId(field.key)]}
          />
        </div>
      </fieldset>
    </div>
  );
}

type PreviousPeriodProps = {
  period: ComparativesAnswers["period"];
  onChange: (period: NonNullable<ComparativesAnswers["period"]>) => void;
  errors: FieldErrors;
};

/** The previous period of account's dates, asked with the profit and loss account. */
function PreviousPeriod({ period, onChange, errors }: PreviousPeriodProps) {
  const dates = period ?? { start: EMPTY_DATE, end: EMPTY_DATE };
  return (
    <>
      <DateInput
        id={PREVIOUS_START}
        legend="When did the previous period of account start?"
        hint="For example, 1 4 2024"
        value={dates.start}
        onChange={(start) => onChange({ ...dates, start })}
        error={errors[PREVIOUS_START]}
      />
      <DateInput
        id={PREVIOUS_END}
        legend="When did it end?"
        hint="For example, 31 3 2025"
        value={dates.end}
        onChange={(end) => onChange({ ...dates, end })}
        error={errors[PREVIOUS_END]}
      />
    </>
  );
}

type NoticeProps = { prefilled: string | null; unavailable: string | null; firstUnknown: boolean };

/** Where the previous period's figures came from, why they could not be read, or when to skip them. */
function PreviousNotice({ prefilled, unavailable, firstUnknown }: NoticeProps) {
  if (prefilled) return <div className="govuk-inset-text">{prefilled}</div>;
  if (unavailable) {
    return (
      <div className="govuk-inset-text">
        {unavailable} Enter last period’s figures from the company’s accounts.
      </div>
    );
  }
  if (firstUnknown) {
    return (
      <div className="govuk-inset-text">
        After its first period of account, the company’s accounts show last period’s figures beside
        this period’s. If this is its first period, leave the previous period blank.
      </div>
    );
  }
  return null;
}

/**
 * A section of the return made up of amounts: profit and loss, adjustments, balance sheet. After
 * the company's first period of account, the profit and loss account and balance sheet also ask
 * for the previous period's figures (comparatives), prefilled from the accounts last filed at
 * Companies House where they could be read.
 */
export function AmountSectionPage<K extends AmountSectionKey>({
  section,
}: {
  section: AmountSection<K>;
}) {
  const { draft, saveSection } = useDraft();
  const { next } = useNextPage();
  const navigate = useNavigate();
  const key = section.key;
  const comparative = isComparative(key);
  const askingPrevious = comparative && comparativesAsked(draft);
  const record = draftRecord(draft);
  const [prefill] = useState(() =>
    comparative && !draft[key] && !draft.comparatives?.[key]
      ? filedComparatives(record, key, section.fields)
      : null,
  );
  const [values, setValues] = useState<Record<string, string>>(draft[key] ?? {});
  // The saved comparatives, with the filed accounts' figures for this section (and their dates,
  // if none are saved) until the section is saved.
  const [previous, setPrevious] = useState<ComparativesAnswers>(() => {
    const saved = draft.comparatives ?? {};
    if (!prefill || !comparative) return saved;
    const period = saved.period ?? prefill.period;
    return { ...saved, ...(period ? { period } : {}), [key]: prefill[key] ?? {} };
  });
  const [errors, setErrors] = useState<FieldErrors>({});
  // Some amounts are only asked once an earlier answer makes them relevant.
  const asked = section.fields.filter((field) => field.askedWhen?.(values, draft) ?? true);

  function save() {
    const result = validateAmounts(section, values, draft);
    const previousProblems = askingPrevious
      ? comparativesProblems(
          { ...draft, comparatives: previous },
          key as ComparativeSection,
          section.fields,
        )
      : {};
    const found = { ...(result.ok ? {} : result.errors), ...previousProblems };
    if (Object.keys(found).length > 0) {
      setErrors(found);
      return;
    }
    saveSection(key, values);
    if (askingPrevious) saveSection("comparatives", previous);
    navigate(next);
  }

  const previousValues = comparative ? (previous[key as ComparativeSection] ?? {}) : {};
  const setPreviousFigure = (field: string, value: string) =>
    setPrevious((current) => ({
      ...current,
      [key]: { ...current[key as ComparativeSection], [field]: value },
    }));
  const periodEnd = validatePreviousPeriod(previous.period);

  let heading: ReactNode = null;
  if (askingPrevious && key === "profit_and_loss") {
    heading = (
      <PreviousPeriod
        period={previous.period}
        onChange={(period) => setPrevious({ ...previous, period })}
        errors={errors}
      />
    );
  } else if (askingPrevious && periodEnd.ok) {
    heading = (
      <p className="govuk-body">
        The previous period’s balance sheet is at {formatDate(periodEnd.value.end)}.
      </p>
    );
  }

  return (
    <SectionFrame
      title={section.title}
      errors={errors}
      fieldOrder={[
        PREVIOUS_START,
        PREVIOUS_END,
        ...asked.flatMap((field) => [field.key, previousFigureId(field.key)]),
      ]}
      inputId={(field) =>
        field === PREVIOUS_START || field === PREVIOUS_END ? `${field}-day` : field
      }
      onSubmit={save}
      intro={section.intro}
      banner={askingPrevious && prefill ? <PrefilledBanner /> : null}
    >
      {askingPrevious ? (
        <PreviousNotice
          prefilled={prefill ? filingDescription(record) : null}
          unavailable={record?.previous_accounts_unavailable ?? null}
          firstUnknown={firstPeriod(draft) === ""}
        />
      ) : null}
      {heading}
      {asked.map((field) => {
        const props = {
          id: field.key,
          label: field.label,
          hint: field.hint,
          value: values[field.key] ?? "",
          onChange: (value: string) => setValues({ ...values, [field.key]: value }),
          error: errors[field.key],
        };
        if (askingPrevious) {
          return (
            <Columns
              key={field.key}
              field={field as AmountField<AmountSectionKey>}
              current={props.value}
              previous={previousValues[field.key] ?? ""}
              onCurrent={props.onChange}
              onPrevious={(value) => setPreviousFigure(field.key, value)}
              errors={errors}
            />
          );
        }
        return field.kind === "count" ? (
          <TextInput key={field.key} {...props} width="3" inputMode="numeric" />
        ) : (
          <MoneyInput key={field.key} {...props} />
        );
      })}
    </SectionFrame>
  );
}
