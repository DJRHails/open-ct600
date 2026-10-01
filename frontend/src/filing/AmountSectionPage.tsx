import { type ReactNode, useState } from "react";
import { useNavigate } from "react-router";

import { PrefilledBanner } from "@/components/content";
import { DateInput, MoneyInput, Radios, TextInput } from "@/components/forms";
import { QuestionHelp } from "@/components/help";
import { COMPARATIVES_HELP } from "@/content/help/accounts";
import type { QuestionHelp as QuestionHelpContent } from "@/content/help/types";
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
  previousTaxUnknown,
  TAX_ON_PROFIT,
  validatePreviousPeriod,
} from "@/filing/comparatives";
import { useDraft } from "@/filing/draft";
import { answeredAmounts, gateErrors, gateId, type Gates, initialGates } from "@/filing/gates";
import {
  type AmountField,
  type AmountSection,
  type AmountSectionKey,
  type Draft,
  type FieldErrors,
  savedPeriod,
  validateAmounts,
  YES_NO,
  type YesNo,
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
  help: ReactNode;
};

/** One line of the accounts with this period's figure beside the previous period's. */
function Columns(props: ColumnsProps) {
  const { field, current, previous, onCurrent, onPrevious, errors, help } = props;
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
      {help}
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
        help={<QuestionHelp id="previous-period-help" help={COMPARATIVES_HELP.previous_period} />}
      />
    </>
  );
}

/**
 * The previous period's dates, asked with the profit and loss account; the balance sheet says
 * which date its previous column is at.
 */
function PreviousHeading(props: PreviousPeriodProps & { sectionKey: AmountSectionKey }) {
  const { sectionKey, ...dates } = props;
  if (sectionKey === "profit_and_loss") return <PreviousPeriod {...dates} />;
  const periodEnd = validatePreviousPeriod(dates.period);
  if (!periodEnd.ok) return null;
  return (
    <p className="govuk-body">
      The previous period’s balance sheet is at {formatDate(periodEnd.value.end)}.
    </p>
  );
}

type PreviousTaxProps = {
  value: string;
  onChange: (value: string) => void;
  error: string | undefined;
  /** The filed accounts were read but gave no tax charge, so it must be entered. */
  unknown: boolean;
};

