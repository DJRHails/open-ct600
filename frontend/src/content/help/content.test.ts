import { ACCOUNTS_HELP, COMPARATIVES_HELP } from "@/content/help/accounts";
import { BALANCE_SHEET_HELP } from "@/content/help/balanceSheet";
import { COMPANY_HELP } from "@/content/help/company";
import { SAVED_GUIDES, words } from "@/content/help/guides.test-utils";
import type { Guidance } from "@/content/help/hmrc/extract";
import guidanceJson from "@/content/help/hmrc/guidance.json";
import { indexGuidance } from "@/content/help/hmrc/lookup";
import { PAGE_BOX_HELP } from "@/content/help/pages";
import { PERIOD_HELP } from "@/content/help/period";
import { PROFIT_AND_LOSS_HELP } from "@/content/help/profitAndLoss";
import {
  CHOOSE_PAGES_HELP,
  CREATIVE_HELP,
  LOAN_DATE_HELP,
  RESEARCH_HELP,
  SURRENDERER_HELP,
} from "@/content/help/reliefs";
import { TAX_ADJUSTMENTS_HELP } from "@/content/help/taxAdjustments";
import type { PlainHelp, QuestionHelp } from "@/content/help/types";
import {
  BALANCE_SHEET,
  COMPANY_TYPES,
  EMPTY_ACCOUNTS,
  EMPTY_COMPANY,
  PROFIT_AND_LOSS,
  TAX_ADJUSTMENTS,
} from "@/filing/model";
import { EMPTY_RESEARCH } from "@/filing/reliefs";

const INDEX = indexGuidance(guidanceJson as Guidance);

const keys = (fields: readonly { key: string }[]) => fields.map((field) => field.key);

/** Every question in the main return, by section: its help, and the questions asked. */
const QUESTIONS: [section: string, help: Record<string, QuestionHelp>, asked: string[]][] = [
  ["company details", COMPANY_HELP, Object.keys(EMPTY_COMPANY)],
  ["accounting period", PERIOD_HELP, ["start", "end"]],
  ["profit and loss", PROFIT_AND_LOSS_HELP, keys(PROFIT_AND_LOSS.fields)],
  ["tax adjustments", TAX_ADJUSTMENTS_HELP, keys(TAX_ADJUSTMENTS.fields)],
  ["balance sheet", BALANCE_SHEET_HELP, keys(BALANCE_SHEET.fields)],
  ["accounts details", ACCOUNTS_HELP, Object.keys(EMPTY_ACCOUNTS)],
  ["research and development", RESEARCH_HELP, Object.keys(EMPTY_RESEARCH)],
  ["creative industries", CREATIVE_HELP, ["additional_information_submitted"]],
  [
    "surrendering companies",
    SURRENDERER_HELP,
    ["surrenderable_amount", "surrendered_to_others", "consortium_share"],
  ],
  ["loan dates", { loan_date: LOAN_DATE_HELP }, ["loan_date"]],
  ["supplementary pages", { pages: CHOOSE_PAGES_HELP }, ["pages"]],
  [
    "previous period",
    COMPARATIVES_HELP,
    ["previous_period", "tax_on_profit", "previous_employees"],
  ],
];

/** A box named in plain text: "box 160", "boxes 210 and 220", "boxes L185 and L190". */
const BOX_MENTION =
  /\b[Bb]ox(?:es)? (?<first>[A-P]?\d+[A-Z]?)(?: (?:and|or) (?<second>[A-P]?\d+[A-Z]?))?/g;

function mentionedBoxes(texts: string[]): string[] {
  return texts.flatMap((text) =>
    [...text.matchAll(BOX_MENTION)].flatMap((match) =>
      [match.groups?.first, match.groups?.second].filter((box): box is string => !!box),
    ),
  );
}

/** The boxes a question's HMRC tab explains: each box it cites and the others in its entries. */
function explainedBoxes(question: QuestionHelp): Set<string> {
  const cited = question.hmrc.flatMap((ref) => ("box" in ref ? [ref.box] : []));
  const entries = cited.flatMap((box) => INDEX.forBox(box).flatMap(({ entry }) => entry.boxes));
  return new Set([...cited, ...entries]);
}

