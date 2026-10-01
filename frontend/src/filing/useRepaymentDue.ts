import { useEffect, useMemo, useState } from "react";

import { api, ApiError, type CT600Return, type SchemaPage } from "@/api";
import type { Draft } from "@/filing/model";
import { toReturn } from "@/filing/payload";
import { moneyDueBack } from "@/filing/repayment";

/**
 * Whether the return shows money due back to the company, so its bank details are needed. Only
 * the computation knows (payable credits depend on the whole return), so this asks the service
 * once every other part of the return is complete: money is due back if the computation shows
 * it, or if the service asks for the bank details (a problem located at ``repayment``).
 * ``false`` until then, and if the service cannot be asked.
 */
export function useRepaymentDue(draft: Draft, pages: SchemaPage[] | undefined): boolean {
  const ct600 = useMemo(() => toReturn(draft, pages), [draft, pages]);
  const [answer, setAnswer] = useState<{ ct600: CT600Return; due: boolean } | null>(null);

  useEffect(() => {
    if (ct600 === null) return;
    let current = true;
    const settle = (due: boolean) => current && setAnswer({ ct600, due });
    api.computeReturn(ct600).then(
      (computation) => settle(moneyDueBack(computation.boxes)),
      (error: unknown) =>
        settle(
          error instanceof ApiError &&
            error.problems.some((problem) => problem.path[0] === "repayment"),
        ),
    );
    return () => {
      current = false;
    };
  }, [ct600]);

  return answer !== null && answer.ct600 === ct600 && answer.due;
}
