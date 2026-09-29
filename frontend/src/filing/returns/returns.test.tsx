import { screen, within } from "@testing-library/react";
import type { UserEvent } from "@testing-library/user-event";
import { afterEach, vi } from "vitest";

import type { Draft } from "@/filing/model";
import { FILE_FORMAT, FILE_VERSION } from "@/filing/returns/returnFile";
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

const YEAR_TO_MARCH_2025 = {
  start: { day: "1", month: "4", year: "2024" },
  end: { day: "31", month: "3", year: "2025" },
};

const ACME: Draft = { company: COMPANY, period: YEAR_TO_MARCH_2025 };
const ACME_LABEL = "Acme Widgets Ltd — 1 April 2024 to 31 March 2025";

const BETA: Draft = {
  company: { ...COMPANY, name: "Beta Gadgets Ltd", registration_number: "SC123456" },
  period: YEAR_TO_MARCH_2025,
};
const BETA_LABEL = "Beta Gadgets Ltd — 1 April 2024 to 31 March 2025";

function saved(id: string, draft: Draft, updatedAt: string): SavedReturn {
  return { id, created_at: "2026-09-01T09:00:00.000Z", updated_at: updatedAt, draft };
}

/** Acme, open on the filing pages and saved last, and Beta. */
function seedTwoReturns() {
  const returns = [
    saved("acme", ACME, "2026-09-02T09:00:00.000Z"),
    saved("beta", BETA, "2026-09-01T09:00:00.000Z"),
  ];
  const store = { version: STORAGE_VERSION, currentId: "acme", returns };
  window.localStorage.setItem(RETURNS_KEY, JSON.stringify(store));
}

function storedReturns(): SavedReturn[] {
  return JSON.parse(window.localStorage.getItem(RETURNS_KEY) ?? "{}").returns;
}

function returnFile(draft: unknown, changes: object = {}): string {
  const envelope = {
    format: FILE_FORMAT,
    version: FILE_VERSION,
    exported_at: "2026-09-29T09:00:00.000Z",
    app_version: "0.1.0",
    draft,
  };
  return JSON.stringify({ ...envelope, ...changes });
}

async function importFile(user: UserEvent, file: File) {
  await user.upload(screen.getByLabelText("Upload a file"), file);
  await user.click(screen.getByRole("button", { name: "Import return" }));
}

function jsonFile(text: string, name = "ct600-beta-gadgets-ltd-2025-03-31.json"): File {
  return new File([text], name, { type: "application/json" });
}

afterEach(() => {
  vi.restoreAllMocks();
});

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

