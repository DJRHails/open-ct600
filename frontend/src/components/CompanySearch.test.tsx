import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import type { CompanySearchResult } from "@/api";
import { CompanySearch, escapeHtml } from "@/components/CompanySearch";

const ACME: CompanySearchResult = {
  number: "01234567",
  name: "ACME WIDGETS LTD",
  status: "active",
  address: "1 High Street, Leeds, LS1 1AA",
  incorporated_on: "2019-05-01",
};
const ACORN: CompanySearchResult = { ...ACME, number: "07654321", name: "ACORN <b>BAKERY</b> LTD" };

/**
 * Press a navigation key where the focus is. The autocomplete reads ``event.keyCode``, which
 * browsers set but jsdom's KeyboardEvent leaves at 0, so the key is sent with the code a browser
 * would give.
 */
const KEY_CODES = { ArrowDown: 40, ArrowUp: 38, Enter: 13, Escape: 27 } as const;

function press(key: keyof typeof KEY_CODES) {
  fireEvent.keyDown(document.activeElement ?? document.body, { key, keyCode: KEY_CODES[key] });
}

/** The autocomplete waits 1.4 seconds before announcing, so screen readers are not flooded. */
const ANNOUNCED = { timeout: 3000 };

/** What the live regions say: the autocomplete alternates between two to re-announce. */
function announced(): string {
  return screen
    .getAllByRole("status")
    .map((region) => region.textContent ?? "")
    .join(" ");
}

function renderSearch(search: (query: string) => Promise<CompanySearchResult[]>) {
  const onChoose = vi.fn<(company: CompanySearchResult) => void>();
  const onSearchError = vi.fn<(error: unknown) => void>();
  const user = userEvent.setup();
  render(
    <CompanySearch
      id="company-search"
      label="Company name or number"
      hint="For example, Acme Widgets Ltd or 01234567"
      search={search}
      onChoose={onChoose}
      onSearchError={onSearchError}
    />,
  );
  return { user, onChoose, onSearchError };
}

describe("the company search", () => {
  it("describes the combobox with its hint, so screen readers announce it", () => {
    renderSearch(async () => []);

    expect(
      screen.getByRole("combobox", { name: "Company name or number" }),
    ).toHaveAccessibleDescription(/^For example, Acme Widgets Ltd or 01234567\. When autocomplete/);
  });

  it("is a labelled combobox chosen from with the keyboard", async () => {
    const search = vi.fn<(query: string) => Promise<CompanySearchResult[]>>(async () => [
      ACME,
      ACORN,
    ]);
    const { user, onChoose } = renderSearch(search);

    const input = screen.getByRole("combobox", { name: "Company name or number" });
    await user.type(input, "ac");
    expect(await screen.findByRole("option", { name: "Searching…" })).toBeInTheDocument();
    await screen.findByRole("option", { name: /ACME WIDGETS LTD/ });
    const options = screen.getAllByRole("option");

    expect(options.map((option) => option.textContent)).toEqual([
      expect.stringContaining("ACME WIDGETS LTD (01234567)"),
      expect.stringContaining("ACORN <b>BAKERY</b> LTD (07654321)"),
    ]);
    expect(screen.queryByText("BAKERY", { selector: "b" })).toBeNull();
    await waitFor(() => expect(announced()).toMatch(/2 results are available/), ANNOUNCED);

    // The autocomplete re-renders with Preact, asynchronously, after each key.
    press("ArrowDown");
    const acme = screen.getByRole("option", { name: /ACME WIDGETS LTD/ });
    await waitFor(() => expect(acme).toHaveFocus());
    press("ArrowDown");
    await waitFor(() => expect(screen.getByRole("option", { name: /ACORN/ })).toHaveFocus());
    press("ArrowUp");
    await waitFor(() => expect(acme).toHaveFocus());
    press("Enter");

    await waitFor(() => expect(onChoose).toHaveBeenCalledWith(ACME));
    await waitFor(() => expect(input).toHaveValue("ACME WIDGETS LTD"));
  });

  it("waits for a pause in typing and searches once", async () => {
    const search = vi.fn<(query: string) => Promise<CompanySearchResult[]>>(async () => [ACME]);
    const { user } = renderSearch(search);

    await user.type(screen.getByRole("combobox"), "acme");
    await screen.findByRole("option", { name: /ACME WIDGETS LTD/ });

    expect(search.mock.calls.map(([query]) => query)).toEqual(["acme"]);
  });

  it("does not search until 2 characters are typed", async () => {
    const search = vi.fn<(query: string) => Promise<CompanySearchResult[]>>(async () => [ACME]);
    const { user } = renderSearch(search);

    await user.type(screen.getByRole("combobox"), "a");

    await waitFor(
      () => expect(announced()).toContain("Type 2 or more characters to search"),
      ANNOUNCED,
    );
    expect(search).not.toHaveBeenCalled();
  });

  it("reports a failed search and shows no results", async () => {
    const failure = new Error("Companies House is not available");
    const search = vi.fn<(query: string) => Promise<CompanySearchResult[]>>(async () => {
      throw failure;
    });
    const { user, onSearchError } = renderSearch(search);

    await user.type(screen.getByRole("combobox"), "acme");

    await waitFor(() => expect(onSearchError).toHaveBeenCalledWith(failure));
    expect(await screen.findByRole("option", { name: "No companies found" })).toBeInTheDocument();
  });
});

describe("escapeHtml", () => {
  it("escapes the characters HTML gives meaning to", () => {
    expect(escapeHtml(`<a href="x">Tom & Jerry's</a>`)).toBe(
      "&lt;a href=&quot;x&quot;&gt;Tom &amp; Jerry&#39;s&lt;/a&gt;",
    );
  });
});
