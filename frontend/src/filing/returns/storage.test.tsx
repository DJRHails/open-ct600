/**
 * The saved returns when the browser's storage misbehaves: other tabs changing it, writes that
 * fail, and data this site cannot read.
 */
import { act, screen, within } from "@testing-library/react";
import type { UserEvent } from "@testing-library/user-event";
import { afterEach, vi } from "vitest";

import type { Draft } from "@/filing/model";
import {
  LEGACY_DRAFT_KEY,
  RETURNS_KEY,
  type SavedReturn,
  STORAGE_VERSION,
} from "@/filing/returns/savedReturns";
import { openDraft, renderApp } from "@/test-utils";

const COMPANY = {
  name: "Acme Widgets Ltd",
  registration_number: "01234567",
  utr: "1234567890",
  company_type: "0",
  principal_activity: "Manufacture of widgets",
};

const ACME: Draft = { company: COMPANY };
const BETA: Draft = { company: { ...COMPANY, name: "Beta Gadgets Ltd" } };

function saved(id: string, draft: Draft): SavedReturn {
  return {
    id,
    created_at: "2026-09-01T09:00:00.000Z",
    updated_at: "2026-09-01T09:00:00.000Z",
    draft,
  };
}

/** Write the returns as another tab would, without this tab hearing of it. */
function writeFromAnotherTab(currentId: string | null, returns: SavedReturn[]) {
  const store = { version: STORAGE_VERSION, currentId, returns };
  window.localStorage.setItem(RETURNS_KEY, JSON.stringify(store));
}

/** The ``storage`` event the browser fires in this tab when another tab writes. */
function announceFromAnotherTab() {
  act(() => {
    window.dispatchEvent(new StorageEvent("storage", { key: RETURNS_KEY }));
  });
}

function storedIds(): string[] {
  const stored = JSON.parse(window.localStorage.getItem(RETURNS_KEY) ?? "null");
  return stored.returns.map((kept: SavedReturn) => kept.id);
}

async function saveAccountingPeriod(user: UserEvent) {
  const dates = [
    ["Start date", "1", "4", "2025"],
    ["End date", "31", "3", "2026"],
  ] as const;
  for (const [legend, day, month, year] of dates) {
    const group = screen.getByRole("group", { name: legend });
    await user.type(within(group).getByLabelText("Day"), day);
    await user.type(within(group).getByLabelText("Month"), month);
    await user.type(within(group).getByLabelText("Year"), year);
  }
  await user.click(screen.getByRole("button", { name: "Save and continue" }));
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("returns open in two tabs", () => {
  it("keeps a return another tab added when this tab saves an answer", async () => {
    writeFromAnotherTab("a", [saved("a", ACME)]);
    const user = renderApp("/file/accounting-period");

    writeFromAnotherTab("new-in-other-tab", [saved("a", ACME), saved("new-in-other-tab", BETA)]);
    await saveAccountingPeriod(user);

    expect(storedIds()).toEqual(["a", "new-in-other-tab"]);
    expect(openDraft()).toMatchObject({ company: COMPANY, period: { end: { year: "2026" } } });
  });

  it("shows returns another tab added", async () => {
    writeFromAnotherTab("a", [saved("a", ACME)]);
    renderApp("/file/returns");
    expect(await screen.findByRole("heading", { name: /^Acme Widgets Ltd/ })).toBeVisible();

    writeFromAnotherTab("a", [saved("a", ACME), saved("b", BETA)]);
    announceFromAnotherTab();

    expect(screen.getByRole("heading", { name: /^Beta Gadgets Ltd/ })).toBeVisible();
  });

  it("says when the open return was changed in another tab", () => {
    writeFromAnotherTab("a", [saved("a", ACME)]);
    renderApp("/file/tasks");

    const changed = { ...saved("a", BETA), updated_at: "2026-09-02T09:00:00.000Z" };
    writeFromAnotherTab("a", [changed]);
    announceFromAnotherTab();

    expect(screen.getByRole("region", { name: "Important" })).toHaveTextContent(
      "This return was changed in another tab",
    );
  });

  it("says when the open return was deleted in another tab, and never brings it back", async () => {
    writeFromAnotherTab("a", [saved("a", ACME), saved("b", BETA)]);
    const user = renderApp("/file/accounting-period");

    writeFromAnotherTab(null, [saved("b", BETA)]);
    announceFromAnotherTab();

    expect(screen.getByRole("region", { name: "Important" })).toHaveTextContent(
      "The return you had open was deleted in another tab",
    );
    await saveAccountingPeriod(user);
    expect(storedIds()).toHaveLength(2);
    expect(storedIds()).toContain("b");
    expect(storedIds()).not.toContain("a");
  });
});

describe("storage that cannot be written", () => {
  it("keeps the page and says the answer was not saved", async () => {
    writeFromAnotherTab("a", [saved("a", ACME)]);
    const user = renderApp("/file/accounting-period");
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new DOMException("The quota has been exceeded.", "QuotaExceededError");
    });

    await saveAccountingPeriod(user);

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("Your answers could not be saved");
    expect(alert).toHaveTextContent(/Export this return to keep a copy/);
    expect(within(alert).getByRole("link", { name: /Export this return/ })).toHaveAttribute(
      "href",
      "/file/returns",
    );
    expect(screen.getByRole("heading", { level: 1 })).toBeVisible();
  });

  it("explains when this browser does not let the site use its storage", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new DOMException("The operation is insecure.", "SecurityError");
    });

    renderApp("/file/tasks");

    expect(
      screen.getByRole("heading", { name: "Your saved returns cannot be opened" }),
    ).toBeVisible();
    expect(screen.getByText(/This browser is not letting Open CT600 save/)).toBeVisible();
    expect(screen.queryByRole("button", { name: "Delete the saved data" })).toBeNull();
  });
});

describe("a draft from an earlier version that cannot be read", () => {
  it("does not block the saved returns, and deletes only that draft", async () => {
    writeFromAnotherTab("a", [saved("a", ACME), saved("b", BETA)]);
    window.localStorage.setItem(LEGACY_DRAFT_KEY, "{damaged");
    const user = renderApp("/file/returns");

    expect(await screen.findByRole("heading", { name: /^Acme Widgets Ltd/ })).toBeVisible();
    const banner = screen.getByRole("region", { name: "Important" });
    expect(banner).toHaveTextContent("A return saved by an earlier version cannot be read");
    expect(within(banner).getByRole("button", { name: "Download it" })).toBeVisible();

    await user.click(within(banner).getByRole("button", { name: "Delete it" }));
    await user.click(screen.getByRole("button", { name: "Yes, delete the unreadable return" }));

    expect(window.localStorage.getItem(LEGACY_DRAFT_KEY)).toBeNull();
    expect(storedIds()).toEqual(["a", "b"]);
    expect(screen.queryByText(/cannot be read/)).toBeNull();
  });
});

describe("saved returns this site cannot read", () => {
  it("deletes only the unreadable data, keeping a readable draft from an earlier version", async () => {
    window.localStorage.setItem(RETURNS_KEY, "{damaged");
    window.localStorage.setItem(LEGACY_DRAFT_KEY, JSON.stringify(ACME));
    const user = renderApp("/file/returns");

    await user.click(screen.getByRole("button", { name: "Delete the saved data" }));
    await user.click(screen.getByRole("button", { name: "Yes, delete the saved data" }));

    expect(await screen.findByRole("heading", { name: /^Acme Widgets Ltd/ })).toBeVisible();
    expect(storedIds()).toHaveLength(1);
  });
});