const EVERY_HELP = QUESTIONS.flatMap(([section, help]) =>
  Object.entries(help).map(([key, question]) => [`${section}: ${key}`, question] as const),
);

function plainTexts(plain: PlainHelp): string[] {
  return [...plain.meaning, ...plain.example, ...plain.excludes, ...plain.effect];
}

/** GOV.UK style: no Latin abbreviations, exclamation marks or ampersands (except R&D). */
const OFF_STYLE = /\be\.g\.|\bi\.e\.|\betc\b|!|&(?!D\b)/;

describe("help content", () => {
  it.each(QUESTIONS)("covers every question in %s, and nothing else", (_, help, asked) => {
    expect(Object.keys(help).sort()).toEqual([...asked].sort());
  });

  it.each(EVERY_HELP)("for %s explains it in plain English in every part", (_, question) => {
    expect(question.topic).not.toBe("");
    for (const part of Object.values(question.plain)) {
      expect(part.length).toBeGreaterThan(0);
      for (const text of part) expect(text.trim()).not.toBe("");
    }
  });

  it.each(EVERY_HELP)("for %s has HMRC's guidance for each box it cites", (_, question) => {
    expect(question.hmrc.length).toBeGreaterThan(0);
    const boxes = question.hmrc.flatMap((ref) => ("box" in ref ? [ref.box] : []));
    expect(boxes.filter((box) => INDEX.forBox(box).length === 0)).toEqual([]);
  });

  it.each(EVERY_HELP)("for %s quotes saved guides word for word", (_, question) => {
    const quotes = question.hmrc.flatMap((ref) => ("quote" in ref ? [ref.quote] : []));
    for (const quote of quotes) {
      expect(Object.keys(SAVED_GUIDES)).toContain(quote.guide);
      const guide = SAVED_GUIDES[quote.guide] ?? "";
      const headings = guide
        .split("\n")
        .filter((line) => /^#{1,6}\s/.test(line))
        .map((line) => line.replace(/^#+\s+/, "").trim());
      expect(headings).toContain(quote.heading);
      const missing = quote.paragraphs.filter((text) => !words(guide).includes(words(text)));
      expect(missing).toEqual([]);
    }
  });

  it.each(EVERY_HELP)("for %s only names boxes its HMRC tab explains", (_, question) => {
    const explained = explainedBoxes(question);
    const unexplained = mentionedBoxes(plainTexts(question.plain)).filter(
      (box) => !explained.has(box),
    );
    expect(unexplained).toEqual([]);
  });

  it("takes indexation allowance up to December 2017 off chargeable gains", () => {
    const text = plainTexts(TAX_ADJUSTMENTS_HELP.chargeable_gains.plain).join(" ");
    expect(text).toMatch(/indexation allowance/);
    expect(text).toMatch(/December 2017/);
    expect(text).toMatch(/cannot create or increase a loss/);
  });

  it("gives HMRC's instruction for companies in liquidation: 0 in the first year, 3 after", () => {
    const liquidation = COMPANY_TYPES.find((type) => type.value === "3");
    expect(liquidation?.label).toBe("Company in liquidation, second or later year");
    expect(liquidation?.hint).toMatch(/In the first, choose none of these/);
    expect(liquidation?.hint).toMatch(/Pays the main rate on all profits/);

    const help = COMPANY_HELP.company_type;
    const effect = help.plain.effect.join(" ");
    expect(effect).toMatch(/companies in their second or later year of liquidation/);
    expect(effect).not.toMatch(/not a close company/);
    const quotes = help.hmrc.flatMap((ref) => ("quote" in ref ? [ref.quote] : []));
    expect(quotes).toContainEqual(
      expect.objectContaining({
        guide: "the-company-tax-return-guide",
        paragraphs: [
          "Enter 0, if the company is in the first year of liquidation, unless one of the other company types apply.",
          "Enter 3, if the company is in the second or later year of liquidation.",
        ],
      }),
    );
  });

  it("is written in GOV.UK style", () => {
    const texts = [
      ...EVERY_HELP.flatMap(([, question]) => [question.topic, ...plainTexts(question.plain)]),
      ...Object.values(PAGE_BOX_HELP).flatMap(plainTexts),
    ];
    expect(texts.filter((text) => OFF_STYLE.test(text))).toEqual([]);
  });
});
