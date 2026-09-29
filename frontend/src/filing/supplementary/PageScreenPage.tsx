import { useEffect, useRef, useState } from "react";
import { Navigate, useLocation, useNavigate, useParams, useSearchParams } from "react-router";

import type { SchemaPage } from "@/api";
import type { ErrorItem } from "@/components/forms";
import { useDraft } from "@/filing/draft";
import { pagePath, screenPath, TASK_LIST } from "@/filing/paths";
import { SectionFrame } from "@/filing/SectionFrame";
import {
  type Problem,
  type RawTree,
  type RawValue,
  screenProblems,
  setAt,
} from "@/filing/supplementary/answers";
import { pageName } from "@/filing/supplementary/content";
import { Items, PageFormProvider, pathKey } from "@/filing/supplementary/fields";
import { summaryText } from "@/filing/supplementary/links";
import { SchemaGate } from "@/filing/supplementary/SchemaGate";
import {
  errorTargetId,
  formItems,
  pageScreens,
  repeats,
  type Screen,
} from "@/filing/supplementary/spec";
import { NotFoundPage } from "@/pages/NotFound";

/** Find the page and screen named in the URL, among the pages the user chose. */
function ScreenRoute({ pages }: { pages: SchemaPage[] }) {
  const { code, screen: screenId } = useParams();
  const { draft } = useDraft();
  const page = pages.find((candidate) => candidate.code === code && !candidate.dormant);
  if (!page) return <NotFoundPage />;
  if (!draft.chosen_pages?.includes(page.code)) return <Navigate to={TASK_LIST} replace />;
  const screens = pageScreens(page);
  const index = screens.findIndex((screen) => screen.id === screenId);
  if (index < 0) return <NotFoundPage />;
  return (
    <ScreenForm key={`${page.code}/${screenId}`} page={page} screens={screens} index={index} />
  );
}

type ScreenFormProps = { page: SchemaPage; screens: Screen[]; index: number };

function ScreenQuestions({ screen }: { screen: Screen }) {
  const [only] = screen.items;
  if (screen.items.length === 1 && only?.type === "node" && only.node.kind === "group") {
    if (!repeats(only.node)) {
      const path = [...screen.path, only.node.name];
      return <Items items={formItems(only.node)} path={path} depth={0} />;
    }
  }
  return <Items items={screen.items} path={screen.path} depth={0} />;
}

function intro(screen: Screen): string | undefined {
  const [only] = screen.items;
  if (screen.items.length !== 1 || only?.type !== "node" || only.node.kind !== "group") {
    return undefined;
  }
  const box = only.node.box ? `Box ${only.node.box}. ` : "";
  const optional = only.node.min === 0 ? "Leave this blank if it does not apply." : "";
  return `${box}${optional}`.trim() || undefined;
}

/** One screen of a supplementary page's questions, saved to the draft when it is valid. */
function ScreenForm({ page, screens, index }: ScreenFormProps) {
  const screen = screens[index] as Screen;
  const { draft, savePageAnswers } = useDraft();
  const [params] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [answers, setAnswers] = useState<RawTree>(
    () => draft.supplementary_pages?.[page.code] ?? {},
  );
  const [problems, setProblems] = useState<Problem[]>(() =>
    params.get("check") === "1" ? screenProblems(page, screen, answers) : [],
  );

  const fromCheck = params.get("from") === "check";
  const overview = `${pagePath(page.code)}${fromCheck ? "?change=1" : ""}`;
  const following = screens[index + 1];
  const changing = params.get("change") === "1";
  const next =
    changing || !following
      ? overview
      : `${screenPath(page.code, following.id)}${fromCheck ? "?from=check" : ""}`;
  const previous = screens[index - 1];
  const back = changing ? overview : previous ? screenPath(page.code, previous.id) : TASK_LIST;

  // On arrival from an error elsewhere, the link names the field to fix. When this screen has
  // errors of its own, the error summary takes focus instead.
  const arrivalTarget = useRef(problems.length > 0 ? "" : location.hash.slice(1));
  useEffect(() => {
    if (arrivalTarget.current) {
      document.getElementById(decodeURIComponent(arrivalTarget.current))?.focus();
    }
  }, []);

  function save() {
    const found = screenProblems(page, screen, answers);
    setProblems(found);
    if (found.length > 0) return;
    savePageAnswers(page.code, answers);
    navigate(next);
  }

  const errors = Object.fromEntries(
    [...problems].reverse().map((found) => [pathKey(found.path), found.message]),
  );
  const summary: ErrorItem[] = problems.map((found) => ({
    href: `#${errorTargetId(page.code, found.path, found.node)}`,
    text: summaryText(found),
  }));

  return (
    <SectionFrame
      title={screen.title}
      caption={`${pageName(page.code)}: ${page.title}`}
      errors={errors}
      fieldOrder={[]}
      summary={summary}
      onSubmit={save}
      intro={intro(screen)}
      backTo={back}
    >
      <PageFormProvider
        value={{
          code: page.code,
          answers,
          setAnswer: (path, value: RawValue) =>
            setAnswers((current) => setAt(current, path, value) as RawTree),
          errors,
          clearErrors: () => setProblems([]),
        }}
      >
        <ScreenQuestions screen={screen} />
      </PageFormProvider>
    </SectionFrame>
  );
}

export function PageScreenPage() {
  return (
    <SchemaGate title="Supplementary page">{(pages) => <ScreenRoute pages={pages} />}</SchemaGate>
  );
}
