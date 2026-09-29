import { type ReactNode, useEffect, useState } from "react";
import { Link, Navigate } from "react-router";

import {
  api,
  ApiError,
  type CT600Return,
  type ReturnComputation,
  type SchemaPage,
  type ValidationResult,
} from "@/api";
import { BackLink, SummaryList, usePageTitle } from "@/components/content";
import { type ErrorItem, ErrorSummary } from "@/components/forms";
import { TaxBreakdownTable, TaxSummary } from "@/components/TaxBreakdown";
import { Downloads } from "@/filing/Downloads";
import { hmrcErrorItems } from "@/filing/hmrcProblems";
import {
  answerRows,
  SECTION_ORDER,
  SECTION_SLUGS,
  SECTION_TITLES,
  type SectionKey,
} from "@/filing/model";
import { CHOOSE_PAGES, DECLARATION, pagePath, TASK_LIST } from "@/filing/paths";
import { Pending } from "@/filing/Pending";
import { ReliefsSummary } from "@/filing/ReliefsSummary";
import { AccountsTables, CT600BoxesTable } from "@/filing/ReturnViews";
import { pageName } from "@/filing/supplementary/content";
import { rejectedAnswerLink } from "@/filing/supplementary/links";
import { TreeSummary } from "@/filing/supplementary/summary";
import { useReturn } from "@/filing/useReturn";
import { formatPounds } from "@/format";

type Result<T> =
  | { state: "loading" }
  | { state: "done"; value: T }
  | { state: "failed"; error: unknown };

function changeLink(section: SectionKey): string {
  return `/file/${SECTION_SLUGS[section]}?change=1`;
}

function toErrorItems(error: unknown, pages: SchemaPage[]): ErrorItem[] {
  if (error instanceof ApiError && error.problems.length > 0) {
    return error.problems.map((problem) => {
      const section = SECTION_ORDER.find((key) => key === problem.path[0]);
      const href = section
        ? changeLink(section)
        : (rejectedAnswerLink(pages, problem.path) ?? TASK_LIST);
      return { href, text: problem.message };
    });
  }
  const message = error instanceof Error ? error.message : String(error);
  return [{ href: "#main-content", text: `We could not work out your tax: ${message}` }];
}

/** Call the API with the return whenever it changes, keeping only the latest answer. */
function useLatest<T>(ct600: CT600Return | null, call: (ct600: CT600Return) => Promise<T>) {
  const [latest, setLatest] = useState<{ ct600: CT600Return; result: Result<T> } | null>(null);

  useEffect(() => {
    if (ct600 === null) return;
    let current = true;
    const settle = (result: Result<T>) => current && setLatest({ ct600, result });
    call(ct600).then(
      (value) => settle({ state: "done", value }),
      (error: unknown) => settle({ state: "failed", error }),
    );
    return () => {
      current = false;
    };
  }, [ct600, call]);
  const loading: Result<T> = { state: "loading" };
  return latest !== null && latest.ct600 === ct600 ? latest.result : loading;
}

function SectionCard({ ct600, section }: { ct600: CT600Return; section: SectionKey }) {
  const title = SECTION_TITLES[section];
  return (
    <Card title={title} change={changeLink(section)}>
      <SummaryList
        rows={answerRows(ct600, section).map((row) => ({ key: row.label, value: row.value }))}
      />
    </Card>
  );
}

function Card(props: { title: string; change: string; children: ReactNode }) {
  return (
    <div className="govuk-summary-card">
      <div className="govuk-summary-card__title-wrapper">
        <h2 className="govuk-summary-card__title">{props.title}</h2>
        <ul className="govuk-summary-card__actions">
          <li className="govuk-summary-card__action">
            <Link className="govuk-link" to={props.change}>
              Change<span className="govuk-visually-hidden"> {props.title.toLowerCase()}</span>
            </Link>
          </li>
        </ul>
      </div>
      <div className="govuk-summary-card__content">{props.children}</div>
    </div>
  );
}

type PagesProps = {
  ct600: CT600Return;
  pages: SchemaPage[];
  computation: ReturnComputation | null;
};

