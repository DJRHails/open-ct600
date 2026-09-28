import { createContext, type ReactNode, useCallback, useContext, useMemo, useState } from "react";

import type { SubmissionReceipt } from "@/api";
import type { Draft, SectionKey } from "@/filing/model";

const DRAFT_KEY = "open-ct600:draft:v1";
const RECEIPT_KEY = "open-ct600:receipt:v1";

/**
 * The draft lives in localStorage so the user can come back to it later. The receipt of a
 * submitted return lives in sessionStorage, so it disappears when the tab is closed.
 */
function read<T>(storage: Storage, key: string, fallback: T): T {
  const stored = storage.getItem(key);
  if (stored === null) return fallback;
  try {
    return JSON.parse(stored) as T;
  } catch (error) {
    console.error(`Discarding unreadable saved data in storage["${key}"]`, error);
    storage.removeItem(key);
    return fallback;
  }
}

type DraftStore = {
  draft: Draft;
  receipt: SubmissionReceipt | null;
  saveSection: <K extends SectionKey>(key: K, value: NonNullable<Draft[K]>) => void;
  /** Forget everything this browser holds: the draft and any submission receipt. */
  deleteAnswers: () => void;
  /** Keep the receipt for the confirmation page and discard the finished draft. */
  recordSubmission: (receipt: SubmissionReceipt) => void;
};

const DraftContext = createContext<DraftStore | null>(null);

export function DraftProvider({ children }: { children: ReactNode }) {
  const [draft, setDraft] = useState<Draft>(() => read(window.localStorage, DRAFT_KEY, {}));
  const [receipt, setReceipt] = useState<SubmissionReceipt | null>(() =>
    read(window.sessionStorage, RECEIPT_KEY, null),
  );

  const saveSection = useCallback(<K extends SectionKey>(key: K, value: NonNullable<Draft[K]>) => {
    setDraft((current) => {
      const next = { ...current, [key]: value };
      window.localStorage.setItem(DRAFT_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const deleteAnswers = useCallback(() => {
    window.localStorage.removeItem(DRAFT_KEY);
    window.sessionStorage.removeItem(RECEIPT_KEY);
    setDraft({});
    setReceipt(null);
  }, []);

  const recordSubmission = useCallback((submitted: SubmissionReceipt) => {
    window.sessionStorage.setItem(RECEIPT_KEY, JSON.stringify(submitted));
    window.localStorage.removeItem(DRAFT_KEY);
    setReceipt(submitted);
    setDraft({});
  }, []);

  const store = useMemo(
    () => ({ draft, receipt, saveSection, deleteAnswers, recordSubmission }),
    [draft, receipt, saveSection, deleteAnswers, recordSubmission],
  );
  return <DraftContext.Provider value={store}>{children}</DraftContext.Provider>;
}

export function useDraft(): DraftStore {
  const store = useContext(DraftContext);
  if (!store) throw new Error("useDraft must be used inside <DraftProvider>");
  return store;
}
