import { Link, useLocation, useNavigate } from "react-router";

import { SummaryList, usePageTitle, WarningText } from "@/components/content";
import { Button } from "@/components/forms";
import { saveFile } from "@/filing/Downloads";
import { useDraft } from "@/filing/draft";
import { needsSchema } from "@/filing/model";
import { deleteReturnPath, IMPORT_RETURN, TASK_LIST } from "@/filing/paths";
import { exportReturn } from "@/filing/returns/returnFile";
import {
  isRecord,
  type ReturnStatus,
  returnLabel,
  returnStatus,
  type SavedReturn,
  STATUS_LABELS,
} from "@/filing/returns/savedReturns";
import { useSchemaPages } from "@/filing/supplementary/schema";

const SAVED_AT = new Intl.DateTimeFormat("en-GB", {
  dateStyle: "long",
  timeStyle: "short",
  timeZone: "Europe/London",
});

const TAG_CLASSES: Record<ReturnStatus, string> = {
  "in-progress": "govuk-tag govuk-tag--blue",
  ready: "govuk-tag govuk-tag--light-blue",
  submitted: "govuk-tag govuk-tag--green",
};

/** What the pages after this one say they did, like deleting a return, passed as route state. */
export type ReturnsNotice = { notice: string };

function useNotice(): string | null {
  const { state } = useLocation();
  return isRecord(state) && typeof state.notice === "string" ? state.notice : null;
}

function SuccessBanner({ children }: { children: string }) {
  return (
    <div
      className="govuk-notification-banner govuk-notification-banner--success"
      role="alert"
      aria-labelledby="returns-notice-title"
    >
      <div className="govuk-notification-banner__header">
        <h2 className="govuk-notification-banner__title" id="returns-notice-title">
          Success
        </h2>
      </div>
      <div className="govuk-notification-banner__content">
        <p className="govuk-notification-banner__heading">{children}</p>
      </div>
    </div>
  );
}

/** An action read out with the return it is for, like "Delete Acme Widgets Ltd — …". */
function ActionText({ action, label }: { action: string; label: string }) {
  return (
    <>
      {`${action} `}
      <span className="govuk-visually-hidden">{label}</span>
    </>
  );
}

function ReturnCard({ saved, status }: { saved: SavedReturn; status: ReturnStatus }) {
  const { openReturn } = useDraft();
  const label = returnLabel(saved.draft);

  function download() {
    const { blob, filename } = exportReturn(saved.draft, new Date().toISOString());
    saveFile(blob, filename);
  }

  const rows = [
    {
      key: "Status",
      value: <strong className={TAG_CLASSES[status]}>{STATUS_LABELS[status]}</strong>,
    },
    { key: "Last saved", value: SAVED_AT.format(new Date(saved.updated_at)) },
    { key: "Started", value: SAVED_AT.format(new Date(saved.created_at)) },
  ];
  return (
    <div className="govuk-summary-card">
      <div className="govuk-summary-card__title-wrapper">
        <h2 className="govuk-summary-card__title">{label}</h2>
        <ul className="govuk-summary-card__actions">
          {status === "submitted" ? null : (
            <li className="govuk-summary-card__action">
              <Link className="govuk-link" to={TASK_LIST} onClick={() => openReturn(saved.id)}>
                <ActionText action="Continue" label={label} />
              </Link>
            </li>
          )}
          <li className="govuk-summary-card__action">
            <button type="button" className="govuk-link app-link-button" onClick={download}>
              <ActionText action="Export" label={label} />
            </button>
          </li>
          <li className="govuk-summary-card__action">
            <Link className="govuk-link" to={deleteReturnPath(saved.id)}>
              <ActionText action="Delete" label={label} />
            </Link>
          </li>
        </ul>
      </div>
      <div className="govuk-summary-card__content">
        <SummaryList rows={rows} />
      </div>
    </div>
  );
}

function ReturnCards() {
  const { returns } = useDraft();
  const schema = useSchemaPages(returns.some((saved) => needsSchema(saved.draft)));
  const pages = schema.status === "ready" ? schema.pages : undefined;

  if (returns.length === 0) {
    return <p className="govuk-body">You have no returns saved in this browser.</p>;
  }
  const newestFirst = [...returns].sort((a, b) => b.updated_at.localeCompare(a.updated_at));
  return newestFirst.map((saved) => (
    <ReturnCard key={saved.id} saved={saved} status={returnStatus(saved, pages)} />
  ));
}

export function ReturnsPage() {
  usePageTitle("Your returns");
  const notice = useNotice();
  const { startNewReturn } = useDraft();
  const navigate = useNavigate();

  function startNew() {
    startNewReturn();
    void navigate(TASK_LIST);
  }

  return (
    <div className="govuk-grid-row">
      <div className="govuk-grid-column-two-thirds">
        {notice ? <SuccessBanner>{notice}</SuccessBanner> : null}
        <h1 className="govuk-heading-xl">Your returns</h1>
        <p className="govuk-body">
          These are the Company Tax Returns saved in this browser. They are not saved anywhere else,
          and we cannot see them.
        </p>
        <p className="govuk-body">
          To keep a copy, or to carry on in another browser or on another device, export a return to
          a file and import it there.
        </p>
        <WarningText>
          An exported file contains the company’s tax details. Keep it somewhere safe and only share
          it with people you trust, such as your accountant.
        </WarningText>
        <ReturnCards />
        <div className="govuk-button-group">
          <Button type="button" onClick={startNew}>
            Start a new return
          </Button>
          <Link className="govuk-button govuk-button--secondary" to={IMPORT_RETURN}>
            Import a return from a file
          </Link>
        </div>
      </div>
    </div>
  );
}
