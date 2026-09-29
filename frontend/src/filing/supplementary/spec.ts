/**
 * How a supplementary page's schema spec becomes questions: which elements are asked, how
 * choices are grouped, and how a page is split into screens.
 *
 * Answers are addressed by a *tree path*: element names and list indexes from the page's root
 * element, like ``["LoansByCloseCompanies", "LoansInformation", "Loan", 0, "Name"]``. A choice's
 * selected branch is stored under the key ``choiceKey(id)`` of the group that holds it.
 */
import type { PageCode, SchemaPage, SpecNode } from "@/api";

export type TreePath = (string | number)[];

/** One branch of a choice: the elements that are answered when the branch is chosen. */
export type Branch = { name: string; label: string; members: SpecNode[] };

/** A question on a form: one element (scalar, group or list), or a choice between branches. */
export type FormItem =
  | { type: "node"; node: SpecNode }
  | { type: "choice"; id: string; min: number; branches: Branch[] };

/** One screen of a page: the items asked at ``path`` (the group that holds them). */
export type Screen = { id: string; title: string; path: TreePath; items: FormItem[] };

export function repeats(node: SpecNode): boolean {
  return node.max === null || node.max > 1;
}

/** Elements the service works out are shown on check your answers, never asked. */
export function asked(node: SpecNode): boolean {
  return node.computed !== true;
}

/** The key under which a group's answers record the branch chosen for a choice. */
export function choiceKey(id: string): string {
  return `?${id}`;
}

/** A group's children as form items, in schema order, with each choice's members together. */
export function formItems(node: SpecNode): FormItem[] {
  const items: FormItem[] = [];
  const choices = new Map<string, Extract<FormItem, { type: "choice" }>>();
  for (const child of node.children.filter(asked)) {
    if (child.choice === null) {
      items.push({ type: "node", node: child });
      continue;
    }
    let choice = choices.get(child.choice);
    if (!choice) {
      const min = node.choices.find((group) => group.id === child.choice)?.min ?? 1;
      choice = { type: "choice", id: child.choice, min, branches: [] };
      choices.set(child.choice, choice);
      items.push(choice);
    }
    const branchName = child.branch ?? child.name;
    const branch = choice.branches.find((candidate) => candidate.name === branchName);
    if (branch) branch.members.push(child);
    else choice.branches.push({ name: branchName, label: child.label, members: [child] });
  }
  return items;
}

/** The path of an item in the group at ``path``: its element, or its choice key. */
export function itemPath(item: FormItem, path: TreePath): TreePath {
  return item.type === "node" ? [...path, item.node.name] : [...path, choiceKey(item.id)];
}

/** Every path an item's answers can live under (a choice's key and each member). */
export function itemPaths(item: FormItem, path: TreePath): TreePath[] {
  if (item.type === "node") return [[...path, item.node.name]];
  const members = item.branches.flatMap((branch) => branch.members);
  return [[...path, choiceKey(item.id)], ...members.map((member) => [...path, member.name])];
}

export function startsWith(path: TreePath, prefix: TreePath): boolean {
  return prefix.every((segment, index) => String(path[index]) === String(segment));
}

/**
 * A spec for the whole page as a group holding the page's root element, which is required
 * because the user chose the page. This lets a page whose root is a single amount (CT600K)
 * be handled like any other.
 */
export function pageSpec(page: SchemaPage): SpecNode {
  return {
    ...page.node,
    name: "",
    path: "",
    box: null,
    kind: "group",
    min: 1,
    max: 1,
    choice: null,
    branch: null,
    choices: [],
    children: [{ ...page.node, min: 1 }],
  };
}

function isPlainGroup(node: SpecNode): boolean {
  return node.kind === "group" && !repeats(node) && node.choices.length === 0;
}

/**
 * Split a page into screens, one per top-level group (GOV.UK's one thing per page), with runs
 * of single questions and choices between groups sharing a screen. A root that only wraps one
 * required group is looked through, so the screens follow the content.
 */
export function pageScreens(page: SchemaPage): Screen[] {
  let node = page.node;
  let path: TreePath = [node.name];
  if (node.kind !== "group") {
    return [{ id: node.name, title: page.title, path: [], items: [{ type: "node", node }] }];
  }
  let only = node.children.length === 1 ? node.children[0] : undefined;
  while (only && isPlainGroup(only) && only.min > 0) {
    node = only;
    path = [...path, node.name];
    only = node.children.length === 1 ? node.children[0] : undefined;
  }

  const screens: Screen[] = [];
  let run: FormItem[] = [];
  const closeRun = () => {
    if (run.length === 0) return;
    const [first] = run;
    const id = first?.type === "node" ? first.node.name : (first?.branches[0]?.name ?? "");
    const title =
      run.length === 1 && first?.type === "node" ? first.node.label : continuedTitle(page, screens);
    screens.push({ id, title, path, items: run });
    run = [];
  };
  for (const item of formItems(node)) {
    if (item.type === "node" && item.node.kind === "group") {
      closeRun();
      screens.push({ id: item.node.name, title: item.node.label, path, items: [item] });
    } else run.push(item);
  }
  closeRun();
  if (screens.length === 1 && screens[0]) screens[0] = { ...screens[0], title: page.title };
  return screens;
}

function continuedTitle(page: SchemaPage, screens: Screen[]): string {
  const earlier = screens.some((screen) => screen.title.startsWith(page.title));
  return earlier ? `${page.title} (continued)` : page.title;
}

/** The screen that asks for the answer at ``path``, if any does. */
export function screenFor(screens: Screen[], path: TreePath): Screen | undefined {
  return screens.find((screen) =>
    screen.items.some((item) =>
      itemPaths(item, screen.path).some((prefix) => startsWith(path, prefix)),
    ),
  );
}

/** A DOM id for the answer at ``path`` on page ``code``. */
export function fieldId(code: PageCode, path: TreePath): string {
  const joined = [code, ...path.map(String)].join("-");
  return joined.replace(/[^A-Za-z0-9_-]/g, "_");
}

/**
 * The id a link to an error at ``path`` should focus: a choice's first radio, a list's "Add
 * another" button, a date's day input, or else the field itself.
 */
export function errorTargetId(code: PageCode, path: TreePath, node: SpecNode | null): string {
  const id = fieldId(code, path);
  const last = path.at(-1);
  if (typeof last === "string" && last.startsWith("?")) return id;
  if (node && node.kind === "group" && repeats(node) && last === node.name) return `${id}-add`;
  return node?.kind === "date" ? `${id}-day` : id;
}

/** The elements a screen shows: a lone group's children, or else its own items' elements. */
export function screenNodes(screen: Screen): { nodes: SpecNode[]; path: TreePath } {
  const [only] = screen.items;
  if (screen.items.length === 1 && only?.type === "node" && isPlainGroup(only.node)) {
    return { nodes: only.node.children, path: [...screen.path, only.node.name] };
  }
  const nodes = screen.items.flatMap((item) =>
    item.type === "node" ? [item.node] : item.branches.flatMap((branch) => branch.members),
  );
  return { nodes, path: screen.path };
}

/** The label as the middle of a sentence: "Amount of loan" becomes "amount of loan". */
export function phrase(label: string): string {
  if (/^.[A-Z]/.test(label)) return label;
  return label.charAt(0).toLowerCase() + label.slice(1);
}

export function sentence(label: string): string {
  return label.charAt(0).toUpperCase() + label.slice(1);
}

/** The "Box A15" hint prefix for an element HMRC's form numbers. */
export function boxHint(node: SpecNode): string | undefined {
  return node.box ? `Box ${node.box}` : undefined;
}
