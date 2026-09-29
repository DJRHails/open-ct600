/**
 * The returns saved in this browser: every draft the user has started, which one the filing
 * pages are showing, and the one-time move from the single draft earlier versions kept.
 *
 * Everything here is a pure function of the stored data, so ``draft.tsx`` only has to hold the
 * result in React state and write it back.
 */
import type { SchemaPage } from "@/api";
import { type Draft, savedPeriod } from "@/filing/model";
import { toReturn } from "@/filing/payload";
import { formatDate } from "@/format";

export const RETURNS_KEY = "open-ct600:returns";
/** Where versions before several drafts kept the one draft. */
export const LEGACY_DRAFT_KEY = "open-ct600:draft:v1";
/** The format of ``RETURNS_KEY``. Version 1 was the single draft under ``LEGACY_DRAFT_KEY``. */
export const STORAGE_VERSION = 2;

export type SavedReturn = {
  id: string;
  created_at: string;
  updated_at: string;
  /** When the return was submitted from this browser. A submitted return is not changed again. */
  submitted_at?: string;
  draft: Draft;
};

export type ReturnsStore = {
  /** The return the filing pages show; ``null`` until the next answer saved starts a new one. */
  currentId: string | null;
  returns: SavedReturn[];
};

/**
 * Why the saved returns cannot be opened. ``raw`` is kept so the user can still download it, and
 * ``key`` says where it is, so deleting it removes nothing else. ``unavailable``: the browser
 * will not let the site read its storage at all.
 */
export type StorageProblem =
  | { kind: "newer-version"; found: number; raw: string; key: string }
  | { kind: "unreadable"; reason: string; raw: string; key: string }
  | { kind: "unavailable"; reason: string };

export type Loaded =
  | {
      ok: true;
      store: ReturnsStore;
      /** A draft left by an earlier version that cannot be read; the returns are unaffected. */
      damagedLegacy?: string;
      /** Why moving an earlier version's draft into the list could not be saved. */
      unsaved?: string;
    }
  | { ok: false; problem: StorageProblem };

export const EMPTY_STORE: ReturnsStore = { currentId: null, returns: [] };

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseJson(raw: string): { ok: true; value: unknown } | { ok: false; reason: string } {
  try {
    return { ok: true, value: JSON.parse(raw) as unknown };
  } catch (error) {
    return { ok: false, reason: error instanceof Error ? error.message : String(error) };
  }
}

function isSavedReturn(value: unknown): value is SavedReturn {
  return (
    isRecord(value) &&
    typeof value.id === "string" &&
    typeof value.created_at === "string" &&
    typeof value.updated_at === "string" &&
    (value.submitted_at === undefined || typeof value.submitted_at === "string") &&
    isRecord(value.draft)
  );
}

/** Read ``RETURNS_KEY``. A version this code does not know is a problem, never an empty list. */
function parseStored(raw: string): Loaded {
  const key = RETURNS_KEY;
  const unreadable = (reason: string): Loaded => ({
    ok: false,
    problem: { kind: "unreadable", reason, raw, key },
  });
  const parsed = parseJson(raw);
  if (!parsed.ok) return unreadable(`it is not valid JSON (${parsed.reason})`);
  const stored = parsed.value;
  if (!isRecord(stored) || typeof stored.version !== "number") {
    return unreadable("it has no version number");
  }
  if (stored.version > STORAGE_VERSION) {
    return { ok: false, problem: { kind: "newer-version", found: stored.version, raw, key } };
  }
  if (stored.version !== STORAGE_VERSION) {
    return unreadable(`it has version ${stored.version}, which this site has never written`);
  }
  const { currentId, returns } = stored;
  if (!Array.isArray(returns) || !returns.every(isSavedReturn)) {
    return unreadable("its list of returns is not in the expected format");
  }
  const known = typeof currentId === "string" && returns.some((saved) => saved.id === currentId);
  if (currentId !== null && !known) return unreadable("it points to a return that is not saved");
  return { ok: true, store: { currentId, returns } };
}

