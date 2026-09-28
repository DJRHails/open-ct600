import { type FormEvent, useEffect, useRef, useState } from "react";
import { Link } from "react-router";

import { api, ApiError, type TaxComputation } from "@/api";
import { usePageTitle } from "@/components/content";
import {
  Button,
  DateInput,
  type DateParts,
  ErrorSummary,
  MoneyInput,
  TextInput,
} from "@/components/forms";
import { TaxBreakdownTable, TaxSummary } from "@/components/TaxBreakdown";
import { parseCount, parseDateParts, parseWholePounds } from "@/format";

type Field = "period_start" | "period_end" | "taxable_profits" | "associated_companies";
type Errors = Partial<Record<Field, string>>;

const FIELD_ORDER: Field[] = [
  "period_start",
  "period_end",
  "taxable_profits",
  "associated_companies",
];
const INPUT_IDS: Record<Field, string> = {
  period_start: "period_start-day",
  period_end: "period_end-day",
  taxable_profits: "taxable_profits",
  associated_companies: "associated_companies",
};

type Inputs = { start: DateParts; end: DateParts; profits: string; associated: string };

const DEFAULT_INPUTS: Inputs = {
  start: { day: "1", month: "4", year: "2026" },
  end: { day: "31", month: "3", year: "2027" },
  profits: "",
  associated: "0",
};

function parseInputs(inputs: Inputs) {
  const start = parseDateParts(inputs.start, "period start date");
  const end = parseDateParts(inputs.end, "period end date");
  const profits = parseWholePounds(inputs.profits, "taxable profits", true);
  const associated = parseCount(inputs.associated, "number of associated companies", 999);
  const errors: Errors = {};
  if (!start.ok) errors.period_start = start.error;
  if (!end.ok) errors.period_end = end.error;
  if (!profits.ok) errors.taxable_profits = profits.error;
  if (!associated.ok) errors.associated_companies = associated.error;
  if (!start.ok || !end.ok || !profits.ok || !associated.ok) return { errors };
  return {
    errors,
    request: {
      period_start: start.value,
      period_end: end.value,
      taxable_profits: profits.value,
      associated_companies: associated.value,
    },
  };
}

function serverErrors(error: unknown): Errors {
  if (!(error instanceof ApiError) || error.problems.length === 0) {
    const message = error instanceof Error ? error.message : String(error);
    return { taxable_profits: `We could not work out your tax: ${message}` };
  }
  const errors: Errors = {};
  for (const problem of error.problems) {
    const field = FIELD_ORDER.find((name) => name === problem.path[0]) ?? "period_end";
    errors[field] ??= problem.message;
  }
  return errors;
}

function Result({ tax }: { tax: TaxComputation }) {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => heading.current?.focus(), []);

  return (
    <section aria-labelledby="result-heading">
      <h2 className="govuk-heading-l" id="result-heading" tabIndex={-1} ref={heading}>
        Your Corporation Tax estimate
      </h2>
      <TaxSummary tax={tax} />
      <TaxBreakdownTable tax={tax} />
    </section>
  );
}

