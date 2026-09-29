import specText from "../../../../../backend/src/open_ct600/schema/ct600-v1.994.json?raw";

import { SAVED_GUIDES, words } from "@/content/help/guides.test-utils";
import {
  boxCandidates,
  extractGuidance,
  extractGuide,
  type GuidanceEntry,
  headingBoxes,
  headingId,
  schemaBoxes,
} from "@/content/help/hmrc/extract";
import committed from "@/content/help/hmrc/guidance.json";
import { boxLookups, indexGuidance } from "@/content/help/hmrc/lookup";

const SCHEMA_BOXES = schemaBoxes(JSON.parse(specText).root);
const CANDIDATES = boxCandidates(SCHEMA_BOXES);
const extracted = extractGuidance(SAVED_GUIDES, SCHEMA_BOXES);
const guidance = indexGuidance(extracted.guidance);

describe("heading ids", () => {
  it("match the ids gov.uk gives headings", () => {
    const used = new Map<string, number>();
    expect(headingId("1 Company name", used)).toBe("company-name");
    expect(headingId("30 and 35 Period of the return", used)).toBe("and-35-period-of-the-return");
    expect(headingId("Members’ club or voluntary association", used)).toBe(
      "members-club-or-voluntary-association",
    );
    expect(headingId("A3", used)).toBe("a3");
    expect(headingId("Example", used)).toBe("example");
    expect(headingId("Example", used)).toBe("example-1");
  });

  it("are unknown for headings with a dash, which gov.uk writes two ways", () => {
    expect(headingId("C45 Trading losses — total", new Map())).toBeNull();
  });
});

describe("box headings", () => {
  const boxes = (heading: string, page = "") => headingBoxes(heading, page, CANDIDATES)?.boxes;

  it("read one box, a list of boxes, and a second box named in the title", () => {
    expect(boxes("145 Total turnover from trade")).toEqual(["145"]);
    expect(boxes("80, 85 and 90 Accounts and computations")).toEqual(["80", "85", "90"]);
    expect(
      boxes(
        "585 Ring fence Corporation Tax included and 590 Ring fence supplementary charge included",
      ),
    ).toEqual(["585", "590"]);
  });

  it("expand ranges to the boxes the schema has", () => {
    expect(boxes("Boxes 330 to 425")).toEqual([
      "330",
      "335",
      "340",
      "345",
      "380",
      "385",
      "390",
      "395",
    ]);
    expect(boxes("F20A to F20C and F25A to F25C Chartering-in limit", "F")).toEqual([
      "F20A",
      "F20B",
      "F20C",
      "F25A",
      "F25B",
      "F25C",
    ]);
    expect(boxes("J5 to J50 Scheme reference number", "J")).toEqual(["J5"]);
  });

  it("are only a page's own boxes", () => {
    expect(headingBoxes("A15 Total", "", CANDIDATES)).toBeNull();
    expect(headingBoxes("145 Total", "A", CANDIDATES)).toBeNull();
    expect(headingBoxes("Transfer pricing", "", CANDIDATES)).toBeNull();
  });

  it("report box ids the schema does not have", () => {
    expect(headingBoxes("980 Date", "", CANDIDATES)).toEqual({ boxes: [], unknown: ["980"] });
  });
});

const GUIDE = `# Completing the CT600Z page
Source: https://www.gov.uk/guidance/example
Updated: 2026-01-01T00:00:00+00:00

## When to complete

Complete this page if it applies.

## Part 1: details

### Period covered by this supplementary page

### B10

Enter the start date.

### B5 Controlled foreign company table

Enter one row for each company.

#### A Name of controlled foreign company

Enter the full name.


- first point

- second point

##### Example

A worked example.

### Transfer pricing

Not a box.
`;

describe("extracting a guide", () => {
  const { entries } = extractGuide(GUIDE, "CT600B", CANDIDATES);
  const entry = (box: string) => entries.find((candidate) => candidate.boxes.includes(box));

  it("gives each box its heading, its part of the guide and its text", () => {
    expect(entry("B10")).toMatchObject({
      heading: "B10",
      context: "Period covered by this supplementary page",
      anchor: "b10",
      blocks: [{ type: "paragraph", text: "Enter the start date." }],
    });
    expect(entry("B5")).toMatchObject({
      context: "Part 1: details",
      blocks: [{ type: "paragraph", text: "Enter one row for each company." }],
    });
  });

  it("reads a table's columns as boxes of their own, with their lists and subheadings", () => {
    expect(entry("B5A")).toEqual<GuidanceEntry>({
      form: "CT600B",
      boxes: ["B5A"],
      heading: "A Name of controlled foreign company",
      context: "B5 Controlled foreign company table",
      anchor: "a-name-of-controlled-foreign-company",
      blocks: [
        { type: "paragraph", text: "Enter the full name." },
        { type: "list", items: ["first point", "second point"] },
        { type: "heading", text: "Example" },
        { type: "paragraph", text: "A worked example." },
      ],
    });
  });

  it("leaves out text that is not under a box", () => {
    const text = JSON.stringify(entries);
    expect(text).not.toContain("Not a box");
    expect(text).not.toContain("Complete this page if it applies");
  });
});

