import { useSearchParams } from "react-router";

export const TASK_LIST = "/file/tasks";
export const CHECK_ANSWERS = "/file/check-your-answers";
export const DECLARATION = "/file/declaration";
export const CONFIRMATION = "/file/confirmation";

/** Where a section page goes after saving: back to check answers if it came from there. */
export function useNextPage(): { next: string; changing: boolean } {
  const [params] = useSearchParams();
  const changing = params.get("change") === "1";
  return { next: changing ? CHECK_ANSWERS : TASK_LIST, changing };
}
