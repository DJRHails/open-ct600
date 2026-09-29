import { useSearchParams } from "react-router";

import type { PageCode } from "@/api";

export const TASK_LIST = "/file/tasks";
export const CHECK_ANSWERS = "/file/check-your-answers";
export const DECLARATION = "/file/declaration";
export const CONFIRMATION = "/file/confirmation";
export const CHOOSE_PAGES = "/file/supplementary-pages";
export const RETURNS = "/file/returns";
export const IMPORT_RETURN = "/file/returns/import";

/** The page that asks the user to confirm deleting a saved return. */
export function deleteReturnPath(id: string): string {
  return `${RETURNS}/${id}/delete`;
}

/** A supplementary page's own check your answers page. */
export function pagePath(code: PageCode): string {
  return `${CHOOSE_PAGES}/${code}`;
}

/** One screen of questions on a supplementary page. */
export function screenPath(code: PageCode, screen: string): string {
  return `${pagePath(code)}/${screen}`;
}

/** Where a section page goes after saving: back to check answers if it came from there. */
export function useNextPage(): { next: string; changing: boolean } {
  const [params] = useSearchParams();
  const changing = params.get("change") === "1";
  return { next: changing ? CHECK_ANSWERS : TASK_LIST, changing };
}
