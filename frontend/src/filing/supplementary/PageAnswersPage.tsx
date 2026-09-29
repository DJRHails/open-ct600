import { useState } from "react";
import { Link, Navigate, useNavigate, useParams, useSearchParams } from "react-router";

import type { ElementTree, JsonValue, SchemaPage } from "@/api";
import { BackLink, TwoThirds, usePageTitle } from "@/components/content";
import { Button, type ErrorItem, ErrorSummary } from "@/components/forms";
import { useDraft } from "@/filing/draft";
import { screenPath, TASK_LIST, useNextPage } from "@/filing/paths";
import { convertPage, type Problem } from "@/filing/supplementary/answers";
import { pageName } from "@/filing/supplementary/content";
import { problemLink, summaryText } from "@/filing/supplementary/links";
import { SchemaGate } from "@/filing/supplementary/SchemaGate";
import { pageScreens, type Screen, screenNodes, type TreePath } from "@/filing/supplementary/spec";
import { TreeSummary } from "@/filing/supplementary/summary";
import { NotFoundPage } from "@/pages/NotFound";

function subtree(tree: JsonValue | undefined, path: TreePath): ElementTree {
  let current = tree;
  for (const segment of path) {
    if (typeof current !== "object" || current === null || Array.isArray(current)) return {};
    current = current[String(segment)];
  }
  return typeof current === "object" && current !== null && !Array.isArray(current) ? current : {};
}

type PageProps = { page: SchemaPage; changing: boolean };

function toErrorItem(page: SchemaPage, problem: Problem, changing: boolean): ErrorItem {
  return { href: problemLink(page, problem, changing), text: summaryText(problem) };
}

function ScreenCard({
  page,
  screen,
  tree,
  changing,
}: PageProps & { screen: Screen; tree: JsonValue }) {
  const { nodes, path } = screenNodes(screen);
  const from = changing ? "&from=check" : "";
  return (
    <div className="govuk-summary-card">
      <div className="govuk-summary-card__title-wrapper">
        <h2 className="govuk-summary-card__title">{screen.title}</h2>
        <ul className="govuk-summary-card__actions">
          <li className="govuk-summary-card__action">
            <Link className="govuk-link" to={`${screenPath(page.code, screen.id)}?change=1${from}`}>
              Change<span className="govuk-visually-hidden"> {screen.title.toLowerCase()}</span>
            </Link>
          </li>
        </ul>
      </div>
      <div className="govuk-summary-card__content">
        <TreeSummary nodes={nodes} tree={subtree(tree, path)} />
      </div>
    </div>
  );
}

/** Check your answers for one supplementary page, with a card per screen of questions. */
function PageAnswers({ page, changing }: PageProps) {
  const { draft } = useDraft();
  const { next } = useNextPage();
  const navigate = useNavigate();
  const [errors, setErrors] = useState<ErrorItem[]>([]);
  const [attempt, setAttempt] = useState(0);
  const title = `Check your answers for ${pageName(page.code)}`;
  usePageTitle(title, errors.length > 0);
  const screens = pageScreens(page);
  const raw = draft.supplementary_pages?.[page.code];
  const [first] = screens;
  if (raw === undefined && first) return <Navigate to={screenPath(page.code, first.id)} replace />;

  const converted = convertPage(page, raw);
  const tree = { [page.node.name]: converted.value };

  function finish() {
    setAttempt(attempt + 1);
    setErrors(converted.problems.map((problem) => toErrorItem(page, problem, changing)));
    if (converted.problems.length === 0) navigate(next);
  }

  return (
    <>
      <BackLink to={TASK_LIST} />
      <TwoThirds>
        <ErrorSummary key={attempt} errors={errors} />
        <span className="govuk-caption-l">{`${pageName(page.code)}: ${page.title}`}</span>
        <h1 className="govuk-heading-l">{title}</h1>
        {screens.map((screen) => (
          <ScreenCard key={screen.id} page={page} screen={screen} tree={tree} changing={changing} />
        ))}
        <Button type="button" onClick={finish}>
          Continue
        </Button>
      </TwoThirds>
    </>
  );
}

function PageRoute({ pages }: { pages: SchemaPage[] }) {
  const { code } = useParams();
  const [params] = useSearchParams();
  const { draft } = useDraft();
  const page = pages.find((candidate) => candidate.code === code && !candidate.dormant);
  if (!page) return <NotFoundPage />;
  if (!draft.chosen_pages?.includes(page.code)) return <Navigate to={TASK_LIST} replace />;
  return <PageAnswers page={page} changing={params.get("change") === "1"} />;
}

export function PageAnswersPage() {
  return (
    <SchemaGate title="Supplementary page">{(pages) => <PageRoute pages={pages} />}</SchemaGate>
  );
}
