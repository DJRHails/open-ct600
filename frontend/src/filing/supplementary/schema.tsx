import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { api, type SchemaPage } from "@/api";
import { withComputed } from "@/filing/supplementary/spec";

export type SchemaState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; pages: SchemaPage[] }
  | { status: "failed"; message: string };

type SchemaStore = { state: SchemaState; load: () => void };

const SchemaContext = createContext<SchemaStore | null>(null);

/** Holds HMRC's supplementary page definitions, fetched once, the first time a page needs them. */
export function SchemaProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<SchemaState>({ status: "idle" });
  const started = useRef(false);

  const load = useCallback(() => {
    if (started.current) return;
    started.current = true;
    setState({ status: "loading" });
    api.schemaPages().then(
      (pages) => setState({ status: "ready", pages: pages.map(withComputed) }),
      (error: unknown) =>
        setState({
          status: "failed",
          message: error instanceof Error ? error.message : String(error),
        }),
    );
  }, []);

  const store = useMemo(() => ({ state, load }), [state, load]);
  return <SchemaContext.Provider value={store}>{children}</SchemaContext.Provider>;
}

/** The supplementary page definitions, loading them if ``needed``. */
export function useSchemaPages(needed = true): SchemaState {
  const store = useContext(SchemaContext);
  if (!store) throw new Error("useSchemaPages must be used inside <SchemaProvider>");
  const { state, load } = store;
  useEffect(() => {
    if (needed) load();
  }, [needed, load]);
  return state;
}
