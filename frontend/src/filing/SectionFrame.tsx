import { type FormEvent, type ReactNode, useState } from "react";

import { BackLink, TwoThirds, usePageTitle } from "@/components/content";
import { Button, type ErrorItem, ErrorSummary } from "@/components/forms";
import type { FieldErrors } from "@/filing/model";
import { useNextPage } from "@/filing/paths";

type SectionFrameProps = {
  title: string;
  errors: FieldErrors;
  /** Field keys in page order, so the error summary lists problems top to bottom. */
  fieldOrder: string[];
  /** The id of the input an error for ``field`` should link to. */
  inputId?: (field: string) => string;
  /** The error summary, when it is not built from ``errors`` and ``fieldOrder``. */
  summary?: ErrorItem[];
  onSubmit: () => void;
  intro?: ReactNode;
  /** A notification banner above the heading, such as one saying answers were prefilled. */
  banner?: ReactNode;
  caption?: string;
  backTo?: string;
  children: ReactNode;
};

/** The frame shared by every section of the return: back link, errors, heading, save button. */
export function SectionFrame(props: SectionFrameProps) {
  const { title, errors, fieldOrder, onSubmit, intro, children } = props;
  const inputId = props.inputId ?? ((field: string) => field);
  const { next } = useNextPage();
  const summary: ErrorItem[] =
    props.summary ??
    fieldOrder
      .filter((field) => errors[field])
      .map((field) => ({ href: `#${inputId(field)}`, text: errors[field] ?? "" }));
  usePageTitle(title, summary.length > 0);

  const [attempt, setAttempt] = useState(0);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAttempt(attempt + 1);
    onSubmit();
  }

  return (
    <>
      <BackLink to={props.backTo ?? next} />
      <TwoThirds>
        <ErrorSummary key={attempt} errors={summary} />
        {props.banner}
        <span className="govuk-caption-l">{props.caption ?? "Company Tax Return"}</span>
        <h1 className="govuk-heading-l">{title}</h1>
        {intro ? <p className="govuk-body">{intro}</p> : null}
        <form onSubmit={handleSubmit} noValidate>
          {children}
          <Button>Save and continue</Button>
        </form>
      </TwoThirds>
    </>
  );
}
