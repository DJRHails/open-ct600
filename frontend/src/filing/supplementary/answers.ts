/**
 * A supplementary page's answers as typed, and how they become the element tree the API takes.
 *
 * The draft keeps what the user typed (a *raw tree*): strings as entered, dates as their day,
 * month and year, and each choice's selected branch. ``convertPage`` checks it against the spec,
 * mirroring the service's own checks (``open_ct600.schema.trees``), and produces the element
 * tree: element names as keys, lists for repeating elements and every value a string.
 */
import type { ElementTree, JsonValue, SchemaPage, SpecNode } from "@/api";
import type { DateParts } from "@/components/forms";
import {
  type Branch,
  choiceKey,
  formItems,
  type FormItem,
  itemPaths,
  pageSpec,
  phrase,
  repeats,
  type Screen,
  sentence,
  startsWith,
  type TreePath,
} from "@/filing/supplementary/spec";
import { parseDateParts } from "@/format";

/** Dates are kept as ``DateParts``, which are ``RawTree``s with a day, month and year. */
export type RawValue = string | RawTree | RawValue[];
export type RawTree = { [key: string]: RawValue };

/** Something to correct, at ``path``; ``context`` names the list item, like "loan 2". */
export type Problem = { path: TreePath; message: string; context: string | null; node: SpecNode };

export type Conversion<T> = { value: T | undefined; problems: Problem[] };

