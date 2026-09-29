/** Links from a problem to the screen and field where the user can fix it. */
import type { SchemaPage, SpecNode } from "@/api";
import { pagePath, screenPath } from "@/filing/paths";
import type { Problem } from "@/filing/supplementary/answers";
import {
  errorTargetId,
  fieldId,
  pageScreens,
  repeats,
  screenFor,
  type TreePath,
} from "@/filing/supplementary/spec";

/** How a problem is listed in an error summary: with the list item it is about, if any. */
export function summaryText(problem: Problem): string {
  return problem.context ? `${problem.message} (${problem.context})` : problem.message;
}

/**
 * A link to the screen that asks for the answer at ``path``, which checks its answers on
 * arrival and focuses ``targetId``. ``fromCheck`` returns the user to check your answers after.
 */
export function screenLink(
  page: SchemaPage,
  path: TreePath,
  targetId: string,
  fromCheck: boolean,
): string {
  const screen = screenFor(pageScreens(page), path);
  if (!screen) return `${pagePath(page.code)}${fromCheck ? "?change=1" : ""}`;
  const from = fromCheck ? "&from=check" : "";
  return `${screenPath(page.code, screen.id)}?change=1&check=1${from}#${targetId}`;
}

export function problemLink(page: SchemaPage, problem: Problem, fromCheck: boolean): string {
  return screenLink(
    page,
    problem.path,
    errorTargetId(page.code, problem.path, problem.node),
    fromCheck,
  );
}

const RETURN_PATH = "/IRenvelope/CompanyTaxReturn/";
const INDEXED = /^(?<name>[^[]+)\[(?<position>[0-9]+)\]$/;

/**
 * The page and tree path of an element HMRC names, like
 * ``/IRenvelope/CompanyTaxReturn/LoansByCloseCompanies/LoansInformation/Loan[2]/Name``.
 */
export function locateOnPage(
  pages: SchemaPage[],
  xmlPath: string | null,
): { page: SchemaPage; path: TreePath; node: SpecNode } | null {
  if (!xmlPath?.startsWith(RETURN_PATH)) return null;
  const steps = xmlPath.slice(RETURN_PATH.length).split("/");
  const parse = (step: string) => {
    const indexed = INDEXED.exec(step)?.groups;
    return { name: indexed?.name ?? step, position: Number(indexed?.position ?? 1) };
  };
  const [head, ...rest] = steps.map(parse);
  const page = pages.find((candidate) => candidate.node.name === head?.name);
  if (!page || !head) return null;
  let node = page.node;
  const path: TreePath = [node.name];
  for (const step of rest) {
    const child = node.children.find((candidate) => candidate.name === step.name);
    if (!child) break;
    node = child;
    path.push(child.name);
    if (repeats(child)) path.push(step.position - 1);
  }
  return { page, path, node };
}

function answerLink(page: SchemaPage, path: TreePath, node: SpecNode): string {
  const listItem = typeof path.at(-1) === "number" && node.kind === "group";
  const target = listItem
    ? `${fieldId(page.code, path)}-legend`
    : errorTargetId(page.code, path, node);
  return screenLink(page, path, target, true);
}

/** A link to where HMRC's problem at ``xmlPath`` can be fixed, if it is on a supplementary page. */
export function hmrcProblemLink(pages: SchemaPage[], xmlPath: string | null): string | null {
  const located = locateOnPage(pages, xmlPath);
  return located ? answerLink(located.page, located.path, located.node) : null;
}

/**
 * A link to the answer the service rejected, from its location in the request, like
 * ``["supplementary_pages", "A", "LoansInformation", "Loan", "0", "Name"]``.
 */
export function rejectedAnswerLink(pages: SchemaPage[], location: string[]): string | null {
  const [section, code, ...rest] = location;
  const page = pages.find((candidate) => candidate.code === code);
  if (section !== "supplementary_pages" || !page) return null;
  let node = page.node;
  const path: TreePath = [node.name];
  for (const segment of rest) {
    if (/^[0-9]+$/.test(segment)) {
      path.push(Number(segment));
      continue;
    }
    const child = node.children.find((candidate) => candidate.name === segment);
    if (!child) break;
    node = child;
    path.push(segment);
  }
  return answerLink(page, path, node);
}
