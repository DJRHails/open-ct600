/** HMRC's problems with a return, as error summary items linking to where to fix them. */
import type { HmrcProblem, SchemaPage } from "@/api";
import type { ErrorItem } from "@/components/forms";
import { DECLARATION, pagePath } from "@/filing/paths";
import { hmrcProblemLink } from "@/filing/supplementary/links";

/** Where to fix problems with parts of the main return the user answers directly. */
const MAIN_RETURN: Record<string, string> = {
  IRheader: "/file/company-details?change=1",
  CompanyInformation: "/file/company-details?change=1",
  AttachedFiles: "/file/accounts-details?change=1",
  Declaration: DECLARATION,
};

/** The element under ``/IRenvelope`` (or under the return itself) HMRC names. */
function topElement(path: string | null): string | null {
  const steps = (path ?? "").split("/").filter(Boolean);
  const [envelope, first, second] = steps.map((step) => step.replace(/\[[0-9]+\]$/, ""));
  if (envelope !== "IRenvelope" || !first) return null;
  return first === "CompanyTaxReturn" ? (second ?? null) : first;
}

/**
 * Where the user can fix a problem: the question on a supplementary page, the section of the
 * main return, or else the CT600 boxes the service worked out.
 */
export function hmrcProblemHref(problem: HmrcProblem, pages: SchemaPage[]): string {
  const onPage = hmrcProblemLink(pages, problem.path);
  if (onPage) return onPage;
  if (problem.page) return `${pagePath(problem.page)}?change=1`;
  const element = topElement(problem.path);
  return (element && MAIN_RETURN[element]) || "#ct600-boxes";
}

/** HMRC's message, with its error code and the box, for reference. */
export function hmrcProblemText(problem: HmrcProblem): string {
  const reference = [
    problem.code === null ? null : `HMRC error ${problem.code}`,
    problem.box ? `box ${problem.box}` : null,
  ].filter(Boolean);
  return reference.length > 0 ? `${problem.message} (${reference.join(", ")})` : problem.message;
}

export function hmrcErrorItems(problems: HmrcProblem[], pages: SchemaPage[]): ErrorItem[] {
  return problems.map((problem) => ({
    href: hmrcProblemHref(problem, pages),
    text: hmrcProblemText(problem),
  }));
}
