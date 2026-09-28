import { useEffect, useMemo, useState } from "react";
import { Link, Navigate } from "react-router";

import { api, ApiError, type CT600Return, type ReturnComputation } from "@/api";
import { BackLink, SummaryList, usePageTitle } from "@/components/content";
import { type ErrorItem, ErrorSummary } from "@/components/forms";
import { TaxBreakdownTable, TaxSummary } from "@/components/TaxBreakdown";
import { useDraft } from "@/filing/draft";
import {
  answerRows,
  SECTION_ORDER,
  SECTION_SLUGS,
  SECTION_TITLES,
  type SectionKey,
  toReturn,
} from "@/filing/model";
import { DECLARATION, TASK_LIST } from "@/filing/paths";
import { AccountsTables, CT600BoxesTable } from "@/filing/ReturnViews";
import { formatPounds } from "@/format";

type Computed =
  | { state: "loading" }
  | { state: "done"; computation: ReturnComputation }
  | { state: "failed"; errors: ErrorItem[] };

function changeLink(section: SectionKey): string {
  return `/file/${SECTION_SLUGS[section]}?change=1`;
}

function toErrorItems(error: unknown): ErrorItem[] {
  if (error instanceof ApiError && error.problems.length > 0) {
    return error.problems.map((problem) => {
      const section = SECTION_ORDER.find((key) => key === problem.path[0]);
      return { href: section ? changeLink(section) : TASK_LIST, text: problem.message };
    });
  }
  const message = error instanceof Error ? error.message : String(error);
  return [{ href: "#main-content", text: `We could not work out your tax: ${message}` }];
}

/** Ask the API to compute the return whenever the answers change. */
function useComputation(ct600: CT600Return | null): Computed {
  const [latest, setLatest] = useState<{ ct600: CT600Return; result: Computed } | null>(null);

  useEffect(() => {
    if (ct600 === null) return;
    let current = true;
    const settle = (result: Computed) => current && setLatest({ ct600, result });
    api.computeReturn(ct600).then(
      (computation) => settle({ state: "done", computation }),
      (error: unknown) => settle({ state: "failed", errors: toErrorItems(error) }),
    );
    return () => {
      current = false;
    };
  }, [ct600]);
  return latest !== null && latest.ct600 === ct600 ? latest.result : { state: "loading" };
}

function SectionCard({ ct600, section }: { ct600: CT600Return; section: SectionKey }) {
  const title = SECTION_TITLES[section];
  return (
    <div className="govuk-summary-card">
      <div className="govuk-summary-card__title-wrapper">
        <h2 className="govuk-summary-card__title">{title}</h2>
        <ul className="govuk-summary-card__actions">
          <li className="govuk-summary-card__action">
            <Link className="govuk-link" to={changeLink(section)}>
              Change<span className="govuk-visually-hidden"> {title.toLowerCase()}</span>
            </Link>
          </li>
        </ul>
      </div>
      <div className="govuk-summary-card__content">
        <SummaryList
          rows={answerRows(ct600, section).map((row) => ({ key: row.label, value: row.value }))}
        />
      </div>
    </div>
  );
}

function ComputationSection({ computation }: { computation: ReturnComputation }) {
  return (
    <>
      <h2 className="govuk-heading-l">Your Corporation Tax</h2>
      <TaxSummary tax={computation.tax} />
      <TaxBreakdownTable tax={computation.tax} />
      {computation.losses_carried_forward > 0 ? (
        <div className="govuk-inset-text">
          Trading losses of {formatPounds(computation.losses_carried_forward)} will be carried
          forward to your next accounting period.
        </div>
      ) : null}
      <CT600BoxesTable boxes={computation.boxes} />
      <h2 className="govuk-heading-m">Your micro-entity accounts</h2>
      <AccountsTables accounts={computation.accounts} />
      <h2 className="govuk-heading-m">Now send your return</h2>
      <p className="govuk-body">
        Check the figures above. On the next page you'll make a declaration and submit your return.
      </p>
      <Link to={DECLARATION} draggable={false} className="govuk-button" data-module="govuk-button">
        Continue
      </Link>
    </>
  );
}

export function CheckAnswersPage() {
  const { draft } = useDraft();
  const ct600 = useMemo(() => toReturn(draft), [draft]);
  const computed = useComputation(ct600);
  const errors = computed.state === "failed" ? computed.errors : [];
  usePageTitle("Check your answers", errors.length > 0);

  if (ct600 === null) return <Navigate to={TASK_LIST} replace />;
  return (
    <>
      <BackLink to={TASK_LIST} />
      <div className="govuk-grid-row">
        <div className="govuk-grid-column-full">
          <ErrorSummary errors={errors} />
          <span className="govuk-caption-l">{ct600.company.name}</span>
          <h1 className="govuk-heading-xl">Check your answers before submitting your return</h1>
          {SECTION_ORDER.map((section) => (
            <SectionCard key={section} ct600={ct600} section={section} />
          ))}
          {computed.state === "loading" ? (
            <p className="govuk-body">Working out your tax…</p>
          ) : null}
          {computed.state === "done" ? (
            <ComputationSection computation={computed.computation} />
          ) : null}
        </div>
      </div>
    </>
  );
}
