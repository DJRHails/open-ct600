import { screen, within } from "@testing-library/react";
import type { UserEvent } from "@testing-library/user-event";

import { TAX_ADJUSTMENTS } from "@/filing/model";
import { openDraft, renderApp, seedDraft } from "@/test-utils";

const PAGE = "/file/tax-adjustments";

function question(name: RegExp) {
  return screen.getByRole("group", { name });
}

async function answer(user: UserEvent, name: RegExp, choice: "Yes" | "No") {
  await user.click(within(question(name)).getByRole("radio", { name: choice }));
}

async function answerNoToEverything(user: UserEvent) {
  for (const no of screen.getAllByRole("radio", { name: "No" })) await user.click(no);
}

async function save(user: UserEvent) {
  await user.click(screen.getByRole("button", { name: "Save and continue" }));
}

describe("tax adjustments", () => {
  it("asks each adjustment as an everyday question first", () => {
    renderApp(PAGE);

    const questions = TAX_ADJUSTMENTS.fields.flatMap((field) => field.gate?.question ?? []);
    expect(questions).toHaveLength(7);
    for (const name of questions) {
      expect(screen.getByRole("group", { name })).toBeInTheDocument();
    }
    expect(question(/buy equipment, tools or vehicles/)).toBeInTheDocument();
    expect(question(/sell property, shares or other major assets/)).toBeInTheDocument();
    expect(question(/control other companies/)).toBeInTheDocument();
    expect(screen.queryByLabelText("Capital allowances the company is claiming")).toBeNull();
  });

  it("asks for the figure, with its precise name, when the answer is yes", async () => {
    const user = renderApp(PAGE);

    await answerNoToEverything(user);
    await answer(user, /buy equipment, tools or vehicles/, "Yes");
    const amount = screen.getByLabelText("Capital allowances the company is claiming");
    expect(amount).toHaveAccessibleDescription(/Annual Investment Allowance/);
    await user.type(amount, "20,400");
    await answer(user, /control other companies/, "Yes");
    await user.type(screen.getByLabelText("Number of associated companies"), "2");
    await save(user);

    expect(openDraft().tax_adjustments).toEqual({
      disallowable_expenses: "0",
      capital_allowances: "20,400",
      losses_brought_forward: "0",
      chargeable_gains: "0",
      qualifying_donations: "0",
      exempt_distributions: "0",
      associated_companies: "2",
    });
  });

  it("sets the figure to 0 when the answer is no, even if one was typed", async () => {
    const user = renderApp(PAGE);

    await answerNoToEverything(user);
    await answer(user, /sell property, shares/, "Yes");
    await user.type(screen.getByLabelText("Chargeable gains"), "35,000");
    await answer(user, /sell property, shares/, "No");
    await save(user);

    expect(openDraft().tax_adjustments).toMatchObject({ chargeable_gains: "0" });
  });

  it("says which questions are unanswered and which figures are missing", async () => {
    const user = renderApp(PAGE);

    await answer(user, /buy equipment, tools or vehicles/, "Yes");
    await save(user);

    const summary = within(screen.getByRole("alert"));
    expect(summary.getByRole("link", { name: "Enter the capital allowances" })).toHaveAttribute(
      "href",
      "#capital_allowances",
    );
    expect(
      summary.getByRole("link", {
        name: "Select yes if the company sold property, shares or other major assets",
      }),
    ).toHaveAttribute("href", "#chargeable_gains-answer");
    expect(summary.getAllByRole("link")).toHaveLength(7);
    expect(document.getElementById("chargeable_gains-answer")).toHaveAttribute("type", "radio");
  });

  it("remembers the answers from the saved figures", () => {
    seedDraft({ tax_adjustments: { capital_allowances: "5000", chargeable_gains: "0" } });
    renderApp(PAGE);

    const yes = within(question(/buy equipment, tools or vehicles/)).getByRole("radio", {
      name: "Yes",
    });
    expect(yes).toBeChecked();
    expect(screen.getByLabelText("Capital allowances the company is claiming")).toHaveValue("5000");
    expect(within(question(/sell property/)).getByRole("radio", { name: "No" })).toBeChecked();
    expect(within(question(/give money/)).getByRole("radio", { name: "No" })).toBeChecked();
  });

  it("has help with plain English and HMRC's guidance under every question", async () => {
    const user = renderApp(PAGE);
    const gated = TAX_ADJUSTMENTS.fields.filter((field) => field.gate);

    expect(screen.getAllByText(/^Help with /)).toHaveLength(gated.length);
    await user.click(screen.getByText("Help with associated companies"));
    const help = document.getElementById("associated_companies-help-plain") as HTMLElement;
    expect(within(help).getByRole("heading", { name: "Example" })).toBeInTheDocument();
    await user.click(
      screen.getAllByRole("tab", { name: "HMRC's guidance" })[gated.length - 1] as HTMLElement,
    );
    expect(
      await screen.findByRole("heading", {
        name: "326 Number of associated companies in this period",
      }),
    ).toBeInTheDocument();
  });
});