describe("your returns", () => {
  it("lists every saved return, most recently saved first, and switches between them", async () => {
    seedTwoReturns();
    const user = renderApp("/file/returns");

    expect(document.title).toBe("Your returns – Open CT600");
    const cards = within(screen.getByRole("main"))
      .getAllByRole("heading", { level: 2 })
      .map((heading) => heading.textContent);
    expect(cards).toEqual([ACME_LABEL, BETA_LABEL]);
    expect(screen.getAllByText("In progress")).toHaveLength(2);
    const menu = screen.getByRole("navigation", { name: "Menu" });
    expect(within(menu).getByRole("link", { name: "Your returns" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(within(menu).getByRole("link", { name: "File a return" })).not.toHaveAttribute(
      "aria-current",
    );

    await user.click(screen.getByRole("link", { name: `Continue ${BETA_LABEL}` }));

    expect(screen.getByRole("heading", { level: 1, name: "Company Tax Return" })).toBeVisible();
    expect(screen.getByText("Beta Gadgets Ltd", { selector: ".govuk-caption-l" })).toBeVisible();
    expect(openDraft()).toEqual(BETA);
  });

  it("starts a new return alongside the others", async () => {
    seedTwoReturns();
    const user = renderApp("/file/returns");

    await user.click(screen.getByRole("button", { name: "Start a new return" }));
    expect(screen.getByText("Your company", { selector: ".govuk-caption-l" })).toBeVisible();
    expect(screen.getByText("You have completed 0 of 8 sections.")).toBeVisible();
    expect(storedReturns()).toHaveLength(2);

    await user.click(screen.getByRole("link", { name: "Accounting period" }));
    for (const [legend, year] of [
      ["Start date", "2025"],
      ["End date", "2026"],
    ] as const) {
      const group = screen.getByRole("group", { name: legend });
      await user.type(within(group).getByLabelText("Day"), legend === "Start date" ? "1" : "31");
      await user.type(within(group).getByLabelText("Month"), legend === "Start date" ? "4" : "3");
      await user.type(within(group).getByLabelText("Year"), year);
    }
    await user.click(screen.getByRole("button", { name: "Save and continue" }));

    expect(storedReturns()).toHaveLength(3);
    expect(openDraft()).toEqual({
      period: {
        start: { day: "1", month: "4", year: "2025" },
        end: { day: "31", month: "3", year: "2026" },
      },
    });
  });

  it("deletes a return only after the user confirms", async () => {
    seedTwoReturns();
    const user = renderApp("/file/returns");

    await user.click(screen.getByRole("link", { name: `Delete ${BETA_LABEL}` }));
    expect(document.title).toBe("Are you sure you want to delete this return? – Open CT600");
    expect(screen.getByText(BETA_LABEL)).toBeVisible();
    await user.click(screen.getByRole("link", { name: "No, keep it" }));
    expect(storedReturns()).toHaveLength(2);

    await user.click(screen.getByRole("link", { name: `Delete ${BETA_LABEL}` }));
    await user.click(screen.getByRole("button", { name: "Yes, delete this return" }));

    expect(screen.getByRole("alert")).toHaveTextContent(`You deleted the return for ${BETA_LABEL}`);
    expect(screen.queryByRole("heading", { name: BETA_LABEL })).toBeNull();
    expect(storedReturns().map((kept) => kept.id)).toEqual(["acme"]);
    expect(openDraft()).toEqual(ACME);
  });

  it("goes back to your returns from the delete page of a return that is not saved", () => {
    seedTwoReturns();
    renderApp("/file/returns/unknown/delete");

    expect(screen.getByRole("heading", { level: 1, name: "Your returns" })).toBeVisible();
  });

  it("says when there are no returns and links to them from the start page", async () => {
    const user = renderApp("/file");
    await user.click(screen.getByRole("link", { name: "Import it from Your returns" }));

    expect(screen.getByText("You have no returns saved in this browser.")).toBeVisible();
  });

  it("counts the saved returns on the start page", () => {
    seedTwoReturns();
    renderApp("/file");

    expect(screen.getByText(/You have 2 returns saved in this browser/)).toBeVisible();
    expect(screen.getByRole("link", { name: "Go to your returns" })).toHaveAttribute(
      "href",
      "/file/returns",
    );
  });
});

describe("deleting answers on the task list", () => {
  it("deletes only the open return and says the others remain", async () => {
    seedTwoReturns();
    const user = renderApp("/file/tasks");

    await user.click(screen.getByRole("button", { name: "Delete your answers" }));

    expect(
      screen.getByText(/Your answers have been deleted. You still have 1 return saved./),
    ).toBeVisible();
    expect(storedReturns().map((kept) => kept.id)).toEqual(["beta"]);
    await user.click(screen.getByRole("link", { name: "Go to your returns" }));
    expect(screen.getByRole("heading", { name: BETA_LABEL })).toBeVisible();
  });
});

describe("exporting a return", () => {
  it("downloads the answers in a versioned file named after the company and period", async () => {
    const files = captureDownloads();
    seedTwoReturns();
    const user = renderApp("/file/returns");

    await user.click(screen.getByRole("button", { name: `Export ${ACME_LABEL}` }));

    expect(files.map((file) => file.filename)).toEqual(["ct600-acme-widgets-ltd-2025-03-31.json"]);
    expect(files[0]?.blob.type).toBe("application/json");
    const exported = JSON.parse((await files[0]?.blob.text()) ?? "");
    expect(exported).toEqual({
      format: "open-ct600-return",
      version: 1,
      exported_at: expect.stringMatching(/^\d{4}-\d{2}-\d{2}T/),
      app_version: "0.1.0",
      draft: ACME,
    });
    expect(screen.getByText(/An exported file contains the company’s tax details/)).toBeVisible();
  });
});

describe("importing a return", () => {
  it("adds the return in the file to the saved returns", async () => {
    window.localStorage.setItem(
      RETURNS_KEY,
      JSON.stringify({
        version: STORAGE_VERSION,
        currentId: "acme",
        returns: [saved("acme", ACME, "2026-09-02T09:00:00.000Z")],
      }),
    );
    const user = renderApp("/file/returns");

    await user.click(screen.getByRole("link", { name: "Import a return from a file" }));
    expect(screen.getByText(/The file contains the company’s tax details/)).toBeVisible();
    await importFile(user, jsonFile(returnFile(BETA)));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      `You imported the return for ${BETA_LABEL}`,
    );
    expect(screen.getByRole("heading", { name: BETA_LABEL })).toBeVisible();
    expect(storedReturns().map((kept) => kept.draft)).toEqual([ACME, BETA]);
    expect(openDraft()).toEqual(ACME);
  });

  it.each([
    ["no file is chosen", null, "Select a file to import"],
    [
      "the file is not JSON",
      jsonFile(returnFile(BETA), "return.txt"),
      "The selected file must be a JSON file",
    ],
    ["the file is empty", jsonFile(""), "The selected file is empty"],
    [
      "the file is not valid JSON",
      jsonFile('{"format": '),
      "The selected file is damaged and cannot be read. Export the return again",
    ],
    [
      "the file is another kind of JSON",
      jsonFile(JSON.stringify({ company: COMPANY })),
      "The selected file is not an Open CT600 return. Choose a file you exported from Your returns",
    ],
    [
      "the version is not a number",
      jsonFile(returnFile(BETA, { version: "1" })),
      "The selected file is not an Open CT600 return. Choose a file you exported from Your returns",
    ],
    [
      "the file is from a newer version",
      jsonFile(returnFile(BETA, { version: FILE_VERSION + 1 })),
      "The selected file was exported from a newer version of Open CT600 than this site runs. Import it on the site you exported it from",
    ],
    [
      "an answer has been changed",
      jsonFile(returnFile({ ...BETA, company: { ...COMPANY, utr: 1234567890 } })),
      "The selected file has been changed or is damaged, so it cannot be imported. The problem is in draft.company.utr",
    ],
    [
      "an answer is missing",
      jsonFile(returnFile({ period: { start: YEAR_TO_MARCH_2025.start } })),
      "The selected file has been changed or is damaged, so it cannot be imported. The problem is in draft.period.end",
    ],
    [
      "it has a part this site does not know",
      jsonFile(returnFile({ ...BETA, notes: "hello" })),
      "The selected file has been changed or is damaged, so it cannot be imported. The problem is in draft.notes",
    ],
    [
      "a supplementary page is unknown",
      jsonFile(returnFile({ chosen_pages: ["O"] })),
      "The selected file has been changed or is damaged, so it cannot be imported. The problem is in draft.chosen_pages.0",
    ],
  ])("shows an error when %s", async (_case, file, message) => {
    const user = renderApp("/file/returns/import");

    if (file) await user.upload(screen.getByLabelText("Upload a file"), file);
    await user.click(screen.getByRole("button", { name: "Import return" }));

    const summary = await screen.findByRole("alert");
    expect(within(summary).getByRole("link", { name: message })).toHaveAttribute(
      "href",
      "#return-file",
    );
    expect(screen.getByLabelText("Upload a file")).toHaveAccessibleDescription(
      expect.stringContaining(`Error: ${message}`),
    );
    expect(document.title).toBe("Error: Import a return from a file – Open CT600");
    expect(window.localStorage.getItem(RETURNS_KEY)).toBeNull();
  });

  it("refuses a file over 1MB", async () => {
    const user = renderApp("/file/returns/import");
    const padded = returnFile(BETA, { padding: "x".repeat(1_000_000) });

    await importFile(user, jsonFile(padded));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The selected file must be smaller than 1MB",
    );
  });

  it("asks before replacing a saved return for the same company and period", async () => {
    seedTwoReturns();
    const changed: Draft = { ...ACME, profit_and_loss: { turnover: "100000" } };
    const user = renderApp("/file/returns/import");

    await importFile(user, jsonFile(returnFile(changed)));
    expect(
      await screen.findByRole("heading", {
        level: 1,
        name: "You already have a return for this company and period",
      }),
    ).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Continue" }));
    expect(document.title).toBe(
      "Error: You already have a return for this company and period – Open CT600",
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Select yes to replace your saved return with the imported one",
    );

    await user.click(screen.getByLabelText("Yes, replace the saved return"));
    await user.click(screen.getByRole("button", { name: "Continue" }));

    expect(screen.getByRole("alert")).toHaveTextContent(
      `You replaced the return for ${ACME_LABEL}`,
    );
    expect(storedReturns().map((kept) => [kept.id, kept.draft])).toEqual([
      ["acme", changed],
      ["beta", BETA],
    ]);
  });

  it("keeps both returns if the user chooses not to replace", async () => {
    seedTwoReturns();
    const user = renderApp("/file/returns/import");

    await importFile(user, jsonFile(returnFile(ACME)));
    await user.click(await screen.findByLabelText("No, keep both returns"));
    await user.click(screen.getByRole("button", { name: "Continue" }));

    expect(screen.getAllByRole("heading", { name: ACME_LABEL })).toHaveLength(2);
    expect(storedReturns()).toHaveLength(3);
  });
});
