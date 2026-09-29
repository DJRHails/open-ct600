import { screen } from "@testing-library/react";
import { vi } from "vitest";

import { LEGACY_DRAFT_KEY, RETURNS_KEY, STORAGE_VERSION } from "@/filing/returns/savedReturns";
import { renderApp } from "@/test-utils";

const COMPANY = {
  name: "Acme Widgets Ltd",
  registration_number: "01234567",
  utr: "1234567890",
  company_type: "0",
  principal_activity: "Manufacture of widgets",
};

/** Capture files the page saves: ``saveFile`` clicks a link to a Blob URL. */
function captureDownloads() {
  const files: { blob: Blob; filename: string }[] = [];
  const blobs = new Map<string, Blob>();
  vi.stubGlobal(
    "URL",
    class extends URL {
      static override createObjectURL(blob: Blob) {
        const url = `blob:test/${blobs.size}`;
        blobs.set(url, blob);
        return url;
      }
      static override revokeObjectURL() {}
    },
  );
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function click(
    this: HTMLAnchorElement,
  ) {
    const blob = blobs.get(this.href);
    if (blob) files.push({ blob, filename: this.download });
  });
  return files;
}

describe("returns saved by an earlier version", () => {
  it("opens the single saved draft on the task list", () => {
    window.localStorage.setItem(LEGACY_DRAFT_KEY, JSON.stringify({ company: COMPANY }));

    renderApp("/file/tasks");

    expect(screen.getByText("Acme Widgets Ltd", { selector: ".govuk-caption-l" })).toBeVisible();
    expect(window.localStorage.getItem(LEGACY_DRAFT_KEY)).toBeNull();
    expect(JSON.parse(window.localStorage.getItem(RETURNS_KEY) ?? "{}").returns).toHaveLength(1);
  });
});

describe("saved returns this site cannot read", () => {
  const newer = JSON.stringify({ version: STORAGE_VERSION + 1, returns: "a newer shape" });

  it("explains, keeps the data and offers it as a download", async () => {
    const files = captureDownloads();
    window.localStorage.setItem(RETURNS_KEY, newer);
    const user = renderApp("/file/tasks");

    expect(
      screen.getByRole("heading", { level: 1, name: "Your saved returns cannot be opened" }),
    ).toBeVisible();
    expect(screen.getByText(/saved data is version 3/)).toBeVisible();
    expect(document.title).toBe("Your saved returns cannot be opened – Open CT600");

    await user.click(screen.getByRole("button", { name: "Download the saved data" }));

    expect(files).toHaveLength(1);
    expect(files[0]?.filename).toBe("open-ct600-saved-data.json");
    expect(await files[0]?.blob.text()).toBe(newer);
    expect(window.localStorage.getItem(RETURNS_KEY)).toBe(newer);
  });

  it("deletes the data only once the user confirms, then starts again", async () => {
    window.localStorage.setItem(RETURNS_KEY, "{damaged");
    const user = renderApp("/file/tasks");
    expect(
      screen.getByText(/data saved in this browser is damaged: it is not valid JSON/),
    ).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Delete the saved data" }));
    expect(window.localStorage.getItem(RETURNS_KEY)).toBe("{damaged");
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    await user.click(screen.getByRole("button", { name: "Delete the saved data" }));
    await user.click(screen.getByRole("button", { name: "Yes, delete the saved data" }));

    expect(window.localStorage.getItem(RETURNS_KEY)).toBeNull();
    expect(screen.getByRole("heading", { level: 1, name: "Company Tax Return" })).toBeVisible();
  });
});
