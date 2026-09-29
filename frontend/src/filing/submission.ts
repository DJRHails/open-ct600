/** What went wrong with a submission, sorted into what the declaration page shows for each. */
import { ApiError, type HmrcProblem, type SchemaPage } from "@/api";
import type { ErrorItem } from "@/components/forms";
import { hmrcErrorItems } from "@/filing/hmrcProblems";
import type { FieldErrors } from "@/filing/model";
import { CHECK_ANSWERS } from "@/filing/paths";

export type Failure =
  /** Errors to show on this page: on its fields, and in the summary. */
  | { kind: "errors"; fields: FieldErrors; general: ErrorItem[]; description?: string }
  /** HMRC has not answered in time: the return may still be accepted. */
  | { kind: "pending"; correlationId: string | null };

const FIELDS = new Set(["name", "capacity", "confirmed", "gateway_user_id", "gateway_password"]);

function locatedErrors(error: ApiError): Failure {
  const fields: FieldErrors = {};
  const general: ErrorItem[] = [];
  for (const problem of error.problems) {
    const [section, field] = problem.path;
    if (section === "declaration" && field) fields[field] = problem.message;
    else if (section && FIELDS.has(section)) fields[section] = problem.message;
    else general.push({ href: CHECK_ANSWERS, text: problem.message });
  }
  return { kind: "errors", fields, general };
}

function withReference(message: string, correlationId: string | null): string {
  return correlationId ? `${message} HMRC's reference for it is ${correlationId}.` : message;
}

/** HMRC rejected the return's content: list HMRC's problems, linking to where to fix them. */
export function rejected(
  problems: HmrcProblem[],
  pages: SchemaPage[],
  description: string,
): Failure {
  return { kind: "errors", fields: {}, general: hmrcErrorItems(problems, pages), description };
}

/** Sort a failed submission into what to show. */
export function failure(error: unknown, pages: SchemaPage[]): Failure {
  if (!(error instanceof ApiError)) {
    const text = `Your return was not submitted: ${String(error)}`;
    return { kind: "errors", fields: {}, general: [{ href: "#main-content", text }] };
  }
  if (error.problems.length > 0) return locatedErrors(error);
  switch (error.code) {
    case "authentication_failed":
      return {
        kind: "errors",
        fields: {
          gateway_user_id:
            "HMRC did not accept this Government Gateway user ID and password. Check them and try again",
          gateway_password: "Enter your Government Gateway password again",
        },
        general: [],
      };
    case "submission_disabled":
      return {
        kind: "errors",
        fields: {
          method: `${error.message} Choose to get a demonstration receipt instead, or file your return with other software.`,
        },
        general: [],
      };
    case "invalid_return":
      return rejected(
        error.hmrcErrors,
        pages,
        "HMRC would reject your return, so it was not sent. Correct these problems and submit it again.",
      );
    case "hmrc_timeout":
      return { kind: "pending", correlationId: error.correlationId };
    default: {
      const text = withReference(
        `Your return was not submitted: ${error.message}`,
        error.correlationId,
      );
      return { kind: "errors", fields: {}, general: [{ href: "#main-content", text }] };
    }
  }
}
