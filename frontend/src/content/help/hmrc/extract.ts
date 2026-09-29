/**
 * Extract HMRC's box-by-box guidance from copies of its gov.uk guides (``specs/hmrc/guidance``,
 * saved as markdown from the gov.uk content API) so each box can quote HMRC's own words.
 *
 * A guide gives each box a heading that starts with its box ids, like "145 Total turnover from
 * trade", "30 and 35 Period of the return", "F20A to F20C and F25A to F25C Chartering-in limit"
 * or "Boxes 330 to 425". Box ids are checked against the boxes in HMRC's schema, so a heading
 * that only starts with a number is not taken for a box. Some boxes are tables whose columns
 * have headings of their own, "A Name of controlled foreign company" under "B5 Controlled
 * foreign company table", which the schema numbers B5A.
 *
 * This module has no imports, so ``scripts/extract-hmrc-guidance.ts`` can run it with Node.
 */

export type GuidanceBlock =
  | { type: "paragraph"; text: string }
  | { type: "list"; items: string[] }
  | { type: "heading"; text: string };

export type GuidanceEntry = {
  /** The form the guide is for, like "CT600" or "CT600A". */
  form: string;
  /** The boxes the heading names, like ["30", "35"]; a table column's box, like "B5A". */
  boxes: string[];
  /** The heading as HMRC wrote it, like "A15 Total". */
  heading: string;
  /** The heading of the part of the guide the box is in, like "Part 1: loans or arrangements made". */
  context: string | null;
  /**
   * The heading's id on the gov.uk page, so a link can go straight to it; ``null`` when it
   * cannot be known from the text (``headingId``).
   */
  anchor: string | null;
  blocks: GuidanceBlock[];
};

/** A saved gov.uk guide: its file name without ".md" (the page's slug), and where it is from. */
export type GuidanceSource = {
  guide: string;
  /** The form whose boxes it explains, like "CT600A"; ``null`` for other guides. */
  form: string | null;
  title: string;
  url: string;
  updated: string;
  /** Who publishes it: HM Revenue and Customs unless the file's "Publisher:" line says. */
  publisher: string;
};

export type Guidance = { sources: GuidanceSource[]; entries: GuidanceEntry[] };

/** One guide's boxes, and any box-like heading ids the schema does not have. */
export type ExtractedGuide = { entries: GuidanceEntry[]; unknown: string[] };

/** A box id: an optional page letter, a number, an optional ".1" and up to two letters. */
const BOX_ID = String.raw`[A-P]?\d{1,3}(?:\.\d)?[A-Za-z]{0,2}`;
const BOX_LIST_ITEM = String.raw`${BOX_ID}(?:\s+to\s+${BOX_ID})?`;
/** A list of box ids and ranges joined by commas and "and", then the title. */
const BOX_HEADING = new RegExp(
  String.raw`^(?:Boxes\s+)?(?<list>${BOX_LIST_ITEM}(?:(?:\s*,\s*|\s+and\s+|\s*,\s+and\s+)${BOX_LIST_ITEM})*)(?:\s+(?<title>.*))?$`,
);
/** A table column heading: a single capital letter and its title, like "A Previously activated". */
const COLUMN_HEADING = /^(?<letter>[A-J])\s+\S/;
/** A second box named in a heading's title: "585 Ring fence ... included and 590 Ring fence". */
const EMBEDDED_BOX = /\band\s+(?<box>\d{3})\s/g;
const PARTS = /^(?<page>[A-P]?)(?<number>\d{1,3})(?<rest>(?:\.\d)?[A-Za-z]{0,2})$/;

/**
 * The id kramdown (which renders gov.uk's govspeak) gives a heading: everything before the first
 * letter dropped, then only letters, digits, spaces and hyphens kept, spaces as hyphens,
 * lower case, and "-1", "-2" and so on added to repeats.
 *
 * A dash can reach kramdown as "—" (dropped) or as "&mdash;" (kept as "mdash"), and the copy
 * of the guide does not say which, so a heading with one has no id we can rely on: ``null``.
 */
export function headingId(text: string, used: Map<string, number>): string | null {
  const base =
    text
      .replace(/^[^a-zA-Z]+/, "")
      .replace(/[^a-zA-Z0-9 -]/g, "")
      .replace(/ /g, "-")
      .toLowerCase() || "section";
  const seen = used.get(base);
  used.set(base, seen === undefined ? 0 : seen + 1);
  if (text.includes("—")) return null;
  return seen === undefined ? base : `${base}-${seen + 1}`;
}

