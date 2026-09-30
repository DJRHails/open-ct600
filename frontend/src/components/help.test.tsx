import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { BoxHelp, QuestionHelp } from "@/components/help";
import { Tabs } from "@/components/Tabs";
import { loadGuidance } from "@/content/help/hmrc/useGuidance";
import { TAX_ADJUSTMENTS_HELP } from "@/content/help/taxAdjustments";

// Loading HMRC's guidance the first time can take longer than a test waits under load.
beforeAll(() => loadGuidance());

const TABS = [
  { id: "first", label: "First", panel: <a href="#somewhere">A link in the first panel</a> },
  { id: "second", label: "Second", panel: <p>Second panel</p> },
  { id: "third", label: "Third", panel: <p>Third panel</p> },
];

function panel(id: string) {
  return document.getElementById(id) as HTMLElement;
}

describe("tabs", () => {
  it("follow GOV.UK Frontend's markup, with the first tab selected", () => {
    render(<Tabs title="Help" tabs={TABS} />);

    const [first, second] = screen.getAllByRole("tab");
    expect(screen.getByRole("tablist")).toHaveClass("govuk-tabs__list");
    expect(first).toHaveAttribute("aria-selected", "true");
    expect(first).toHaveAttribute("tabindex", "0");
    expect(second).toHaveAttribute("aria-selected", "false");
    expect(second).toHaveAttribute("tabindex", "-1");
    expect(second).toHaveAttribute("aria-controls", "second");
    expect(panel("first")).toHaveAttribute("role", "tabpanel");
    expect(panel("first")).toHaveAttribute("aria-labelledby", "tab_first");
    expect(panel("first")).not.toHaveClass("govuk-tabs__panel--hidden");
    expect(panel("second")).toHaveClass("govuk-tabs__panel--hidden");
  });

  it("show a tab's panel when it is clicked, without changing the address", async () => {
    const user = userEvent.setup();
    render(<Tabs title="Help" tabs={TABS} />);

    await user.click(screen.getByRole("tab", { name: "Third" }));

    expect(screen.getByRole("tab", { name: "Third" })).toHaveAttribute("aria-selected", "true");
    expect(panel("third")).not.toHaveClass("govuk-tabs__panel--hidden");
    expect(panel("first")).toHaveClass("govuk-tabs__panel--hidden");
    expect(window.location.hash).toBe("");
  });

  it("move between tabs with the arrow keys, stopping at each end", async () => {
    const user = userEvent.setup();
    render(<Tabs title="Help" tabs={TABS} />);
    const tab = (name: string) => screen.getByRole("tab", { name });

    await user.click(tab("First"));
    await user.keyboard("{ArrowLeft}");
    expect(tab("First")).toHaveFocus();

    await user.keyboard("{ArrowRight}");
    expect(tab("Second")).toHaveFocus();
    expect(tab("Second")).toHaveAttribute("aria-selected", "true");
    expect(panel("second")).not.toHaveClass("govuk-tabs__panel--hidden");

    await user.keyboard("{ArrowRight}{ArrowRight}");
    expect(tab("Third")).toHaveFocus();

    await user.keyboard("{ArrowLeft}");
    expect(tab("Second")).toHaveFocus();
    expect(tab("Third")).toHaveAttribute("aria-selected", "false");
  });

  it("leave the tab list with the tab key, from the selected tab to its panel", async () => {
    const user = userEvent.setup();
    render(<Tabs title="Help" tabs={TABS} />);

    await user.tab();
    expect(screen.getByRole("tab", { name: "First" })).toHaveFocus();
    await user.tab();
    expect(screen.getByRole("link", { name: "A link in the first panel" })).toHaveFocus();
  });

  it("are a list of links to every panel on small screens", () => {
    vi.mocked(window.matchMedia).mockImplementation((query) => {
      const list = new EventTarget() as MediaQueryList;
      return Object.assign(list, { matches: false, media: query, onchange: null });
    });
    render(<Tabs title="Help" tabs={TABS} />);

    expect(screen.queryByRole("tablist")).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Help" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Second" })).toHaveAttribute("href", "#second");
    for (const { id } of TABS) expect(panel(id)).not.toHaveClass("govuk-tabs__panel--hidden");
  });
});

