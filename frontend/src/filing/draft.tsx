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
  replaceReturn,
  type ReturnsStore,
  type SavedReturn,
  updateCurrent,
  writeReturns,
} from "@/filing/returns/savedReturns";
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
  const stored = window.sessionStorage.getItem(RECEIPT_KEY);
  if (stored === null) return null;
  try {
    return JSON.parse(stored) as Receipt;
  } catch (error) {
    console.error(`Discarding unreadable receipt in sessionStorage["${RECEIPT_KEY}"]`, error);
    window.sessionStorage.removeItem(RECEIPT_KEY);
    return null;
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
  return <ReturnsProvider initial={loaded.store}>{children}</ReturnsProvider>;
}

/** Keep ``store`` in localStorage whenever it changes after loading. */
function usePersisted(store: ReturnsStore) {
  const loaded = useRef(store);
  useEffect(() => {
    if (store !== loaded.current) writeReturns(window.localStorage, store);
  }, [store]);
}

function ReturnsProvider({ initial, children }: { initial: ReturnsStore; children: ReactNode }) {
  const [store, setStore] = useState(initial);
  const [receipt, setReceipt] = useState<Receipt | null>(readReceipt);
  usePersisted(store);

  const update = useCallback(
    (change: (answers: Draft) => Draft) =>
      setStore((saved) => updateCurrent(saved, change, now(), newId())),
    [],
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
      openReturn: (id: string) => setStore((saved) => ({ ...saved, currentId: id })),
      startNewReturn: () => setStore((saved) => ({ ...saved, currentId: null })),
      deleteReturn: (id: string) => setStore((saved) => deleteReturn(saved, id)),
      importReturn: (draft: Draft) =>
        setStore((saved) => addReturn(saved, draft, now(), newId(), { open: false })),
      replaceWithImport: (id: string, draft: Draft) =>
        setStore((saved) => replaceReturn(saved, id, draft, now())),
      deleteAnswers: () => {
        window.sessionStorage.removeItem(RECEIPT_KEY);
        setReceipt(null);
        setStore((saved) =>
          saved.currentId === null ? saved : deleteReturn(saved, saved.currentId),
        );
      },
      recordSubmission: (submitted: Receipt) => {
        window.sessionStorage.setItem(RECEIPT_KEY, JSON.stringify(submitted));
        setReceipt(submitted);
        setStore((saved) => markSubmitted(saved, now()));
      },
    }),
    [update],
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
  return <DraftContext.Provider value={value}>{children}</DraftContext.Provider>;
}

export function useDraft(): DraftStore {
  const store = useContext(DraftContext);
  if (!store) throw new Error("useDraft must be used inside <DraftProvider>");
  return store;
}