function CalculatorForm({ onResult }: { onResult: (tax: TaxComputation | null) => void }) {
  const [inputs, setInputs] = useState<Inputs>(DEFAULT_INPUTS);
  const [errors, setErrors] = useState<Errors>({});
  const [attempt, setAttempt] = useState(0);
  usePageTitle("Corporation Tax calculator", Object.keys(errors).length > 0);

  async function calculate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAttempt(attempt + 1);
    const parsed = parseInputs(inputs);
    setErrors(parsed.errors);
    onResult(null);
    if (!parsed.request) return;
    try {
      onResult(await api.calculate(parsed.request));
    } catch (error) {
      setErrors(serverErrors(error));
    }
  }

  const summary = FIELD_ORDER.filter((field) => errors[field]).map((field) => ({
    href: `#${INPUT_IDS[field]}`,
    text: errors[field] ?? "",
  }));
  return (
    <form onSubmit={calculate} noValidate>
      <ErrorSummary key={attempt} errors={summary} />
      <DateInput
        id="period_start"
        legend="Accounting period start date"
        hint="For example, 1 4 2026"
        value={inputs.start}
        onChange={(start) => setInputs({ ...inputs, start })}
        error={errors.period_start}
      />
      <DateInput
        id="period_end"
        legend="Accounting period end date"
        hint="Up to 12 months after the start date"
        value={inputs.end}
        onChange={(end) => setInputs({ ...inputs, end })}
        error={errors.period_end}
      />
      <MoneyInput
        id="taxable_profits"
        label="Taxable profits"
        hint="Profits after allowable expenses, capital allowances and losses, in whole pounds."
        value={inputs.profits}
        onChange={(profits) => setInputs({ ...inputs, profits })}
        error={errors.taxable_profits}
      />
      <TextInput
        id="associated_companies"
        label="Number of associated companies"
        hint="Other companies under the same control as yours. This divides the profit limits between you."
        value={inputs.associated}
        onChange={(associated) => setInputs({ ...inputs, associated })}
        error={errors.associated_companies}
        width="3"
        inputMode="numeric"
      />
      <Button>Calculate Corporation Tax</Button>
    </form>
  );
}

const FAQS = [
  {
    question: "How is Corporation Tax worked out?",
    answer:
      "Since 1 April 2023, companies with profits of £50,000 or less pay the small profits rate of 19%. Companies with profits over £250,000 pay the main rate of 25%. In between, you pay the main rate less marginal relief, so the rate rises gradually.",
  },
  {
    question: "What is marginal relief?",
    answer:
      "Marginal relief is 3/200 × (upper limit − augmented profits) × (taxable profits ÷ augmented profits). With £100,000 of profits and no associated companies, that is £2,250, so you pay £22,750 instead of £25,000.",
  },
  {
    question: "How do associated companies change my tax?",
    answer:
      "The £50,000 and £250,000 limits are shared equally between your company and its associated companies. With one associated company, your limits are £25,000 and £125,000.",
  },
  {
    question: "What if my accounting period is shorter than 12 months?",
    answer: "The limits are reduced in proportion. For a 6-month period, they are roughly halved.",
  },
  {
    question: "What if my accounting period spans 1 April?",
    answer:
      "Profits are split between the two financial years by the number of days in each, and each part is taxed at that year's rates.",
  },
  {
    question: "When do I pay?",
    answer:
      "Corporation Tax is normally due 9 months and 1 day after the end of your accounting period. The return itself is due 12 months after the end of the period.",
  },
];

export function CalculatorPage() {
  const [tax, setTax] = useState<TaxComputation | null>(null);

  return (
    <div className="govuk-grid-row">
      <div className="govuk-grid-column-two-thirds">
        <h1 className="govuk-heading-xl">Corporation Tax calculator</h1>
        <p className="govuk-body-l">
          Estimate your company's Corporation Tax for any accounting period from 1 April 2017 to 31
          March 2027, including marginal relief, associated companies and periods that span two
          financial years.
        </p>
        <CalculatorForm onResult={setTax} />
        {tax ? <Result tax={tax} /> : null}

        <h2 className="govuk-heading-m">Ready to prepare your return?</h2>
        <p className="govuk-body">
          <Link className="govuk-link" to="/file">
            Start your Company Tax Return
          </Link>{" "}
          – it's free, and we work out every box for you.
        </p>

        <h2 className="govuk-heading-m">Common questions</h2>
        {FAQS.map((faq) => (
          <details className="govuk-details" key={faq.question}>
            <summary className="govuk-details__summary">
              <span className="govuk-details__summary-text">{faq.question}</span>
            </summary>
            <div className="govuk-details__text">{faq.answer}</div>
          </details>
        ))}
      </div>
    </div>
  );
}
