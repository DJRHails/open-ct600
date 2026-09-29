import { type FormEvent, useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router";

import { BackLink, TwoThirds, usePageTitle, WarningText } from "@/components/content";
import { Button } from "@/components/forms";
import { useDraft } from "@/filing/draft";
import { RETURNS } from "@/filing/paths";
import type { ReturnsNotice } from "@/filing/returns/ReturnsPage";
import { returnLabel } from "@/filing/returns/savedReturns";

/** The GOV.UK confirmation before deleting a saved return, which cannot be undone. */
export function DeleteReturnPage() {
  usePageTitle("Are you sure you want to delete this return?");
  const { id } = useParams();
  const { returns, deleteReturn } = useDraft();
  const navigate = useNavigate();
  // Once deleted, the return is gone before the navigation to Your returns with the notice.
  const [deleted, setDeleted] = useState(false);
  const saved = returns.find((candidate) => candidate.id === id);

  if (!saved) return deleted ? null : <Navigate to={RETURNS} replace />;
  const label = returnLabel(saved.draft);

  function confirm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!saved) return;
    setDeleted(true);
    deleteReturn(saved.id);
    const state: ReturnsNotice = { notice: `You deleted the return for ${label}` };
    void navigate(RETURNS, { state });
  }

  return (
    <>
      <BackLink to={RETURNS} />
      <TwoThirds>
        <span className="govuk-caption-l">{label}</span>
        <h1 className="govuk-heading-l">Are you sure you want to delete this return?</h1>
        <WarningText>
          You cannot get the answers back after you delete them. Export the return first if you
          might need it.
        </WarningText>
        <form onSubmit={confirm} noValidate>
          <div className="govuk-button-group">
            <Button variant="warning">Yes, delete this return</Button>
            <Link className="govuk-link" to={RETURNS}>
              No, keep it
            </Link>
          </div>
        </form>
      </TwoThirds>
    </>
  );
}
