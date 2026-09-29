import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router";

import { BackLink, TwoThirds, usePageTitle, WarningText } from "@/components/content";
import { Button, ErrorSummary, Radios } from "@/components/forms";
import { useDraft } from "@/filing/draft";
import type { Draft } from "@/filing/model";
import { RETURNS } from "@/filing/paths";
import { readReturnFile } from "@/filing/returns/returnFile";
import type { ReturnsNotice } from "@/filing/returns/ReturnsPage";
import { findSameReturn, returnLabel, type SavedReturn } from "@/filing/returns/savedReturns";
import { formatDate } from "@/format";

const FILE_ID = "return-file";
const REPLACE_ID = "replace";

function FileUpload({ error }: { error: string | null }) {
  const describedBy = [`${FILE_ID}-hint`, error ? `${FILE_ID}-error` : ""].filter(Boolean);
  return (
    <div className={error ? "govuk-form-group govuk-form-group--error" : "govuk-form-group"}>
      <label className="govuk-label govuk-label--m" htmlFor={FILE_ID}>
        Upload a file
      </label>
      <div id={`${FILE_ID}-hint`} className="govuk-hint">
        The file ends in .json, like ct600-acme-widgets-ltd-2025-03-31.json
      </div>
      {error ? (
        <p id={`${FILE_ID}-error`} className="govuk-error-message">
          <span className="govuk-visually-hidden">Error:</span> {error}
        </p>
      ) : null}
      <input
        className={error ? "govuk-file-upload govuk-file-upload--error" : "govuk-file-upload"}
        id={FILE_ID}
        name={FILE_ID}
        type="file"
        accept=".json,application/json"
        aria-describedby={describedBy.join(" ")}
      />
    </div>
  );
}

function ChooseFile({ onRead }: { onRead: (draft: Draft) => void }) {
  const [error, setError] = useState<string | null>(null);
  usePageTitle("Import a return from a file", error !== null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const field = event.currentTarget.elements.namedItem(FILE_ID);
    const file = field instanceof HTMLInputElement ? field.files?.[0] : undefined;
    const imported = await readReturnFile(file);
    if (imported.ok) onRead(imported.draft);
    else setError(imported.error);
  }

  return (
    <>
      <ErrorSummary errors={error ? [{ href: `#${FILE_ID}`, text: error }] : []} />
      <h1 className="govuk-heading-l">Import a return from a file</h1>
      <p className="govuk-body">
        Choose a file you exported from Your returns in Open CT600, in this or another browser. The
        return is added to the returns saved in this browser.
      </p>
      <WarningText>
        The file contains the company’s tax details. Keep it somewhere safe.
      </WarningText>
      <form onSubmit={(event) => void submit(event)} noValidate>
        <FileUpload error={error} />
        <div className="govuk-button-group">
          <Button>Import return</Button>
          <Link className="govuk-link" to={RETURNS}>
            Cancel
          </Link>
        </div>
      </form>
    </>
  );
}

type ReplaceProps = {
  existing: SavedReturn;
  onChoose: (replace: boolean) => void;
};

/** The file is for a company and period already saved: replace that return, or keep both. */
function ChooseReplace({ existing, onChoose }: ReplaceProps) {
  const [answer, setAnswer] = useState<"yes" | "no" | "">("");
  const [error, setError] = useState<string | null>(null);
  usePageTitle("You already have a return for this company and period", error !== null);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (answer === "") setError("Select yes to replace your saved return with the imported one");
    else onChoose(answer === "yes");
  }

  return (
    <>
      <ErrorSummary errors={error ? [{ href: `#${REPLACE_ID}`, text: error }] : []} />
      <span className="govuk-caption-l">{returnLabel(existing.draft)}</span>
      <h1 className="govuk-heading-l">You already have a return for this company and period</h1>
      <p className="govuk-body">
        The file is for the same company registration number and accounting period as a return saved
        in this browser.
      </p>
      <form onSubmit={submit} noValidate>
        <Radios
          name={REPLACE_ID}
          legend="Do you want to replace the saved return with the imported one?"
          options={[
            {
              value: "yes",
              label: "Yes, replace the saved return",
              hint: "The answers saved in this browser are deleted",
            },
            { value: "no", label: "No, keep both returns" },
          ]}
          value={answer}
          onChange={setAnswer}
          error={error ?? undefined}
        />
        <Button>Continue</Button>
      </form>
    </>
  );
}

/**
 * The file is for a company and period already submitted from this browser. Replacing that
 * return would clear its record of being submitted and let the same return be sent twice, so
 * the only choice offered is to keep both.
 */
function AlreadySubmitted({ existing, onImport }: { existing: SavedReturn; onImport: () => void }) {
  const title = "You have already submitted a return for this company and period";
  usePageTitle(title);
  const submittedOn = formatDate((existing.submitted_at ?? "").slice(0, 10));
  return (
    <>
      <span className="govuk-caption-l">{returnLabel(existing.draft)}</span>
      <h1 className="govuk-heading-l">{title}</h1>
      <p className="govuk-body">
        The file is for the same company registration number and accounting period as a return
        submitted from this browser on {submittedOn}. That return is kept as it is.
      </p>
      <p className="govuk-body">You can import the file as a separate return.</p>
      <WarningText>
        Do not submit it again unless you mean to send HMRC a second return for the same period.
      </WarningText>
      <div className="govuk-button-group">
        <Button type="button" onClick={onImport}>
          Import as a separate return
        </Button>
        <Link className="govuk-link" to={RETURNS}>
          Cancel
        </Link>
      </div>
    </>
  );
}

function Pending(props: { existing: SavedReturn; onChoose: (replace: boolean) => void }) {
  if (props.existing.submitted_at !== undefined) {
    return <AlreadySubmitted existing={props.existing} onImport={() => props.onChoose(false)} />;
  }
  return <ChooseReplace existing={props.existing} onChoose={props.onChoose} />;
}

export function ImportReturnPage() {
  const { returns, importReturn, replaceWithImport } = useDraft();
  const navigate = useNavigate();
  const [pending, setPending] = useState<{ draft: Draft; existing: SavedReturn } | null>(null);

  function finish(notice: string) {
    const state: ReturnsNotice = { notice };
    void navigate(RETURNS, { state });
  }

  function add(draft: Draft) {
    importReturn(draft);
    finish(`You imported the return for ${returnLabel(draft)}`);
  }

  function read(draft: Draft) {
    const existing = findSameReturn(returns, draft);
    if (existing) setPending({ draft, existing });
    else add(draft);
  }

  function choose(replace: boolean) {
    if (!pending) return;
    if (!replace) return add(pending.draft);
    replaceWithImport(pending.existing.id, pending.draft);
    finish(`You replaced the return for ${returnLabel(pending.draft)}`);
  }

  return (
    <>
      <BackLink to={RETURNS} />
      <TwoThirds>
        {pending ? (
          <Pending existing={pending.existing} onChoose={choose} />
        ) : (
          <ChooseFile onRead={read} />
        )}
      </TwoThirds>
    </>
  );
}
