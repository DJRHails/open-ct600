import { screen, waitFor } from "@testing-library/react";

import type { SpecNode } from "@/api";
import { boxHelpKey } from "@/components/help";
import type { Guidance } from "@/content/help/hmrc/extract";
import guidanceJson from "@/content/help/hmrc/guidance.json";
import { boxLookups, indexGuidance } from "@/content/help/hmrc/lookup";
import { loadGuidance } from "@/content/help/hmrc/useGuidance";
import { PAGE_BOX_HELP } from "@/content/help/pages";
import { asked, pageScreens, withComputed } from "@/filing/supplementary/spec";
import { schemaPages } from "@/test-schema";
import { renderApp, seedDraft, stubApi } from "@/test-utils";

const INDEX = indexGuidance(guidanceJson as Guidance);
const PAGES = schemaPages()
  .filter((page) => !page.dormant)
  .map(withComputed);
const SCREENS = PAGES.flatMap((page) =>
  pageScreens(page).map((pageScreen) => [page.code, pageScreen.id] as const),
);

function askedBoxes(node: SpecNode): string[] {
  const own = node.box && asked(node) ? [node.box] : [];
  return [...own, ...node.children.filter(asked).flatMap(askedBoxes)];
}

// Loading HMRC's guidance the first time can take longer than a test waits under load.
beforeAll(() => loadGuidance());

describe("help on supplementary pages", () => {
  it.each(SCREENS)(
    "on %s screen %s is there for every box HMRC or we explain",
    async (code, id) => {
      stubApi((path) =>
        path === "/schema/pages"
          ? { status: 200, body: schemaPages() }
          : { status: 404, body: { detail: "Not Found" } },
      );
      seedDraft({ chosen_pages: [code] });
      renderApp(`/file/supplementary-pages/${code}/${id}`);
      await screen.findByRole("button", { name: "Save and continue" });

      const boxes = screen
        .queryAllByText(/^Box \S+$/)
        .map((hint) => (hint.textContent ?? "").replace(/^Box /, ""));
      const keys = [...new Set(boxes.map((box) => boxHelpKey(box, INDEX)))].filter(
        (key): key is string => key !== null,
      );
      await waitFor(() => {
        const summaries = [...document.querySelectorAll(".govuk-details__summary-text")].map(
          (summary) => summary.textContent ?? "",
        );
        for (const key of keys)
          expect(summaries).toContainEqual(expect.stringMatching(`box ${key}$`));
      });
    },
  );

  it("explains every box asked on CT600A, CT600C and CT600L in plain English", () => {
    for (const code of ["A", "C", "L"]) {
      const page = PAGES.find((candidate) => candidate.code === code);
      const missing = askedBoxes(page?.node as SpecNode).filter(
        (box) => !boxLookups(box).some((id) => PAGE_BOX_HELP[id]),
      );
      expect(missing, `CT600${code}`).toEqual([]);
    }
  });

  it("only explains boxes that are asked", () => {
    const boxes = PAGES.filter((page) => ["A", "C", "L"].includes(page.code)).flatMap((page) =>
      askedBoxes(page.node).flatMap(boxLookups),
    );
    const unknown = Object.keys(PAGE_BOX_HELP).filter((key) => !boxes.includes(key));
    expect(unknown).toEqual([]);
  });
});