export function writeReturns(storage: Storage, store: ReturnsStore) {
  storage.setItem(RETURNS_KEY, JSON.stringify({ version: STORAGE_VERSION, ...store }));
}

/** An exception's message, for saying why storage could not be used. */
export function failureReason(error: unknown): string {
  // Storage throws DOMExceptions, which are not Errors in every environment.
  const message = isRecord(error) || error instanceof Error ? error.message : undefined;
  return typeof message === "string" ? message : String(error);
}

/** The returns as stored now, which another tab may have changed. */
export function readReturns(storage: Storage): Loaded {
  let raw: string | null;
  try {
    raw = storage.getItem(RETURNS_KEY);
  } catch (error) {
    return { ok: false, problem: { kind: "unavailable", reason: failureReason(error) } };
  }
  return raw === null ? { ok: true, store: EMPTY_STORE } : parseStored(raw);
}

/**
 * Load the saved returns. A draft left under ``LEGACY_DRAFT_KEY`` becomes a saved return and
 * the one the filing pages show, and the old key is removed, so nobody loses work on upgrade.
 * An old draft that cannot be read is left where it is and reported; it never blocks the
 * returns. ``now`` and ``newId`` date and name the moved return.
 */
export function loadReturns(storage: Storage, now: string, newId: string): Loaded {
  const loaded = readReturns(storage);
  if (!loaded.ok) return loaded;
  let legacy: string | null;
  try {
    legacy = storage.getItem(LEGACY_DRAFT_KEY);
  } catch (error) {
    return { ok: false, problem: { kind: "unavailable", reason: failureReason(error) } };
  }
  if (legacy === null) return loaded;

  const parsed = parseJson(legacy);
  if (!parsed.ok || !isRecord(parsed.value)) {
    return { ok: true, store: loaded.store, damagedLegacy: legacy };
  }
  const draft = parsed.value as Draft;
  const store =
    Object.keys(draft).length === 0
      ? loaded.store
      : addReturn(loaded.store, draft, now, newId, { open: true });
  try {
    writeReturns(storage, store);
    storage.removeItem(LEGACY_DRAFT_KEY);
  } catch (error) {
    return { ok: true, store, unsaved: failureReason(error) };
  }
  return { ok: true, store };
}

export type Saved = {
  /** The returns after the change, with every change other tabs saved. */
  store: ReturnsStore;
  /** Why the change could not be written, if it was not. */
  failure: string | null;
  /** The return this tab had open was deleted in another tab. */
  openDeleted: boolean;
};

/**
 * Save one change to the returns. Other tabs may have saved returns since this tab loaded, so
 * the change is made to the returns as stored now, never to this tab's copy of the list: a
 * return added, changed or deleted elsewhere stays that way. Only this tab's open return
 * (``tab.currentId``) is taken from this tab, and only if ``unsavedId`` names it: its latest
 * answers were not written before, so the stored copy is behind.
 */
export function saveChange(
  storage: Storage,
  tab: ReturnsStore,
  change: (store: ReturnsStore) => ReturnsStore,
  unsavedId: string | null,
): Saved {
  const latest = readReturns(storage);
  if (!latest.ok) {
    const failure =
      latest.problem.kind === "unavailable"
        ? latest.problem.reason
        : "the returns saved in this browser were changed by another version of Open CT600";
    return { store: change(tab), failure, openDeleted: false };
  }
  const unsaved = tab.returns.find((kept) => kept.id === unsavedId);
  const returns = latest.store.returns.map((kept) =>
    unsaved && kept.id === unsaved.id ? unsaved : kept,
  );
  const openKept = returns.some((kept) => kept.id === tab.currentId);
  const openDeleted = tab.currentId !== null && !openKept;
  const store = change({ currentId: openKept ? tab.currentId : null, returns });
  try {
    writeReturns(storage, store);
  } catch (error) {
    return { store, failure: failureReason(error), openDeleted };
  }
  return { store, failure: null, openDeleted };
}