/** Every id a guide's headings may name: each schema box, each part of "C105/C110", and its base. */
export function boxCandidates(boxes: Iterable<string>): Set<string> {
  const candidates = new Set<string>();
  for (const box of boxes) {
    for (const part of box.split("/")) {
      candidates.add(part);
      const parts = PARTS.exec(part)?.groups;
      if (parts) candidates.add(`${parts.page}${parts.number}`);
    }
  }
  return candidates;
}

function splitId(id: string) {
  const parts = PARTS.exec(id)?.groups;
  if (!parts) return null;
  return { page: parts.page ?? "", number: Number(parts.number), rest: parts.rest ?? "" };
}

/** The candidate boxes from ``from`` to ``to``: "F15A to F15C", "I5 to I15" or "E50 to E190". */
function expandRange(from: string, to: string, candidates: Set<string>): string[] {
  const start = splitId(from);
  const end = splitId(to);
  if (!start || !end || start.page !== end.page) return [];
  const inRange = [...candidates].filter((candidate) => {
    const id = splitId(candidate);
    if (!id || id.page !== start.page) return false;
    if (start.number === end.number) {
      return id.number === start.number && id.rest >= start.rest && id.rest <= end.rest;
    }
    return id.number >= start.number && id.number <= end.number && id.rest === start.rest;
  });
  return inRange.sort((a, b) => compareIds(a, b));
}

function compareIds(a: string, b: string): number {
  const left = splitId(a);
  const right = splitId(b);
  if (!left || !right) return a.localeCompare(b);
  return left.number - right.number || left.rest.localeCompare(right.rest);
}

/**
 * The boxes a heading names, or ``null`` if it does not start with box ids of ``form``: a
 * supplementary page's ids start with its letter, the main return's are plain numbers.
 */
export function headingBoxes(
  heading: string,
  pageLetter: string,
  candidates: Set<string>,
): { boxes: string[]; unknown: string[] } | null {
  const match = BOX_HEADING.exec(heading.trim());
  const list = match?.groups?.list;
  if (!list) return null;
  const boxes: string[] = [];
  const unknown: string[] = [];
  for (const item of list.split(/\s*,\s+and\s+|\s*,\s*|\s+and\s+/)) {
    const [from = "", to] = item.split(/\s+to\s+/);
    if (!from.startsWith(pageLetter) || /^[A-P]/.test(from) !== pageLetter.length > 0) return null;
    if (to !== undefined) boxes.push(...expandRange(from, to, candidates));
    else if (candidates.has(from)) boxes.push(from);
    else unknown.push(from);
  }
  if (pageLetter === "") {
    for (const embedded of (match.groups?.title ?? "").matchAll(EMBEDDED_BOX)) {
      const box = embedded.groups?.box;
      if (box && candidates.has(box)) boxes.push(box);
    }
  }
  return boxes.length > 0 || unknown.length > 0 ? { boxes, unknown } : null;
}

type Heading = { level: number; text: string };

