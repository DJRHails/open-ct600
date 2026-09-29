import type { ReactNode } from "react";

import type { SchemaPage } from "@/api";
import { BackLink, TwoThirds, usePageTitle } from "@/components/content";
import { TASK_LIST } from "@/filing/paths";
import { useSchemaPages } from "@/filing/supplementary/schema";

type SchemaGateProps = { title: string; children: (pages: SchemaPage[]) => ReactNode };

/** Render ``children`` once HMRC's supplementary page definitions have loaded. */
export function SchemaGate({ title, children }: SchemaGateProps) {
  const schema = useSchemaPages();
  const failed = schema.status === "failed";
  usePageTitle(title, failed);
  if (schema.status === "ready") return children(schema.pages);
  return (
    <>
      <BackLink to={TASK_LIST} />
      <TwoThirds>
        <h1 className="govuk-heading-l">{title}</h1>
        {failed ? (
          <p className="govuk-body govuk-error-message">
            We could not load the questions for supplementary pages: {schema.message}. Try again
            later.
          </p>
        ) : (
          <p className="govuk-body">Loading the questions…</p>
        )}
      </TwoThirds>
    </>
  );
}