/** The supplementary pages chosen and their answers, with the boxes the service worked out. */
function SupplementaryCards({ ct600, pages, computation }: PagesProps) {
  const chosen = Object.keys(ct600.supplementary_pages ?? {});
  const titled = pages.filter((page) => chosen.includes(page.code));
  return (
    <>
      <Card title="Supplementary pages" change={`${CHOOSE_PAGES}?change=1`}>
        <SummaryList
          rows={[
            {
              key: "Pages the company is completing",
              value:
                titled.length === 0
                  ? "None"
                  : titled.map((page) => `${pageName(page.code)}: ${page.title}`).join(", "),
            },
          ]}
        />
      </Card>
      {titled.map((page) => {
        const answers = computation?.pages[page.code] ?? ct600.supplementary_pages?.[page.code];
        return (
          <Card
            key={page.code}
            title={`${pageName(page.code)}: ${page.title}`}
            change={`${pagePath(page.code)}?change=1`}
          >
            <TreeSummary nodes={page.node.children} tree={answers ?? {}} />
          </Card>
        );
      })}
    </>
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
      {computation.reliefs ? <ReliefsSummary reliefs={computation.reliefs} /> : null}
      <div id="ct600-boxes" tabIndex={-1}>
        <CT600BoxesTable boxes={computation.boxes} />
      </div>
      <h2 className="govuk-heading-m">Your accounts</h2>
      <AccountsTables accounts={computation.accounts} />
    </>
  );
}

function ValidationNotice({ validation }: { validation: Result<ValidationResult> }) {
  if (validation.state === "loading") {
    return <p className="govuk-body">Checking your return against HMRC's rules…</p>;
  }
  if (validation.state === "failed") {
    const message =
      validation.error instanceof Error ? validation.error.message : String(validation.error);
    return (
      <div className="govuk-inset-text">
        We could not check your return against HMRC's rules: {message}
      </div>
    );
  }
  if (validation.value.problems.length > 0) return null;
  return <div className="govuk-inset-text">HMRC's rules found no problems with your return.</div>;
}

function Checked({ ct600, pages }: { ct600: CT600Return; pages: SchemaPage[] }) {
  const computed = useLatest(ct600, api.computeReturn);
  const validation = useLatest(ct600, api.validateReturn);
  const computation = computed.state === "done" ? computed.value : null;
  const failures = computed.state === "failed" ? toErrorItems(computed.error, pages) : [];
  const problems =
    validation.state === "done" ? hmrcErrorItems(validation.value.problems, pages) : [];
  const errors = [...failures, ...problems];
  usePageTitle("Check your answers", errors.length > 0);

  return (
    <>
      <BackLink to={TASK_LIST} />
      <div className="govuk-grid-row">
        <div className="govuk-grid-column-full">
          <ErrorSummary
            errors={errors}
            description={
              problems.length > 0
                ? "HMRC would reject your return as it stands. Correct these problems before you submit it to HMRC."
                : undefined
            }
          />
          <span className="govuk-caption-l">{ct600.company.name}</span>
          <h1 className="govuk-heading-xl">Check your answers before submitting your return</h1>
          {SECTION_ORDER.map((section) => (
            <SectionCard key={section} ct600={ct600} section={section} />
          ))}
          <SupplementaryCards ct600={ct600} pages={pages} computation={computation} />
          {computed.state === "loading" ? (
            <p className="govuk-body">Working out your tax…</p>
          ) : null}
          {computation ? <ComputationSection computation={computation} /> : null}
          <ValidationNotice validation={validation} />
          <Downloads ct600={ct600} />
          <h2 className="govuk-heading-m">Now send your return</h2>
          <p className="govuk-body">
            Check the figures above. On the next page you'll make a declaration and submit your
            return.
          </p>
          <Link
            to={DECLARATION}
            draggable={false}
            className="govuk-button"
            data-module="govuk-button"
          >
            Continue
          </Link>
        </div>
      </div>
    </>
  );
}

export function CheckAnswersPage() {
  const built = useReturn();
  if (built.status === "incomplete") return <Navigate to={TASK_LIST} replace />;
  if (built.status === "ready") return <Checked ct600={built.ct600} pages={built.pages} />;
  const failure = built.status === "failed" ? built.message : null;
  return <Pending title="Check your answers" failure={failure} />;
}
