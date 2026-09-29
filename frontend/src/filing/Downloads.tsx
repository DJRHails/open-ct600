import { useState } from "react";

import { api, type CT600Return, type ReturnDocument } from "@/api";
import { Button } from "@/components/forms";

const DOCUMENT_LABELS: Record<ReturnDocument, string> = {
  accounts: "Download the accounts (iXBRL)",
  computations: "Download the tax computations (iXBRL)",
  ct600: "Download the CT600 return (XML)",
};

const ORDER: ReturnDocument[] = ["accounts", "computations", "ct600"];

/** Save a file the browser already holds, like one the service generated. */
export function saveFile(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  // Revoking straight after the click can cancel the download in some browsers.
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

/** Buttons to download the documents the service generates from the return. */
export function Downloads({ ct600 }: { ct600: CT600Return }) {
  const [busy, setBusy] = useState<ReturnDocument | null>(null);
  const [failures, setFailures] = useState<Partial<Record<ReturnDocument, string>>>({});

  async function download(document: ReturnDocument) {
    setBusy(document);
    setFailures(({ [document]: _cleared, ...others }) => others);
    try {
      const { blob, filename } = await api.download(document, ct600);
      saveFile(blob, filename);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setFailures((current) => ({ ...current, [document]: message }));
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <h2 className="govuk-heading-m">Download your documents</h2>
      <p className="govuk-body">
        HMRC receives these with your return: the company's accounts and tax computations in iXBRL,
        and the return itself as XML. Keep copies with your records.
      </p>
      {ORDER.map((document) => {
        const failure = failures[document];
        return (
          <div
            className={failure ? "govuk-form-group govuk-form-group--error" : "govuk-form-group"}
            key={document}
          >
            {failure ? (
              <p className="govuk-error-message" id={`download-${document}-error`}>
                <span className="govuk-visually-hidden">Error:</span> We could not create this
                document: {failure}
              </p>
            ) : null}
            <Button
              type="button"
              variant="secondary"
              className="govuk-!-margin-bottom-0"
              disabled={busy !== null}
              aria-disabled={busy !== null}
              aria-describedby={failure ? `download-${document}-error` : undefined}
              onClick={() => void download(document)}
            >
              {DOCUMENT_LABELS[document]}
            </Button>
          </div>
        );
      })}
    </>
  );
}
