import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import type { CT600Return, HmrcReceipt, PageCode, SubmissionReceipt } from "@/api";
import type { Draft } from "@/filing/model";
import {
  addReturn,
  currentReturn,
  deleteReturn,
  loadReturns,
  markSubmitted,
  openReturnChange,
  readReturns,
  replaceReturn,
  RETURNS_KEY,
  type ReturnsStore,
  type SavedReturn,
  saveChange,
  updateCurrent,
} from "@/filing/returns/savedReturns";
import { type OtherTabChange, StorageNotices } from "@/filing/returns/StorageNotices";
import { StorageProblemPage } from "@/filing/returns/StorageProblemPage";
import type { RawTree } from "@/filing/supplementary/answers";

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
 * The returns live in localStorage so the user can come back to them later. The receipt of a
 * submitted return lives in sessionStorage, so it disappears when the tab is closed.
 * Government Gateway credentials are never stored anywhere.
 */
function readReceipt(): Receipt | null {
  let stored: string | null;
  try {
    stored = window.sessionStorage.getItem(RECEIPT_KEY);
  } catch (error) {
    console.error("sessionStorage cannot be read, so no receipt is shown", error);
    return null;
  }
  if (stored === null) return null;
  try {
    return JSON.parse(stored) as Receipt;
  } catch (error) {
    console.error(`Discarding unreadable receipt in sessionStorage["${RECEIPT_KEY}"]`, error);
    window.sessionStorage.removeItem(RECEIPT_KEY);
    return null;
  }
}

/** Keep the receipt for this tab; if the browser refuses, it stays in memory for this visit. */
function storeReceipt(receipt: Receipt | null) {
  try {
    if (receipt === null) window.sessionStorage.removeItem(RECEIPT_KEY);
    else window.sessionStorage.setItem(RECEIPT_KEY, JSON.stringify(receipt));
  } catch (error) {
    console.error("sessionStorage cannot be written, so the receipt is kept in memory", error);
  }
}

const NOT_STARTED: Draft = {};
const now = () => new Date().toISOString();
const newId = () => crypto.randomUUID();

type DraftStore = {
  /** The answers of the return the filing pages show; empty for a return not yet started. */
  draft: Draft;
  receipt: Receipt | null;
  /** Every return saved in this browser, oldest first. */
  returns: SavedReturn[];
  currentId: string | null;
  saveSection: <K extends keyof Draft>(key: K, value: NonNullable<Draft[K]>) => void;
  /** Record which supplementary pages apply, forgetting answers to pages no longer chosen. */
  saveChosenPages: (codes: PageCode[]) => void;
  savePageAnswers: (code: PageCode, answers: RawTree) => void;
  /** Show a saved return on the filing pages. */
  openReturn: (id: string) => void;
  /** Show an empty return; the first answer saved adds it to the saved returns. */
  startNewReturn: () => void;
  deleteReturn: (id: string) => void;
  /** Save imported answers as a new return. */
  importReturn: (draft: Draft) => void;
  /** Put imported answers in place of a saved return's. */
  replaceWithImport: (id: string, draft: Draft) => void;
  /** Delete the return the filing pages show and any submission receipt. */
  deleteAnswers: () => void;
  /** Keep the receipt for the confirmation page and mark the finished return submitted. */
  recordSubmission: (receipt: Receipt) => void;
};

const DraftContext = createContext<DraftStore | null>(null);

/** Hold the saved returns, or explain why they cannot be opened instead of losing them. */
export function DraftProvider({ children }: { children: ReactNode }) {
  const load = () => loadReturns(window.localStorage, now(), newId());
  const [loaded, setLoaded] = useState(load);
  if (!loaded.ok) {
    return <StorageProblemPage problem={loaded.problem} onCleared={() => setLoaded(load())} />;
  }
  return (
    <ReturnsProvider
      initial={loaded.store}
      damagedLegacy={loaded.damagedLegacy ?? null}
      unsaved={loaded.unsaved ?? null}
    >
      {children}
    </ReturnsProvider>
  );
}

type ProviderProps = {
  initial: ReturnsStore;
  damagedLegacy: string | null;
  unsaved: string | null;
  children: ReactNode;
};

/**
 * This tab's copy of the saved returns. Every change is saved at once, made to the returns as
 * stored (see ``saveChange``), and the copy follows changes other tabs save. A change that
 * cannot be written stays in this tab, and the user is told to export it.
 */
