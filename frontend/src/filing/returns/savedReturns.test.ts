import type { Draft } from "@/filing/model";
import {
  addReturn,
  deleteReturn,
  EMPTY_STORE,
  findSameReturn,
  LEGACY_DRAFT_KEY,
  loadReturns,
  markSubmitted,
  returnLabel,
  RETURNS_KEY,
  returnStatus,
  STORAGE_VERSION,
  updateCurrent,
  writeReturns,
} from "@/filing/returns/savedReturns";

const MONDAY = "2026-09-28T09:00:00.000Z";
const TUESDAY = "2026-09-29T09:00:00.000Z";

const ACME: Draft = {
  company: {
    name: "Acme Widgets Ltd",
    registration_number: "01234567",
    utr: "1234567890",
    company_type: "0",
    principal_activity: "Manufacture of widgets",
  },
  period: {
    start: { day: "1", month: "4", year: "2024" },
    end: { day: "31", month: "3", year: "2025" },
  },
};

function stored() {
  return JSON.parse(window.localStorage.getItem(RETURNS_KEY) ?? "null");
}

describe("loading saved returns", () => {
  it("starts with no returns when nothing is saved, and writes nothing", () => {
    expect(loadReturns(window.localStorage, MONDAY, "new")).toEqual({
      ok: true,
      store: EMPTY_STORE,
    });
    expect(window.localStorage.length).toBe(0);
  });

  it("moves the single draft of earlier versions into the list and opens it", () => {
    window.localStorage.setItem(LEGACY_DRAFT_KEY, JSON.stringify(ACME));

    const loaded = loadReturns(window.localStorage, MONDAY, "migrated");

    const saved = { id: "migrated", created_at: MONDAY, updated_at: MONDAY, draft: ACME };
    expect(loaded).toEqual({ ok: true, store: { currentId: "migrated", returns: [saved] } });
    expect(stored()).toEqual({
      version: STORAGE_VERSION,
      currentId: "migrated",
      returns: [saved],
    });
    expect(window.localStorage.getItem(LEGACY_DRAFT_KEY)).toBeNull();
  });

  it("adds an old draft to returns already saved, keeping them", () => {
    const earlier = addReturn(EMPTY_STORE, { chosen_pages: [] }, MONDAY, "first", { open: false });
    writeReturns(window.localStorage, earlier);
    window.localStorage.setItem(LEGACY_DRAFT_KEY, JSON.stringify(ACME));

    const loaded = loadReturns(window.localStorage, TUESDAY, "second");

    expect(loaded.ok && loaded.store.returns.map((saved) => saved.id)).toEqual(["first", "second"]);
    expect(loaded.ok && loaded.store.currentId).toBe("second");
  });

  it("drops an old draft with no answers instead of listing an empty return", () => {
    window.localStorage.setItem(LEGACY_DRAFT_KEY, "{}");

    expect(loadReturns(window.localStorage, MONDAY, "new")).toEqual({
      ok: true,
      store: EMPTY_STORE,
    });
    expect(window.localStorage.getItem(LEGACY_DRAFT_KEY)).toBeNull();
  });

  it("keeps an old draft it cannot read, and says so", () => {
    window.localStorage.setItem(LEGACY_DRAFT_KEY, "{not json");

    const loaded = loadReturns(window.localStorage, MONDAY, "new");

    expect(loaded).toMatchObject({
      ok: false,
      problem: { kind: "unreadable", raw: "{not json" },
    });
    expect(window.localStorage.getItem(LEGACY_DRAFT_KEY)).toBe("{not json");
  });

  it("refuses returns saved by a newer version rather than discarding them", () => {
    const newer = JSON.stringify({ version: STORAGE_VERSION + 1, drafts: {} });
    window.localStorage.setItem(RETURNS_KEY, newer);

    expect(loadReturns(window.localStorage, MONDAY, "new")).toEqual({
      ok: false,
      problem: { kind: "newer-version", found: STORAGE_VERSION + 1, raw: newer },
    });
    expect(window.localStorage.getItem(RETURNS_KEY)).toBe(newer);
  });

  it.each([
    ["damaged JSON", "{", /not valid JSON/],
    ["no version", JSON.stringify({ returns: [] }), /no version number/],
    ["an older version", JSON.stringify({ version: 1 }), /never written/],
    [
      "a return without answers",
      JSON.stringify({ version: STORAGE_VERSION, currentId: null, returns: [{ id: "a" }] }),
      /not in the expected format/,
    ],
    [
      "an open return that is not saved",
      JSON.stringify({ version: STORAGE_VERSION, currentId: "gone", returns: [] }),
      /not saved/,
    ],
  ])("says why it cannot read saved data with %s", (_case, raw, reason) => {
    window.localStorage.setItem(RETURNS_KEY, raw);

    const loaded = loadReturns(window.localStorage, MONDAY, "new");

    expect(loaded).toMatchObject({ ok: false, problem: { kind: "unreadable", raw } });
    expect(!loaded.ok && loaded.problem.kind === "unreadable" && loaded.problem.reason).toMatch(
      reason,
    );
  });
});

describe("changing saved returns", () => {
  it("starts a return with the first answer saved, then changes that return", () => {
    const started = updateCurrent(EMPTY_STORE, () => ACME, MONDAY, "acme");
    expect(started).toEqual({
      currentId: "acme",
      returns: [{ id: "acme", created_at: MONDAY, updated_at: MONDAY, draft: ACME }],
    });

    const changed = updateCurrent(
      started,
      (draft) => ({ ...draft, chosen_pages: [] }),
      TUESDAY,
      "x",
    );
    expect(changed.returns).toEqual([
      {
        id: "acme",
        created_at: MONDAY,
        updated_at: TUESDAY,
        draft: { ...ACME, chosen_pages: [] },
      },
    ]);
  });

  it("closes a deleted return if it was open, and keeps the others", () => {
    const one = addReturn(EMPTY_STORE, ACME, MONDAY, "one", { open: false });
    const both = addReturn(one, {}, MONDAY, "two", { open: true });

    expect(deleteReturn(both, "two")).toEqual({ currentId: null, returns: one.returns });
    expect(deleteReturn(both, "one").currentId).toBe("two");
  });

  it("marks the open return submitted and closes it", () => {
    const open = addReturn(EMPTY_STORE, ACME, MONDAY, "acme", { open: true });

    const submitted = markSubmitted(open, TUESDAY);

    expect(submitted.currentId).toBeNull();
    expect(submitted.returns[0]).toMatchObject({ submitted_at: TUESDAY, updated_at: TUESDAY });
    expect(returnStatus(submitted.returns[0]!)).toBe("submitted");
    expect(returnStatus(open.returns[0]!)).toBe("in-progress");
  });
});

describe("describing saved returns", () => {
  it("names a return by its company and period", () => {
    expect(returnLabel(ACME)).toBe("Acme Widgets Ltd — 1 April 2024 to 31 March 2025");
    expect(returnLabel({})).toBe("Company name not entered — period not entered");
  });

  it("finds a saved return for the same company number and period", () => {
    const store = addReturn(EMPTY_STORE, ACME, MONDAY, "acme", { open: false });
    const company = { ...ACME.company!, registration_number: " 01234567 " };
    const laterPeriod = {
      start: { day: "1", month: "4", year: "2025" },
      end: { day: "31", month: "3", year: "2026" },
    };

    expect(findSameReturn(store.returns, { ...ACME, company })?.id).toBe("acme");
    expect(findSameReturn(store.returns, { ...ACME, period: laterPeriod })).toBeUndefined();
    expect(findSameReturn(store.returns, { company: ACME.company! })).toBeUndefined();
  });
});
