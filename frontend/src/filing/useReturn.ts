import { useMemo } from "react";

import type { CT600Return, SchemaPage } from "@/api";
import { useDraft } from "@/filing/draft";
import { needsSchema } from "@/filing/model";
import { toReturn } from "@/filing/payload";
import { useSchemaPages } from "@/filing/supplementary/schema";

export type ReturnState =
  | { status: "loading" }
  | { status: "failed"; message: string }
  | { status: "incomplete" }
  | { status: "ready"; ct600: CT600Return; pages: SchemaPage[] };

/** The completed return built from the draft, once HMRC's page definitions are loaded if needed. */
export function useReturn(): ReturnState {
  const { draft } = useDraft();
  const schemaNeeded = needsSchema(draft);
  const schema = useSchemaPages(schemaNeeded);
  const pages = schema.status === "ready" ? schema.pages : undefined;
  const ct600 = useMemo(() => toReturn(draft, pages), [draft, pages]);

  if (schemaNeeded && schema.status === "failed") {
    return { status: "failed", message: schema.message };
  }
  if (schemaNeeded && !pages) return { status: "loading" };
  if (ct600 === null) return { status: "incomplete" };
  return { status: "ready", ct600, pages: pages ?? [] };
}