/** Last period's tax charge, asked with the profit and loss account; this period's is worked out. */
function PreviousTax({ value, onChange, error, unknown }: PreviousTaxProps) {
  // A text keyboard, not a numeric one: some numeric keyboards have no minus sign.
  return (
    <>
      {unknown ? (
        <div className="govuk-inset-text">
          We could not read last period’s tax charge from the accounts filed at Companies House.
          Enter it from the company’s accounts, or 0 if there was none.
        </div>
      ) : null}
      <TextInput
        id={previousFigureId(TAX_ON_PROFIT)}
        label="Tax on profit in the previous period"
        hint="The tax charge in last period’s profit and loss account. If it was a tax credit, put a minus sign in front, like -1200. We work out this period’s."
        value={value}
        onChange={onChange}
        error={error}
        prefix="£"
        width="10"
        spellCheck={false}
        help={<QuestionHelp id="tax-on-profit-help" help={COMPARATIVES_HELP.tax_on_profit} />}
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

type AmountProps = {
  field: AmountField<AmountSectionKey>;
  value: string;
  onChange: (value: string) => void;
  /** The previous period's figure, when it is asked beside this period's. */
  previous: { value: string; onChange: (value: string) => void } | null;
  errors: FieldErrors;
  help: ReactNode;
};

/** One amount: a single figure, or this period's beside the previous period's. */
function Amount({ field, value, onChange, previous, errors, help }: AmountProps) {
  if (previous) {
    return (
      <Columns
        field={field}
        current={value}
        previous={previous.value}
        onCurrent={onChange}
        onPrevious={previous.onChange}
        errors={errors}
        help={help}
      />
    );
  }
  const props = {
    id: field.key,
    label: field.label,
    hint: field.hint,
    value,
    onChange,
    error: errors[field.key],
    help,
  };
  return field.kind === "count" ? (
    <TextInput {...props} width="3" inputMode="numeric" />
  ) : (
    <MoneyInput {...props} />
  );
}

type QuestionProps = Omit<AmountProps, "help"> & {
  gate: YesNo;
  onGate: (answer: YesNo) => void;
  help: QuestionHelpContent | undefined;
};

/** An amount with its help, after its yes or no question if it has one. */
function AmountQuestion({ gate, onGate, help, ...amount }: QuestionProps) {
  const { field, errors } = amount;
  const helpNode = help ? <QuestionHelp id={`${field.key}-help`} help={help} /> : undefined;
  if (!field.gate) return <Amount {...amount} help={helpNode} />;
  return (
    <Radios
      name={gateId(field.key)}
      legend={field.gate.question}
      hint={field.gate.hint}
      options={YES_NO.map((option) =>
        option.value === "yes"
          ? { ...option, conditional: <Amount {...amount} help={undefined} /> }
          : option,
      )}
      value={gate}
      onChange={onGate}
      error={errors[gateId(field.key)]}
      help={helpNode}
    />
  );
}

/** Every answer on the page, in order, so the error summary lists problems top to bottom. */
function fieldOrder<K extends AmountSectionKey>(asked: AmountField<K>[]): string[] {
  return [
    PREVIOUS_START,
    PREVIOUS_END,
    ...asked.flatMap((field) => [
      ...(field.gate ? [gateId(field.key)] : []),
      field.key,
      previousFigureId(field.key),
    ]),
    previousFigureId(TAX_ON_PROFIT),
  ];
}

/**
 * The previous period's answers: the saved comparatives, with the filed accounts' figures for
 * this section (and their dates, if none are saved) until the section is saved.
 */
function usePrevious<K extends AmountSectionKey>(section: AmountSection<K>, draft: Draft) {
  const key = section.key;
  const comparative = isComparative(key);
  const [prefill] = useState(() =>
    comparative && !draft[key] && !draft.comparatives?.[key]
      ? filedComparatives(draftRecord(draft), key, section.fields)
      : null,
  );
  const [previous, setPrevious] = useState<ComparativesAnswers>(() => {
    const saved = draft.comparatives ?? {};
    if (!prefill || !comparative) return saved;
    const period = saved.period ?? prefill.period;
    const tax = saved.tax_on_profit ?? prefill.tax_on_profit;
    return {
      ...saved,
      ...(period ? { period } : {}),
      ...(tax !== undefined ? { tax_on_profit: tax } : {}),
      [key]: prefill[key] ?? {},
    };
  });
  return { prefill, previous, setPrevious };
}

type SectionAnswers = {
  values: Record<string, string>;
  gates: Gates;
  /** The previous period's answers, when they are asked. */
  previous: ComparativesAnswers | null;
};

/** Everything wrong with a section's answers: amounts, yes or no questions, previous period. */
function sectionProblems<K extends AmountSectionKey>(
  section: AmountSection<K>,
  draft: Draft,
  { values, gates, previous }: SectionAnswers,
): FieldErrors {
  const result = validateAmounts(section, answeredAmounts(section, values, gates), draft);
  const previousProblems = previous
    ? comparativesProblems(
        { ...draft, comparatives: previous },
        section.key as ComparativeSection,
        section.fields,
        savedPeriod(draft)?.start,
      )
    : {};
  return {
    ...(result.ok ? {} : result.errors),
    ...gateErrors(section, values, gates),
    ...previousProblems,
  };
}

type PageProps<K extends AmountSectionKey> = {
  section: AmountSection<K>;
  /** Help under each amount's question, by its key. */
  help: Partial<Record<string, QuestionHelpContent>>;
};

/**
 * A section of the return made up of amounts: profit and loss, adjustments, balance sheet. After
 * the company's first period of account, the profit and loss account and balance sheet also ask
 * for the previous period's figures (comparatives), prefilled from the accounts last filed at
 * Companies House where they could be read. An amount with a yes or no question in front of it
 * (``AmountField.gate``) is revealed on yes and is 0 on no. Each question has help under it.
 */
export function AmountSectionPage<K extends AmountSectionKey>({ section, help }: PageProps<K>) {
  const { draft, saveSection } = useDraft();
  const { next } = useNextPage();
  const navigate = useNavigate();
  const key = section.key;
  const comparative = isComparative(key);
  const askingPrevious = comparative && comparativesAsked(draft);
  const record = draftRecord(draft);
  const { prefill, previous, setPrevious } = usePrevious(section, draft);
  const [values, setValues] = useState<Record<string, string>>(draft[key] ?? {});
  const [gates, setGates] = useState<Gates>(() => initialGates(section, draft[key]));
  const [errors, setErrors] = useState<FieldErrors>({});
  const answered = answeredAmounts(section, values, gates);
  // Some amounts are only asked once an earlier answer makes them relevant.
  const asked = section.fields.filter((field) => field.askedWhen?.(answered, draft) ?? true);

  function save() {
    const found = sectionProblems(section, draft, {
      values,
      gates,
      previous: askingPrevious ? previous : null,
    });
    if (Object.keys(found).length > 0) {
      setErrors(found);
      return;
    }
    saveSection(key, answered);
    if (askingPrevious) saveSection("comparatives", previous);
    navigate(next);
  }

  const previousValues = comparative ? (previous[key as ComparativeSection] ?? {}) : {};
  const setPreviousFigure = (field: string, value: string) =>
    setPrevious((current) => ({
      ...current,
      [key]: { ...current[key as ComparativeSection], [field]: value },
    }));

  return (
    <SectionFrame
      title={section.title}
      errors={errors}
      fieldOrder={fieldOrder(asked)}
      inputId={(field) =>
        field === PREVIOUS_START || field === PREVIOUS_END ? `${field}-day` : field
      }
      onSubmit={save}
      intro={section.intro}
      banner={askingPrevious && prefill ? <PrefilledBanner /> : null}
    >
      {askingPrevious ? (
        <PreviousNotice
          prefilled={prefill ? filingDescription(record, key as ComparativeSection) : null}
          unavailable={record?.previous_accounts_unavailable ?? null}
          firstUnknown={firstPeriod(draft) === ""}
        />
      ) : null}
      {askingPrevious ? (
        <PreviousHeading
          sectionKey={key}
          period={previous.period}
          onChange={(period) => setPrevious({ ...previous, period })}
          errors={errors}
        />
      ) : null}
      {asked.map((field) => (
        <AmountQuestion
          key={field.key}
          field={field as AmountField<AmountSectionKey>}
          value={values[field.key] ?? ""}
          onChange={(value) => setValues({ ...values, [field.key]: value })}
          previous={
            askingPrevious
              ? {
                  value: previousValues[field.key] ?? "",
                  onChange: (value) => setPreviousFigure(field.key, value),
                }
              : null
          }
          gate={gates[field.key] ?? ""}
          onGate={(answer) => setGates({ ...gates, [field.key]: answer })}
          errors={errors}
          help={help[field.key]}
        />
      ))}
      {askingPrevious && key === "profit_and_loss" ? (
        <PreviousTax
          value={previous.tax_on_profit ?? ""}
          onChange={(value) => setPrevious((current) => ({ ...current, tax_on_profit: value }))}
          error={errors[previousFigureId(TAX_ON_PROFIT)]}
          unknown={previousTaxUnknown(draft)}
        />
      ) : null}
    </SectionFrame>
  );
}