function asHeading(line: string): Heading | null {
  const match = /^(?<hashes>#{2,6})\s(?<text>.*)$/.exec(line);
  if (!match?.groups) return null;
  return { level: match.groups.hashes?.length ?? 0, text: (match.groups.text ?? "").trim() };
}

/** Paragraphs and lists from a box's lines. A line of spaces separates list items. */
function toBlocks(lines: string[]): GuidanceBlock[] {
  const blocks: GuidanceBlock[] = [];
  let paragraph: string[] = [];
  const endParagraph = () => {
    if (paragraph.length > 0) blocks.push({ type: "paragraph", text: tidy(paragraph.join(" ")) });
    paragraph = [];
  };
  for (const line of lines) {
    const heading = asHeading(line);
    if (heading) {
      endParagraph();
      blocks.push({ type: "heading", text: tidy(heading.text) });
    } else if (line.startsWith("- ")) {
      endParagraph();
      const last = blocks.at(-1);
      const item = tidy(line.slice(2));
      if (last?.type === "list") last.items.push(item);
      else blocks.push({ type: "list", items: [item] });
    } else if (line.trim() === "") {
      endParagraph();
    } else {
      paragraph.push(line.trim());
    }
  }
  endParagraph();
  return mergeLists(blocks);
}

/** A list interrupted only by blank lines is one list. */
function mergeLists(blocks: GuidanceBlock[]): GuidanceBlock[] {
  const merged: GuidanceBlock[] = [];
  for (const block of blocks) {
    const last = merged.at(-1);
    if (block.type === "list" && last?.type === "list") last.items.push(...block.items);
    else merged.push(block);
  }
  return merged;
}

function tidy(text: string): string {
  return text.replace(/\s+/g, " ").trim();
}

const HMRC = "HM Revenue and Customs";

/** A saved guide's header: its title, then "Source:", "Updated:" and optional "Publisher:". */
export function readHeader(markdown: string, guide: string, form: string | null): GuidanceSource {
  const lines = markdown.split("\n");
  const title = (lines[0] ?? "").replace(/^#\s+/, "").trim();
  const field = (name: string) =>
    lines
      .find((line) => line.startsWith(`${name}: `))
      ?.slice(name.length + 2)
      .trim() ?? "";
  const url = field("Source");
  if (!title || !url.startsWith("https://www.gov.uk/")) {
    throw new Error(`The guide ${guide} has no title or gov.uk Source line`);
  }
  return {
    guide,
    form,
    title,
    url,
    updated: field("Updated"),
    publisher: field("Publisher") || HMRC,
  };
}

/** The box being read: its entry, heading level and lines so far. */
type OpenBox = { entry: GuidanceEntry; level: number; lines: string[] };

/** A box whose columns may follow as headings of their own. */
type Table = { box: string; heading: string; level: number };

/** What the reader knows at a heading: where it is in the guide and the box it is reading. */
type ReadState = {
  open: OpenBox | null;
  table: Table | null;
  /** The last heading that is not a box's, like "Part 1: loans or arrangements made". */
  context: string | null;
  /** Headings with no text of their own, by level, which label the boxes after them. */
  labels: Map<number, string>;
};

/**
 * Extract each box's guidance from one guide. ``form`` is "CT600" or a page's name like
 * "CT600A"; ``candidates`` are the box ids its headings may name (``boxCandidates``).
 */
export function extractGuide(
  markdown: string,
  form: string,
  candidates: Set<string>,
): ExtractedGuide {
  const lines = markdown.split("\n");
  const pageLetter = form.replace(/^CT600/, "");
  const entries: GuidanceEntry[] = [];
  const unknown: string[] = [];
  const used = new Map<string, number>();
  const state: ReadState = { open: null, table: null, context: null, labels: new Map() };

  const close = () => {
    if (state.open && state.open.entry.boxes.length > 0) {
      entries.push({ ...state.open.entry, blocks: toBlocks(state.open.lines) });
    }
    state.open = null;
  };
  const open = (entry: Omit<GuidanceEntry, "form" | "blocks">, level: number) => {
    close();
    state.open = { entry: { form, ...entry, blocks: [] }, level, lines: [] };
  };

  const body = lines.slice(lines.findIndex((line) => asHeading(line) !== null));
  for (const [index, line] of body.entries()) {
    const heading = asHeading(line);
    if (!heading) {
      state.open?.lines.push(line);
      continue;
    }
    const anchor = headingId(heading.text, used);
    const column = columnBox(heading, state.table, candidates);
    if (column && state.table) {
      const level = Math.max(heading.level, state.table.level + 1);
      const { heading: tableHeading } = state.table;
      open({ boxes: [column], heading: heading.text, context: tableHeading, anchor }, level);
      continue;
    }
    const named = headingBoxes(heading.text, pageLetter, candidates);
    if (named) {
      unknown.push(...named.unknown);
      const context = contextFor(heading, state);
      const boxes = [...new Set(named.boxes)];
      open({ boxes, heading: heading.text, context, anchor }, heading.level);
      const [only] = boxes;
      state.table =
        boxes.length === 1 && only
          ? { box: only, heading: heading.text, level: heading.level }
          : null;
      continue;
    }
    if (state.open && heading.level > state.open.level) {
      state.open.lines.push(line);
      continue;
    }
    close();
    state.table = null;
    readSectionHeading(heading, asHeading(nextText(body, index) ?? "") !== null, state);
  }
  close();
  return { entries, unknown };
}

/**
 * A heading that is not a box's starts a new part of the guide, unless it is a label: a
 * heading with no text of its own, like "Period covered by this supplementary page", which
 * names the boxes after it.
 */
function readSectionHeading(heading: Heading, isLabel: boolean, state: ReadState) {
  for (const level of [...state.labels.keys()]) {
    if (level >= heading.level) state.labels.delete(level);
  }
  if (isLabel) state.labels.set(heading.level, heading.text);
  if (!isLabel || heading.level === 2) state.context = heading.text;
}

/**
 * What a box heading is under: a label one level up ("Turnover" over "145 Total turnover from
 * trade"), a label at its own level for a box with no title of its own ("Period covered by
 * this supplementary page" over "A3"), or else the part of the guide it is in.
 */
function contextFor(heading: Heading, state: ReadState): string | null {
  const untitled = BOX_HEADING.exec(heading.text)?.groups?.title === undefined;
  const sameLevel = untitled ? state.labels.get(heading.level) : undefined;
  return sameLevel ?? state.labels.get(heading.level - 1) ?? state.context;
}

function nextText(lines: string[], index: number): string | undefined {
  return lines.slice(index + 1).find((line) => line.trim() !== "");
}

function columnBox(heading: Heading, table: Table | null, candidates: Set<string>) {
  const letter = COLUMN_HEADING.exec(heading.text)?.groups?.letter;
  if (!letter || !table || heading.level <= 2) return null;
  const box = `${table.box}${letter}`;
  return candidates.has(box) ? box : null;
}

/** The guides in ``specs/hmrc/guidance`` that explain a form's boxes, by their slug. */
export const BOX_GUIDES: { form: string; guide: string }[] = [
  { form: "CT600", guide: "the-company-tax-return-guide" },
  ...[
    "a-2015-version-3-close-company-loans-and-arrangements-to-confer-benefits-on-participators",
    "b-controlled-foreign-companies-and-foreign-permanent-establishment-exemptions-hybrid-and-other-mismatches",
    "c-group-and-consortium-relief",
    "d-insurance",
    "e-charities-and-community-amateur-sports-clubs",
    "f-tonnage-tax",
    "h-cross-border-royalties",
    "i-supplementary-charge-in-respect-of-ring-fence-trades",
    "j-disclosure-of-tax-avoidance-schemes",
    "k-restitution-tax",
    "l-research-and-development",
    "m-freeports-and-investment-zones",
    "n-residential-property-developer-tax",
  ].map((rest) => ({
    form: `CT600${rest.charAt(0).toUpperCase()}`,
    guide: `supplementary-pages-ct600${rest}`,
  })),
  { form: "CT600P", guide: "completing-the-ct600p-page-for-creative-industries-reliefs" },
];

type SchemaNode = { box?: string | null; children?: SchemaNode[] };

/** Every box id in HMRC's schema spec (``backend/src/open_ct600/schema/ct600-v1.994.json``). */
export function schemaBoxes(root: SchemaNode): string[] {
  const boxes: string[] = [];
  const walk = (node: SchemaNode) => {
    if (node.box) boxes.push(node.box);
    for (const child of node.children ?? []) walk(child);
  };
  walk(root);
  return boxes;
}

/**
 * The guidance in the saved guides, given as markdown by slug: every guide's source, and each
 * box's guidance from the guides in ``BOX_GUIDES``. Box-like heading ids the schema does not
 * have are returned, to be checked by hand.
 */
export function extractGuidance(
  guides: Record<string, string>,
  boxes: Iterable<string>,
): { guidance: Guidance; unknown: string[] } {
  const candidates = boxCandidates(boxes);
  const formOf = new Map(BOX_GUIDES.map(({ form, guide }) => [guide, form]));
  const missing = BOX_GUIDES.filter(({ guide }) => guides[guide] === undefined);
  if (missing.length > 0) {
    throw new Error(`Missing guides: ${missing.map(({ guide }) => guide).join(", ")}`);
  }
  const slugs = Object.keys(guides).sort();
  const sources = slugs.map((guide) =>
    readHeader(guides[guide] ?? "", guide, formOf.get(guide) ?? null),
  );
  const extracted = BOX_GUIDES.map(({ form, guide }) => ({
    form,
    ...extractGuide(guides[guide] ?? "", form, candidates),
  }));
  return {
    guidance: { sources, entries: extracted.flatMap((guide) => guide.entries) },
    unknown: extracted.flatMap(({ form, unknown }) => unknown.map((box) => `${form} ${box}`)),
  };
}