export function isRecord(value: RawValue | undefined): value is RawTree {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function getAt(tree: RawValue | undefined, path: TreePath): RawValue | undefined {
  let current = tree;
  for (const segment of path) {
    if (Array.isArray(current) && typeof segment === "number") current = current[segment];
    else if (isRecord(current)) current = current[String(segment)];
    else return undefined;
  }
  return current;
}

/** A copy of ``tree`` with ``value`` at ``path``, creating groups and lists on the way. */
export function setAt(tree: RawValue | undefined, path: TreePath, value: RawValue): RawValue {
  const [segment, ...rest] = path;
  if (segment === undefined) return value;
  if (typeof segment === "number") {
    const list = Array.isArray(tree) ? [...tree] : [];
    while (list.length < segment) list.push({});
    list[segment] = setAt(list[segment], rest, value);
    return list;
  }
  const record = isRecord(tree) ? tree : {};
  return { ...record, [segment]: setAt(record[segment], rest, value) };
}

/** Whether nothing has been entered: blank text, empty dates, and groups and lists of those. */
export function isBlank(value: RawValue | undefined): boolean {
  if (value === undefined) return true;
  if (typeof value === "string") return value.trim() === "";
  if (Array.isArray(value)) return value.every(isBlank);
  return Object.values(value).every(isBlank);
}

type Context = { label: string | null };

function problem(node: SpecNode, path: TreePath, message: string, context: Context): Problem {
  return { path, message, context: context.label, node };
}

function missing(node: SpecNode): string {
  if (node.kind === "yes" || node.kind === "yesno" || node.kind === "enum") {
    return `Select ${phrase(node.label)}`;
  }
  return `Enter ${phrase(node.label)}`;
}

/** Check a page's answers and build its element tree. */
export function convertPage(page: SchemaPage, raw: RawTree | undefined): Conversion<ElementTree> {
  const root = pageSpec(page);
  const converted = convertGroup(root, raw ?? {}, [], { label: null });
  const value = converted.value?.[page.node.name];
  const tree = typeof value === "object" && value !== null && !Array.isArray(value) ? value : {};
  return { value: tree, problems: converted.problems };
}

function convertGroup(
  node: SpecNode,
  raw: RawValue | undefined,
  path: TreePath,
  context: Context,
): Conversion<ElementTree> {
  const answers = isRecord(raw) ? raw : {};
  const tree: ElementTree = {};
  const problems: Problem[] = [];
  for (const item of formItems(node)) {
    const converted = convertItem(item, answers, path, context);
    Object.assign(tree, converted.value);
    problems.push(...converted.problems);
  }
  return { value: tree, problems };
}

function convertItem(
  item: FormItem,
  answers: RawTree,
  path: TreePath,
  context: Context,
): Conversion<ElementTree> {
  if (item.type === "choice") return convertChoice(item, answers, path, context);
  const { node } = item;
  const converted = convertOccurrences(node, answers[node.name], [...path, node.name], context);
  const value = converted.value === undefined ? {} : { [node.name]: converted.value };
  return { value, problems: converted.problems };
}

/** The value recorded when the user chooses none of an optional choice's branches. */
export const NO_BRANCH = "none";

/** The branch the user chose; for answers without a recorded choice, the one answered. */
export function chosenBranch(
  item: Extract<FormItem, { type: "choice" }>,
  answers: RawTree,
): Branch | undefined {
  const selected = answers[choiceKey(item.id)];
  if (selected !== undefined) return item.branches.find((branch) => branch.name === selected);
  return item.branches.find((branch) =>
    branch.members.some((member) => !isBlank(answers[member.name])),
  );
}

/** The problems with a page's answers that ``screen`` asks about. */
export function screenProblems(page: SchemaPage, screen: Screen, raw: RawTree): Problem[] {
  const prefixes = screen.items.flatMap((item) => itemPaths(item, screen.path));
  return convertPage(page, raw).problems.filter((found) =>
    prefixes.some((prefix) => startsWith(found.path, prefix)),
  );
}

/** The element tree for one group's answers, keeping only the answers that are valid. */
export function groupTree(node: SpecNode, raw: RawValue | undefined): ElementTree {
  return convertGroup(node, raw, [], { label: null }).value ?? {};
}

/** A branch that is a single tick box is answered by choosing it. */
export function answeredByChoosing(branch: Branch): boolean {
  return branch.members.length === 1 && branch.members[0]?.kind === "yes";
}

function convertChoice(
  item: Extract<FormItem, { type: "choice" }>,
  answers: RawTree,
  path: TreePath,
  context: Context,
): Conversion<ElementTree> {
  const branch = chosenBranch(item, answers);
  if (!branch) {
    if (item.min === 0) return { value: {}, problems: [] };
    const options = item.branches.map((option) => phrase(option.label)).join(" or ");
    const head = item.branches[0]?.members[0];
    if (!head) return { value: {}, problems: [] };
    const where = [...path, choiceKey(item.id)];
    return { value: {}, problems: [problem(head, where, `Select ${options}`, context)] };
  }
  const [only] = branch.members;
  if (answeredByChoosing(branch) && only) return { value: { [only.name]: "yes" }, problems: [] };
  const members = branch.members.map((node) => ({ type: "node", node }) as const);
  const converted = members.map((member) => convertItem(member, answers, path, context));
  return {
    value: Object.assign({}, ...converted.map((result) => result.value)) as ElementTree,
    problems: converted.flatMap((result) => result.problems),
  };
}

function convertOccurrences(
  node: SpecNode,
  raw: RawValue | undefined,
  path: TreePath,
  context: Context,
): Conversion<JsonValue> {
  if (repeats(node)) return convertList(node, raw, path, context);
  if (node.kind !== "group") return convertScalar(node, raw, path, context);
  if (isBlank(raw) && node.min === 0) return { value: undefined, problems: [] };
  return convertGroup(node, raw, path, context);
}

/** What one list item is called in error messages, like "loan 2". */
export function itemName(node: SpecNode, index: number): string {
  return `${phrase(node.label)} ${index + 1}`;
}

function convertList(
  node: SpecNode,
  raw: RawValue | undefined,
  path: TreePath,
  context: Context,
): Conversion<JsonValue> {
  const entries = Array.isArray(raw) ? raw : [];
  const values: JsonValue[] = [];
  const problems: Problem[] = [];
  entries.forEach((entry, index) => {
    if (isBlank(entry)) return;
    const itemContext = { label: itemName(node, index) };
    const converted =
      node.kind === "group"
        ? convertGroup(node, entry, [...path, index], itemContext)
        : convertScalar(node, entry, [...path, index], itemContext);
    if (converted.value !== undefined) values.push(converted.value);
    problems.push(...converted.problems);
  });
  const answered = entries.filter((entry) => !isBlank(entry)).length;
  const label = phrase(node.label);
  if (answered < node.min && node.kind !== "group") {
    for (let index = 0; index < node.min; index += 1) {
      if (!isBlank(entries[index])) continue;
      problems.push(problem(node, [...path, index], `Enter ${itemName(node, index)}`, context));
    }
  } else if (answered < node.min) {
    const message =
      node.min === 1 ? `Add at least one ${label}` : `Add at least ${node.min}: ${label}`;
    problems.push(problem(node, path, message, context));
  } else if (node.max !== null && answered > node.max) {
    problems.push(problem(node, path, `Add no more than ${node.max}: ${label}`, context));
  }
  return { value: answered === 0 ? undefined : values, problems };
}

function convertScalar(
  node: SpecNode,
  raw: RawValue | undefined,
  path: TreePath,
  context: Context,
): Conversion<string> {
  if (isBlank(raw)) {
    return node.min > 0
      ? { value: undefined, problems: [problem(node, path, missing(node), context)] }
      : { value: undefined, problems: [] };
  }
  const checked = checkScalar(node, raw);
  if (checked.ok) return { value: checked.value, problems: [] };
  return { value: undefined, problems: [problem(node, path, checked.error, context)] };
}

type Checked = { ok: true; value: string } | { ok: false; error: string };

const POUNDS = /^[0-9]+$/;
const MONEY = /^-?[0-9]+(?:\.[0-9]{1,2})?$/;
const INTEGER = /^-?[0-9]+$/;
const DECIMAL = /^-?[0-9]+(?:\.[0-9]+)?$/;
const PERCENT = /^[0-9]+(?:\.[0-9]{1,2})?$/;
const YEAR = /^[0-9]{4}$/;
/** An XSD pattern that only restricts which characters may be used, like ``[A-Z ]*``. */
const CHARACTER_CLASS = /^\[.*\][*+]$/;

function checkScalar(node: SpecNode, raw: RawValue | undefined): Checked {
  if (node.kind === "date") return checkDate(node, raw);
  if (typeof raw !== "string") return { ok: false, error: missing(node) };
  const text = raw.trim();
  const amount = text.replace(/[\s,]/g, "").replace(/^(-?)£/, "$1");
  const label = sentence(node.label);
  switch (node.kind) {
    case "pounds":
      if (amount.startsWith("-")) return { ok: false, error: `${label} cannot be negative` };
      if (!POUNDS.test(amount)) {
        return { ok: false, error: `${label} must be a whole number of pounds, like 1234` };
      }
      return checkBounds(node, amount, pounds);
    case "money":
      if (!MONEY.test(amount)) {
        return { ok: false, error: `${label} must be an amount in pounds and pence, like 1234.56` };
      }
      return checkBounds(node, amount, pounds);
    case "integer":
      if (!INTEGER.test(amount)) return { ok: false, error: `${label} must be a whole number` };
      return checkPatterns(node, amount) ?? checkBounds(node, amount, String);
    case "decimal":
      if (!DECIMAL.test(amount)) return { ok: false, error: `${label} must be a number` };
      return checkBounds(node, amount, String);
    case "percent": {
      const percent = amount.replace(/%$/, "");
      if (!PERCENT.test(percent)) {
        return { ok: false, error: `${label} must be a percentage, like 19 or 26.5` };
      }
      return checkBounds(node, percent, (bound) => `${bound}%`);
    }
    case "year":
      return YEAR.test(text)
        ? { ok: true, value: text }
        : { ok: false, error: `${label} must be a year, like 2025` };
    default:
      return checkChoiceOrText(node, text);
  }
}

function checkChoiceOrText(node: SpecNode, text: string): Checked {
  switch (node.kind) {
    case "yes":
      return text === "yes" ? { ok: true, value: text } : { ok: false, error: missing(node) };
    case "yesno":
      return text === "yes" || text === "no"
        ? { ok: true, value: text }
        : { ok: false, error: `Select yes or no for ${phrase(node.label)}` };
    case "enum":
      return (node.enum ?? []).some((option) => option.value === text)
        ? { ok: true, value: text }
        : { ok: false, error: `Select ${phrase(node.label)} from the list` };
    case "text":
      return checkLength(node, text) ?? checkPatterns(node, text) ?? { ok: true, value: text };
    default:
      return { ok: false, error: `${sentence(node.label)} cannot be answered in this service` };
  }
}

function checkDate(node: SpecNode, raw: RawValue | undefined): Checked {
  const parts = isDateParts(raw) ? raw : { day: "", month: "", year: "" };
  const parsed = parseDateParts(parts, phrase(node.label));
  if (!parsed.ok) return parsed;
  const label = sentence(node.label);
  const earliest = typeof node.minValue === "string" ? node.minValue : null;
  const latest = typeof node.maxValue === "string" ? node.maxValue : null;
  if (earliest && parsed.value < earliest) {
    return { ok: false, error: `${label} must be on or after ${longDate(earliest)}` };
  }
  if (latest && parsed.value > latest) {
    return { ok: false, error: `${label} must be on or before ${longDate(latest)}` };
  }
  return parsed;
}

export function isDateParts(value: RawValue | undefined): value is DateParts {
  return isRecord(value) && "day" in value && "month" in value && "year" in value;
}

function checkLength(node: SpecNode, text: string): Checked | null {
  const { minLength: shortest, maxLength: longest } = node;
  const tooShort = shortest !== null && text.length < shortest;
  const tooLong = longest !== null && text.length > longest;
  if (!tooShort && !tooLong) return null;
  const label = phrase(node.label);
  if (shortest !== null && longest !== null && shortest !== longest) {
    return { ok: false, error: `Enter ${label}, ${shortest} to ${longest} characters` };
  }
  if (shortest !== null && shortest === longest) {
    return { ok: false, error: `Enter ${label}, ${shortest} characters` };
  }
  if (longest !== null) {
    return { ok: false, error: `Enter ${label} in ${longest} characters or fewer` };
  }
  return { ok: false, error: `Enter ${label}, at least ${shortest} characters` };
}

const compiled = new Map<string, RegExp>();

/** An XSD pattern as a JavaScript regular expression; XSD patterns match the whole value. */
export function xsdPattern(pattern: string): RegExp {
  let regex = compiled.get(pattern);
  if (!regex) {
    regex = new RegExp(`^(?:${pattern})$`);
    compiled.set(pattern, regex);
  }
  return regex;
}

function checkPatterns(node: SpecNode, text: string): Checked | null {
  for (const pattern of node.patterns) {
    if (xsdPattern(pattern).test(text)) continue;
    const label = sentence(node.label);
    return CHARACTER_CLASS.test(pattern)
      ? { ok: false, error: `${label} contains a character that is not allowed` }
      : { ok: false, error: `${label} is not in the right format` };
  }
  return null;
}

function checkBounds(node: SpecNode, value: string, show: (bound: number) => string): Checked {
  const amount = Number(value);
  const label = sentence(node.label);
  if (typeof node.minValue === "number" && amount < node.minValue) {
    return { ok: false, error: `${label} must be ${show(node.minValue)} or more` };
  }
  if (typeof node.maxValue === "number" && amount > node.maxValue) {
    return { ok: false, error: `${label} must be ${show(node.maxValue)} or less` };
  }
  return { ok: true, value };
}

const POUNDS_FORMAT = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 2 });

function pounds(bound: number): string {
  return `£${POUNDS_FORMAT.format(bound)}`;
}

function longDate(iso: string): string {
  const [year, month, day] = iso.split("-").map(Number);
  const date = new Date(Date.UTC(year ?? 0, (month ?? 1) - 1, day ?? 1));
  return new Intl.DateTimeFormat("en-GB", { dateStyle: "long", timeZone: "UTC" }).format(date);
}