describe("question help", () => {
  it("is built when it is opened", async () => {
    const user = userEvent.setup();
    render(<QuestionHelp id="capital" help={TAX_ADJUSTMENTS_HELP.capital_allowances} />);

    expect(screen.queryByRole("tab")).not.toBeInTheDocument();
    await user.click(screen.getByText("Help with capital allowances"));
    expect(screen.getAllByRole("tab")).toHaveLength(2);
  });

  it("explains the question in plain English, in a fixed order", async () => {
    const user = userEvent.setup();
    render(<QuestionHelp id="capital" help={TAX_ADJUSTMENTS_HELP.capital_allowances} />);

    await user.click(screen.getByText("Help with capital allowances"));
    const plain = within(panel("capital-plain"));
    expect(plain.getAllByRole("heading").map((heading) => heading.textContent)).toEqual([
      "What it means",
      "Example",
      "What it does not include",
      "What your answer changes",
    ]);
    expect(plain.getByText(/Annual Investment Allowance/)).toBeInTheDocument();
  });

  it("quotes HMRC's guidance for its boxes, linked to where it is on GOV.UK, with the licence", async () => {
    const user = userEvent.setup();
    render(<QuestionHelp id="capital" help={TAX_ADJUSTMENTS_HELP.capital_allowances} />);

    await user.click(screen.getByText("Help with capital allowances"));
    await user.click(await screen.findByRole("tab", { name: "HMRC's guidance" }));

    const official = within(panel("capital-official"));
    expect(
      await official.findByRole("heading", { name: "690 Annual investment allowance" }),
    ).toBeInTheDocument();
    expect(
      official.getByText(/Enter the amount of Annual Investment Allowance included/),
    ).toBeInTheDocument();
    const [source] = official.getAllByRole("link", { name: /Completing your Company Tax Return/ });
    expect(source).toHaveAttribute(
      "href",
      "https://www.gov.uk/guidance/the-company-tax-return-guide#annual-investment-allowance",
    );
    expect(
      official.getByText(/Contains public sector information licensed under the/),
    ).toBeInTheDocument();
    expect(
      official.getByRole("link", { name: /Open Government Licence v3.0/ }),
    ).toBeInTheDocument();
  });
});

describe("box help", () => {
  it("has plain English and HMRC's guidance for a box we have written about", async () => {
    const user = userEvent.setup();
    render(<BoxHelp id="loan-name" box="A10A" />);

    await user.click(await screen.findByText("Help with box A10"));
    expect(screen.getByRole("tab", { name: "In plain English" })).toBeInTheDocument();
    expect(
      await within(panel("loan-name-official")).findByRole("heading", {
        name: "A10 Outstanding loans and arrangements made",
      }),
    ).toBeInTheDocument();
  });

  it("shows HMRC's guidance for both boxes of a pair", async () => {
    const user = userEvent.setup();
    render(<BoxHelp id="dates" box="N15/N20" />);

    await user.click(await screen.findByText("HMRC's guidance for box N15/N20"));
    expect(await screen.findByRole("heading", { name: "N15 From" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "N20 To" })).toBeInTheDocument();
  });

  it("says when it only has HMRC's guidance", async () => {
    const user = userEvent.setup();
    render(<BoxHelp id="royalty" box="H5Ea" />);

    await user.click(await screen.findByText("HMRC's guidance for box H5Ea"));
    expect(screen.queryByRole("tab")).not.toBeInTheDocument();
    expect(screen.getByText(/We have not written a plain English explanation/)).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", { name: "H5A to H5H Details of payments made" }),
    ).toBeInTheDocument();
  });

  it("is left out for a box with no help", async () => {
    const { container } = render(<BoxHelp id="nothing" box="C95" />);

    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(container).toBeEmptyDOMElement();
  });
});
