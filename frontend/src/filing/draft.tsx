import { createContext, type ReactNode, useCallback, useContext, useMemo, useState } from "react";

import type { CT600Return, HmrcReceipt, PageCode, SubmissionReceipt } from "@/api";
import type { Draft } from "@/filing/model";
import type { RawTree } from "@/filing/supplementary/answers";

const DRAFT_KEY = "open-ct600:draft:v1";
const RECEIPT_KEY = "open-ct600:receipt:v2";

/** What the confirmation page shows: a demonstration receipt, or HMRC's receipt. */
export type Receipt =
  | ({ kind: "demo" } & SubmissionReceipt)
  | ({
      kind: "hmrc";
      company: CT600Return["company"];
      period: CT600Return["period"];
      signatory: string;
    } & HmrcReceipt);

/**
 * The draft lives in localStorage so the user can come back to it later. The receipt of a
 * submitted return lives in sessionStorage, so it disappears when the tab is closed.
 * Government Gateway credentials are never stored anywhere.
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
  receipt: Receipt | null;
  saveSection: <K extends keyof Draft>(key: K, value: NonNullable<Draft[K]>) => void;
  /** Record which supplementary pages apply, forgetting answers to pages no longer chosen. */
  saveChosenPages: (codes: PageCode[]) => void;
  savePageAnswers: (code: PageCode, answers: RawTree) => void;
  /** Forget everything this browser holds: the draft and any submission receipt. */
  deleteAnswers: () => void;
  /** Keep the receipt for the confirmation page and discard the finished draft. */
  recordSubmission: (receipt: Receipt) => void;
};

const DraftContext = createContext<DraftStore | null>(null);

export function DraftProvider({ children }: { children: ReactNode }) {
  const [draft, setDraft] = useState<Draft>(() => read(window.localStorage, DRAFT_KEY, {}));
  const [receipt, setReceipt] = useState<Receipt | null>(() =>
    read(window.sessionStorage, RECEIPT_KEY, null),
  );

  const update = useCallback((change: (current: Draft) => Draft) => {
    setDraft((current) => {
      const next = change(current);
      window.localStorage.setItem(DRAFT_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const saveSection = useCallback(
    <K extends keyof Draft>(key: K, value: NonNullable<Draft[K]>) =>
      update((current) => ({ ...current, [key]: value })),
    [update],
  );

  const saveChosenPages = useCallback(
    (codes: PageCode[]) =>
      update((current) => {
        const kept = Object.entries(current.supplementary_pages ?? {}).filter(([code]) =>
          codes.includes(code as PageCode),
        );
        return { ...current, chosen_pages: codes, supplementary_pages: Object.fromEntries(kept) };
      }),
    [update],
  );

  const savePageAnswers = useCallback(
    (code: PageCode, answers: RawTree) =>
      update((current) => ({
        ...current,
        supplementary_pages: { ...current.supplementary_pages, [code]: answers },
      })),
    [update],
  );

  const deleteAnswers = useCallback(() => {
    window.localStorage.removeItem(DRAFT_KEY);
    window.sessionStorage.removeItem(RECEIPT_KEY);
    setDraft({});
    setReceipt(null);
  }, []);

  const recordSubmission = useCallback((submitted: Receipt) => {
    window.sessionStorage.setItem(RECEIPT_KEY, JSON.stringify(submitted));
    window.localStorage.removeItem(DRAFT_KEY);
    setReceipt(submitted);
    setDraft({});
  }, []);

  const store = useMemo(
    () => ({
      draft,
      receipt,
      saveSection,
      saveChosenPages,
      savePageAnswers,
      deleteAnswers,
      recordSubmission,
    }),
    [
      draft,
      receipt,
      saveSection,
      saveChosenPages,
      savePageAnswers,
      deleteAnswers,
      recordSubmission,
    ],
  );
  return <DraftContext.Provider value={store}>{children}</DraftContext.Provider>;
}

export function useDraft(): DraftStore {
  const store = useContext(DraftContext);
  if (!store) throw new Error("useDraft must be used inside <DraftProvider>");
  return store;
}
