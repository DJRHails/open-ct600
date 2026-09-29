import { BackLink, usePageTitle } from "@/components/content";
import { TASK_LIST } from "@/filing/paths";

/** Shown while HMRC's page definitions load for a finished return, or if they cannot load. */
export function Pending({ title, failure }: { title: string; failure: string | null }) {
  usePageTitle(title, failure !== null);
  return (
    <>
      <BackLink to={TASK_LIST} />
      {failure !== null ? (
        <p className="govuk-body govuk-error-message">
          We could not load the questions for supplementary pages: {failure}
        </p>
      ) : (
        <p className="govuk-body">Loading your answers…</p>
      )}
    </>
  );
}