function useReturnsStore(initial: ReturnsStore, unsavedOnLoad: string | null) {
  const [store, setStore] = useState(initial);
  const [notices, setNotices] = useState<{
    failure: string | null;
    otherTab: OtherTabChange | null;
  }>({ failure: unsavedOnLoad, otherTab: null });
  const tab = useRef(store);
  const unsavedId = useRef<string | null>(unsavedOnLoad === null ? null : initial.currentId);

  const commit = useCallback((change: (saved: ReturnsStore) => ReturnsStore) => {
    const result = saveChange(window.localStorage, tab.current, change, unsavedId.current);
    unsavedId.current = result.failure === null ? null : result.store.currentId;
    tab.current = result.store;
    setStore(result.store);
    // Once this tab saves, its answers are the latest: a notice about another tab is stale.
    setNotices({ failure: result.failure, otherTab: result.openDeleted ? "deleted" : null });
  }, []);

  useEffect(() => {
    function followOtherTabs(event: StorageEvent) {
      if (event.key !== null && event.key !== RETURNS_KEY) return;
      const latest = readReturns(window.localStorage);
      if (!latest.ok) return;
      const change = openReturnChange(tab.current, latest.store);
      const currentId = change === "deleted" ? null : tab.current.currentId;
      tab.current = { currentId, returns: latest.store.returns };
      setStore(tab.current);
      if (change) setNotices((shown) => ({ ...shown, otherTab: change }));
    }
    window.addEventListener("storage", followOtherTabs);
    return () => window.removeEventListener("storage", followOtherTabs);
  }, []);

  return { store, notices, commit };
}

function ReturnsProvider({ initial, damagedLegacy, unsaved, children }: ProviderProps) {
  const { store, notices, commit } = useReturnsStore(initial, unsaved);
  const [receipt, setReceipt] = useState<Receipt | null>(readReceipt);

  const update = useCallback(
    (change: (answers: Draft) => Draft) =>
      commit((saved) => updateCurrent(saved, change, now(), newId())),
    [commit],
  );
  const actions = useMemo(
    () => ({
      saveSection: <K extends keyof Draft>(key: K, value: NonNullable<Draft[K]>) =>
        update((answers) => ({ ...answers, [key]: value })),
      saveChosenPages: (codes: PageCode[]) =>
        update((answers) => {
          const kept = Object.entries(answers.supplementary_pages ?? {}).filter(([code]) =>
            codes.includes(code as PageCode),
          );
          return { ...answers, chosen_pages: codes, supplementary_pages: Object.fromEntries(kept) };
        }),
      savePageAnswers: (code: PageCode, pageAnswers: RawTree) =>
        update((answers) => ({
          ...answers,
          supplementary_pages: { ...answers.supplementary_pages, [code]: pageAnswers },
        })),
      openReturn: (id: string) => commit((saved) => ({ ...saved, currentId: id })),
      startNewReturn: () => commit((saved) => ({ ...saved, currentId: null })),
      deleteReturn: (id: string) => commit((saved) => deleteReturn(saved, id)),
      importReturn: (draft: Draft) =>
        commit((saved) => addReturn(saved, draft, now(), newId(), { open: false })),
      replaceWithImport: (id: string, draft: Draft) =>
        commit((saved) => replaceReturn(saved, id, draft, now())),
      deleteAnswers: () => {
        storeReceipt(null);
        setReceipt(null);
        commit((saved) =>
          saved.currentId === null ? saved : deleteReturn(saved, saved.currentId),
        );
      },
      recordSubmission: (submitted: Receipt) => {
        storeReceipt(submitted);
        setReceipt(submitted);
        commit((saved) => markSubmitted(saved, now()));
      },
    }),
    [update, commit],
  );

  const value = useMemo(
    () => ({
      draft: currentReturn(store)?.draft ?? NOT_STARTED,
      receipt,
      returns: store.returns,
      currentId: store.currentId,
      ...actions,
    }),
    [store, receipt, actions],
  );
  return (
    <DraftContext.Provider value={value}>
      <StorageNotices
        failure={notices.failure}
        otherTab={notices.otherTab}
        damagedLegacy={damagedLegacy}
      />
      {children}
    </DraftContext.Provider>
  );
}

export function useDraft(): DraftStore {
  const store = useContext(DraftContext);
  if (!store) throw new Error("useDraft must be used inside <DraftProvider>");
  return store;
}
