import type { ReactNode } from "react";

import type { SchemaPage } from "@/api";
import { BackLink, TwoThirds, usePageTitle } from "@/components/content";
import { TASK_LIST } from "@/filing/paths";
import { useSchemaPages } from "@/filing/supplementary/schema";

type SchemaGateProps = { title: string; children: (pages: SchemaPage[]) => ReactNode };

/** Render ``children`` once HMRC's supplementary page definitions have loaded. */
export function SchemaGate({ title, children }: SchemaGateProps) {
  const schema = useSchemaPages();
  if (schema.status === "ready") return children(schema.pages);
  return <Waiting title={title} failure={schema.status === "failed" ? schema.message : null} />;
}

/** Its own component, so the page title it sets never overrides the loaded page's title. */
function Waiting({ title, failure }: { title: string; failure: string | null }) {
  usePageTitle(title, failure !== null);
  return (
    <>
      <BackLink to={TASK_LIST} />
      <TwoThirds>
        <h1 className="govuk-heading-l">{title}</h1>
        {failure !== null ? (
          <p className="govuk-body govuk-error-message">
            We could not load the questions for supplementary pages: {failure}. Try again later.
          </p>
        ) : (
          <p className="govuk-body">Loading the questions…</p>
        )}
      </TwoThirds>
    </>
  );
}
