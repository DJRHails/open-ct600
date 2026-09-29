/**
 * HMRC's box guidance, loaded when a page first needs it: it is large, so it is kept out of
 * the main bundle.
 */
import { useEffect, useState } from "react";

import type { Guidance } from "@/content/help/hmrc/extract";
import { type GuidanceIndex, indexGuidance } from "@/content/help/hmrc/lookup";

export type GuidanceState =
  | { status: "loading" }
  | { status: "ready"; index: GuidanceIndex }
  | { status: "failed" };

let loading: Promise<GuidanceIndex> | null = null;
let loaded: GuidanceIndex | null = null;

function load(): Promise<GuidanceIndex> {
  loading ??= import("@/content/help/hmrc/guidance.json").then((module) => {
    // JSON's strings are not typed as the block kinds; extract.test.ts checks the file is
    // exactly what ``extractGuidance`` gives.
    loaded = indexGuidance(module.default as Guidance);
    return loaded;
  });
  return loading;
}

export function useGuidance(): GuidanceState {
  const [state, setState] = useState<GuidanceState>(
    loaded ? { status: "ready", index: loaded } : { status: "loading" },
  );
  const settled = state.status !== "loading";
  useEffect(() => {
    if (settled) return;
    let current = true;
    load().then(
      (index) => current && setState({ status: "ready", index }),
      (error: unknown) => {
        // Let a later page try again, and say here that it could not be loaded.
        loading = null;
        console.error("Could not load HMRC's guidance", error);
        if (current) setState({ status: "failed" });
      },
    );
    return () => {
      current = false;
    };
  }, [settled]);
  return state;
}