/** How the return this tab has open differs in ``latest``, which another tab saved. */
export function openReturnChange(
  tab: ReturnsStore,
  latest: ReturnsStore,
): "changed" | "deleted" | null {
  const open = currentReturn(tab);
  if (!open) return null;
  const stored = latest.returns.find((kept) => kept.id === open.id);
  if (!stored) return "deleted";
  return stored.updated_at === open.updated_at && stored.submitted_at === open.submitted_at
    ? null
    : "changed";
}

export function currentReturn(store: ReturnsStore): SavedReturn | undefined {
  return store.returns.find((saved) => saved.id === store.currentId);
}

/**
 * Change the current return's answers. With no current return, the answers start a new one,
 * so opening the task list and leaving creates nothing.
 */
export function updateCurrent(
  store: ReturnsStore,
  change: (draft: Draft) => Draft,
  now: string,
  newId: string,
): ReturnsStore {
  const current = currentReturn(store);
  if (!current) return addReturn(store, change({}), now, newId, { open: true });
  return {
    ...store,
    returns: store.returns.map((saved) =>
      saved === current ? { ...saved, draft: change(saved.draft), updated_at: now } : saved,
    ),
  };
}

export function addReturn(
  store: ReturnsStore,
  draft: Draft,
  now: string,
  id: string,
  { open }: { open: boolean },
): ReturnsStore {
  const saved: SavedReturn = { id, created_at: now, updated_at: now, draft };
  return { currentId: open ? id : store.currentId, returns: [...store.returns, saved] };
}

/** Put imported answers in place of a saved return's, which is then no longer submitted. */
export function replaceReturn(
  store: ReturnsStore,
  id: string,
  draft: Draft,
  now: string,
): ReturnsStore {
  return {
    ...store,
    returns: store.returns.map((saved) =>
      saved.id === id ? { id, created_at: saved.created_at, updated_at: now, draft } : saved,
    ),
  };
}

export function deleteReturn(store: ReturnsStore, id: string): ReturnsStore {
  return {
    currentId: store.currentId === id ? null : store.currentId,
    returns: store.returns.filter((saved) => saved.id !== id),
  };
}

/** Mark the current return submitted and stop showing it, so the next answers start anew. */
export function markSubmitted(store: ReturnsStore, now: string): ReturnsStore {
  return {
    currentId: null,
    returns: store.returns.map((saved) =>
      saved.id === store.currentId ? { ...saved, submitted_at: now, updated_at: now } : saved,
    ),
  };
}

/** How a saved return is named: "Company name — period". */
export function returnLabel(draft: Draft): string {
  const name = draft.company?.name.trim() || "Company name not entered";
  const period = savedPeriod(draft);
  const dates = period
    ? `${formatDate(period.start)} to ${formatDate(period.end)}`
    : "period not entered";
  return `${name} — ${dates}`;
}

export type ReturnStatus = "in-progress" | "ready" | "submitted";

export const STATUS_LABELS: Record<ReturnStatus, string> = {
  "in-progress": "In progress",
  ready: "Ready to check",
  submitted: "Submitted",
};

/** ``pages`` are HMRC's page definitions, needed to tell if chosen pages are complete. */
export function returnStatus(saved: SavedReturn, pages?: SchemaPage[]): ReturnStatus {
  if (saved.submitted_at !== undefined) return "submitted";
  return toReturn(saved.draft, pages) === null ? "in-progress" : "ready";
}

function registrationNumber(draft: Draft): string {
  return (draft.company?.registration_number ?? "").replace(/\s/g, "").toUpperCase();
}

/** A saved return for the same company and accounting period as ``draft``, if there is one. */
export function findSameReturn(returns: SavedReturn[], draft: Draft): SavedReturn | undefined {
  const number = registrationNumber(draft);
  const period = savedPeriod(draft);
  if (!number || !period) return undefined;
  return returns.findLast((saved) => {
    const other = savedPeriod(saved.draft);
    return (
      registrationNumber(saved.draft) === number &&
      other?.start === period.start &&
      other.end === period.end
    );
  });
}
