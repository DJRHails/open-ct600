import { useState } from "react";

import { TwoThirds, usePageTitle, WarningText } from "@/components/content";
import { Button } from "@/components/forms";
import { saveFile } from "@/filing/Downloads";
import { STORAGE_VERSION, type StorageProblem } from "@/filing/returns/savedReturns";

type ReadableProblem = Exclude<StorageProblem, { kind: "unavailable" }>;

const TITLE = "Your saved returns cannot be opened";

function Explanation({ problem }: { problem: ReadableProblem }) {
  if (problem.kind === "newer-version") {
    return (
      <>
        <p className="govuk-body">
          They were saved by a newer version of Open CT600 than this site runs. The saved data is
          version {problem.found}, and this site can only read version {STORAGE_VERSION}.
        </p>
        <p className="govuk-body">
          Go back to the site you saved them on to carry on, or download the saved data to keep a
          copy.
        </p>
      </>
    );
  }
  return (
    <p className="govuk-body">
      The data saved in this browser is damaged: {problem.reason}. Download it to keep a copy.
    </p>
  );
}

/** Delete the data that cannot be read, and only that: nothing readable is ever removed. */
function StartAgain({ problemKey, onCleared }: { problemKey: string; onCleared: () => void }) {
  const [confirming, setConfirming] = useState(false);

  function clear() {
    window.localStorage.removeItem(problemKey);
    onCleared();
  }

  return (
    <>
      <h2 className="govuk-heading-m">Start again</h2>
      <p className="govuk-body">
        If you do not need these returns, you can delete the data that cannot be opened and start
        again.
      </p>
      {confirming ? (
        <>
          <WarningText>
            This deletes the saved data that cannot be opened. You cannot undo this.
          </WarningText>
          <div className="govuk-button-group">
            <Button type="button" variant="warning" onClick={clear}>
              Yes, delete the saved data
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
        <Button type="button" variant="warning" onClick={() => setConfirming(true)}>
          Delete the saved data
        </Button>
      )}
    </>
  );
}

/** The browser will not let the site use its storage: there is nothing to download or delete. */
function Unavailable({ reason }: { reason: string }) {
  return (
    <TwoThirds>
      <h1 className="govuk-heading-l">{TITLE}</h1>
      <p className="govuk-body">
        This browser is not letting Open CT600 save or read returns ({reason}).
      </p>
      <p className="govuk-body">
        Check that the browser allows this site to store data: for example, that it is not blocking
        cookies and site data for it. Then reload the page.
      </p>
    </TwoThirds>
  );
}

/** Shown instead of the filing pages when the saved returns cannot be read. Nothing is lost. */
export function StorageProblemPage(props: { problem: StorageProblem; onCleared: () => void }) {
  usePageTitle(TITLE);
  const { problem } = props;
  if (problem.kind === "unavailable") return <Unavailable reason={problem.reason} />;

  const download = () => {
    const blob = new Blob([problem.raw], { type: "application/json" });
    saveFile(blob, "open-ct600-saved-data.json");
  };

  return (
    <TwoThirds>
      <h1 className="govuk-heading-l">{TITLE}</h1>
      <Explanation problem={problem} />
      <p className="govuk-body">Nothing has been deleted.</p>
      <Button type="button" variant="secondary" onClick={download}>
        Download the saved data
      </Button>
      <StartAgain problemKey={problem.key} onCleared={props.onCleared} />
    </TwoThirds>
  );
}