describe("the committed guidance", () => {
  it("is what the saved guides give (run pnpm guidance:extract if not)", () => {
    expect(committed).toEqual(extracted.guidance);
  });

  it("names every saved guide's source on gov.uk", () => {
    for (const source of extracted.guidance.sources) {
      expect(source.url).toMatch(/^https:\/\/www\.gov\.uk\//);
      expect(source.title).not.toBe("");
    }
  });

  it("only names boxes the schema does not have for page details the return fills in", () => {
    const unexpected = extracted.unknown.filter(
      (id) =>
        !/^CT600[A-P] [A-P][1-4]$/.test(id) &&
        !["CT600 980", "CT600D D5", "CT600E E35"].includes(id),
    );
    expect(unexpected).toEqual([]);
  });

  // Checked by hand against each box's section of the gov.uk guide.
  const SPOT_CHECKS: [box: string, heading: string, text: string][] = [
    ["1", "1 Company name", "Enter the registered name of the company."],
    [
      "3",
      "3 Tax reference",
      "It is the last 10 digits of the 13 digit number at the top of the document.",
    ],
    ["4", "4 Type of company", "Enter 0, if the company is in the first year of liquidation"],
    [
      "35",
      "30 and 35 Period of the return",
      "Enter the beginning date (box 30) and the end date (box 35)",
    ],
    ["145", "145 Total turnover from trade", "Enter the total trading turnover from any source."],
    [
      "160",
      "160 Trading losses brought forward set against trading profits",
      "only enter sufficient losses to cover the trading profit",
    ],
    ["305", "305 Qualifying donations", "Do not enter a figure greater than that in box 300."],
    [
      "326",
      "326 Number of associated companies in this period",
      "The figure should not include your company",
    ],
    ["385", "Boxes 330 to 425", "Enter the amount of profit chargeable at each rate of tax"],
    [
      "590",
      "585 Ring fence Corporation Tax included and 590 Ring fence supplementary charge included",
      "Do not complete box 585, 590 or form CT600I",
    ],
    [
      "620",
      "620 Franked investment income or exempt ABGH distributions",
      "Enter the amount of any exempt ABGH distributions",
    ],
    ["689", "688 and 689 Full expensing", "full expensing"],
    [
      "A5",
      "A5 Loans repaid, released or written off or return payments",
      "Put an X in this box if any or all loans made during the period have been repaid",
    ],
    [
      "A10B",
      "A10 Outstanding loans and arrangements made",
      "The figure you enter in column 2 of the table is the total of all debit entries",
    ],
    [
      "A15",
      "A15 Total",
      "loans or benefits conferred which are deemed to be outstanding by the operation of section 464C",
    ],
    [
      "A25",
      "A25 Relief for returned payments or amounts repaid, released or written off within 9 months",
      "The loan is fully repaid on 30 June 2021.",
    ],
    [
      "B5A",
      "A Name of controlled foreign company",
      "Enter the full name of the controlled foreign company.",
    ],
    ["C5C", "C5 Surrendering company details", "Enter the following for each surrender:"],
    ["C10", "C10 Total amount claimed", "Enter the total amount of group relief claimed."],
    ["F25B", "F20A to F20C and F25A to F25C Chartering-in limit", "Enter X in the relevant boxes."],
    [
      "H5Ea",
      "H5A to H5H Details of payments made",
      "Enter the relevant details for each recipient of the royalty.",
    ],
    [
      "I155C",
      "C Total activated",
      "Enter the totals of profit and tax entered in boxes I155 A and B",
    ],
    ["K15.1A", "K15 Columns A to D", ""],
    [
      "L71A",
      "L71A Total expenditure on externally provided workers from, and subcontracting to, connected persons",
      "Enter a figure that is equal to, or less than, the figure in box L10",
    ],
    ["P5A", "P5 Film", "include the combined total for all your company’s films"],
  ];

  it.each(SPOT_CHECKS)("gives box %s HMRC's guidance for it", (box, heading, text) => {
    const [first] = guidance.forBox(box);
    expect(first?.entry.heading).toBe(heading);
    expect(words(JSON.stringify(first?.entry.blocks))).toContain(words(text));
  });
});

describe("looking up a box", () => {
  it("tries the box, then each of a pair, then the box a column belongs to", () => {
    expect(boxLookups("A10A")).toEqual(["A10A", "A10"]);
    expect(boxLookups("688/689")).toEqual(["688/689", "688", "689"]);
    expect(boxLookups("K15.1A")).toEqual(["K15.1A", "K15.1", "K15"]);
    expect(boxLookups("L71A")).toEqual(["L71A", "L71"]);
    expect(boxLookups("145")).toEqual(["145"]);
  });

  it("prefers a box's own guidance to a range's", () => {
    const found = guidance.forBox("E95").map(({ entry }) => entry.heading);
    expect(found).toEqual(["E95 to E125 Type of expenditure", "E50 to E190"]);
  });

  it("finds nothing for a box HMRC's guide has no heading for", () => {
    expect(guidance.forBox("C25")).toEqual([]);
  });
});
