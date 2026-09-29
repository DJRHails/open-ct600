import { useEffect, useState } from "react";

import { api, type HmrcEnvironment } from "@/api";

/** The HMRC services this deployment can send to; none if it cannot say. ``null`` until known. */
export function useSubmissionEnvironments(): HmrcEnvironment[] | null {
  const [environments, setEnvironments] = useState<HmrcEnvironment[] | null>(null);
  useEffect(() => {
    let current = true;
    api.submissionStatus().then(
      (status) => current && setEnvironments(status.enabled ? status.environments : []),
      () => current && setEnvironments([]),
    );
    return () => {
      current = false;
    };
  }, []);
  return environments;
}
