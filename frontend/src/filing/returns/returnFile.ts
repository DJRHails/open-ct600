/**
 * A saved return as a file the user keeps: exported from one browser, imported into another.
 * The file is a versioned envelope around the draft, and is not encrypted.
 */
import { draftShapeProblem } from "@/filing/returns/draftShape";
import { type Draft, savedPeriod, withAnswersAddedLater } from "@/filing/model";
import { isRecord } from "@/filing/returns/savedReturns";

export const FILE_FORMAT = "open-ct600-return";
/** The envelope's version; a file with a later one comes from a newer Open CT600. */
export const FILE_VERSION = 1;
export const MAX_FILE_BYTES = 1_000_000;

export type ReturnFile = {
  format: typeof FILE_FORMAT;
  version: typeof FILE_VERSION;
  exported_at: string;
  app_version: string;
  draft: Draft;
};

function slug(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

/** Like ``ct600-acme-widgets-ltd-2025-03-31.json``: the company and the period's end. */
export function exportFilename(draft: Draft): string {
  const parts = ["ct600", slug(draft.company?.name ?? "") || "return", savedPeriod(draft)?.end];
  return `${parts.filter(Boolean).join("-")}.json`;
}

export function exportReturn(draft: Draft, exportedAt: string): { blob: Blob; filename: string } {
  const file: ReturnFile = {
    format: FILE_FORMAT,
    version: FILE_VERSION,
    exported_at: exportedAt,
    app_version: APP_VERSION,
    draft,
  };
  const blob = new Blob([JSON.stringify(file, null, 2)], { type: "application/json" });
  return { blob, filename: exportFilename(draft) };
}

export type Imported = { ok: true; draft: Draft } | { ok: false; error: string };

const NOT_OURS =
  "The selected file is not an Open CT600 return. Choose a file you exported from Your returns";

/** Check a file's text: an Open CT600 envelope this site can read, around a draft. */
export function parseReturnFile(text: string): Imported {
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    return {
      ok: false,
      error: "The selected file is damaged and cannot be read. Export the return again",
    };
  }
  if (!isRecord(parsed) || parsed.format !== FILE_FORMAT) return { ok: false, error: NOT_OURS };
  const { version } = parsed;
  if (typeof version !== "number" || !Number.isInteger(version) || version < 1) {
    return { ok: false, error: NOT_OURS };
  }
  if (version > FILE_VERSION) {
    return {
      ok: false,
      error:
        "The selected file was exported from a newer version of Open CT600 than this site " +
        "runs. Import it on the site you exported it from",
    };
  }
  const problem = draftShapeProblem(parsed.draft);
  if (problem) {
    return {
      ok: false,
      error:
        "The selected file has been changed or is damaged, so it cannot be imported. " +
        `The problem is in ${problem}`,
    };
  }
  return { ok: true, draft: withAnswersAddedLater(parsed.draft as Draft) };
}

/** Check the chosen file, then its contents. */
export async function readReturnFile(file: File | undefined): Promise<Imported> {
  if (!file) return { ok: false, error: "Select a file to import" };
  if (!file.name.toLowerCase().endsWith(".json")) {
    return { ok: false, error: "The selected file must be a JSON file" };
  }
  if (file.size === 0) return { ok: false, error: "The selected file is empty" };
  if (file.size > MAX_FILE_BYTES) {
    return { ok: false, error: "The selected file must be smaller than 1MB" };
  }
  return parseReturnFile(await file.text());
}
