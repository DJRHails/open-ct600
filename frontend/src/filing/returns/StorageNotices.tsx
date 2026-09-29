/**
 * What the user needs to know about the returns saved in this browser, shown above every filing
 * page: an answer that could not be saved, a change made in another tab, and a draft from an
 * earlier version that cannot be read.
 */
import { useState } from "react";
import { Link } from "react-router";

import { NotificationBanner, WarningText } from "@/components/content";
import { Button } from "@/components/forms";
import { saveFile } from "@/filing/Downloads";
import { RETURNS } from "@/filing/paths";
import { failureReason, LEGACY_DRAFT_KEY } from "@/filing/returns/savedReturns";

export type OtherTabChange = "changed" | "deleted";

/** An answer was not saved: it is kept in this tab, and exporting the return keeps a copy. */
function SaveFailure({ reason }: { reason: string }) {
  return (
    <div className="govuk-error-summary">
      <div role="alert">
        <h2 className="govuk-error-summary__title">Your answers could not be saved</h2>
        <div className="govuk-error-summary__body">
          <p className="govuk-body">
            This browser did not save your latest answers ({reason}). They are kept on this page
            until you close the tab. <Link to={RETURNS}>Export this return to keep a copy</Link> of
            your answers.
          </p>
        </div>
      </div>
    </div>
  );
}

function OtherTab({ change }: { change: OtherTabChange }) {
  return (
    <NotificationBanner title="Important" id="banner-other-tab">
      {change === "changed" ? (
        <>
          <p className="govuk-notification-banner__heading">
            This return was changed in another tab
          </p>
          <p className="govuk-body">
            Pages you open now show the latest answers. If you save this page, your answers on it
            replace the other tab’s.
          </p>
        </>
      ) : (
        <>
          <p className="govuk-notification-banner__heading">
            The return you had open was deleted in another tab
          </p>
          <p className="govuk-body">
            Your other returns are unchanged. Answers you save now start a new return.
          </p>
        </>
      )}
    </NotificationBanner>
  );
}

/**
 * A draft an earlier version saved that cannot be read. The returns are unaffected; the user can
 * download it or delete it, and deleting it removes nothing else.
 */
function DamagedLegacy({ raw }: { raw: string }) {
  const [confirming, setConfirming] = useState(false);
  const [gone, setGone] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);
  if (gone) return null;

  function remove() {
    try {
      window.localStorage.removeItem(LEGACY_DRAFT_KEY);
      setGone(true);
    } catch (error) {
      setFailure(`It could not be deleted: ${failureReason(error)}`);
    }
  }

  return (
    <NotificationBanner title="Important" id="banner-damaged-legacy">
      <p className="govuk-notification-banner__heading">
        A return saved by an earlier version cannot be read
      </p>
      <p className="govuk-body">
        It was saved in this browser before Open CT600 could keep several returns, and it is
        damaged. Your other returns are not affected. Download it to keep a copy, or delete it.
      </p>
      {failure ? <p className="govuk-body">{failure}</p> : null}
      {confirming ? (
        <>
          <WarningText>This deletes the unreadable return. You cannot undo this.</WarningText>
          <div className="govuk-button-group">
            <Button type="button" variant="warning" onClick={remove}>
              Yes, delete the unreadable return
            </Button>
            <button
              type="button"
              className="govuk-link govuk-body app-link-button"
              onClick={() => setConfirming(false)}
            >
              Cancel
            </button>
          </div>
        </>
      ) : (
        <div className="govuk-button-group">
          <Button
            type="button"
            variant="secondary"
            onClick={() =>
              saveFile(new Blob([raw], { type: "application/json" }), "open-ct600-old-draft.json")
            }
          >
            Download it
          </Button>
          <Button type="button" variant="warning" onClick={() => setConfirming(true)}>
            Delete it
          </Button>
        </div>
      )}
    </NotificationBanner>
  );
}

export function StorageNotices(props: {
  failure: string | null;
  otherTab: OtherTabChange | null;
  damagedLegacy: string | null;
}) {
  return (
    <>
      {props.failure === null ? null : <SaveFailure reason={props.failure} />}
      {props.otherTab === null ? null : <OtherTab change={props.otherTab} />}
      {props.damagedLegacy === null ? null : <DamagedLegacy raw={props.damagedLegacy} />}
    </>
  );
}
