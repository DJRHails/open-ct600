import { useState } from "react";
import { Link } from "react-router";

import { TwoThirds, usePageTitle } from "@/components/content";
import { Button } from "@/components/forms";
import { Deadlines } from "@/filing/Deadlines";
import { useDraft } from "@/filing/draft";
import { CHECK_ANSWERS, CHOOSE_PAGES, pagePath, RETURNS } from "@/filing/paths";
import {
  completedCount,
  needsSchema,
  pageComplete,
  savedPeriod,
  sectionComplete,
  SECTION_ORDER,
  SECTION_SLUGS,
  SECTION_TITLES,
} from "@/filing/model";
import { type ReliefTask, RELIEF_TASKS, reliefComplete, reliefTasks } from "@/filing/payload";
import { pageName } from "@/filing/supplementary/content";
import { useSchemaPages } from "@/filing/supplementary/schema";
import { useRepaymentDue } from "@/filing/useRepaymentDue";

type Task = { id: string; title: string; to: string; completed: boolean };

function TaskItem({ task }: { task: Task }) {
  const statusId = `${task.id}-status`;
  return (
    <li className="govuk-task-list__item govuk-task-list__item--with-link">
      <div className="govuk-task-list__name-and-hint">
        <Link className="govuk-link govuk-task-list__link" to={task.to} aria-describedby={statusId}>
          {task.title}
        </Link>
      </div>
      <div className="govuk-task-list__status" id={statusId}>
        {task.completed ? (
          "Completed"
        ) : (
          <strong className="govuk-tag govuk-tag--blue">Incomplete</strong>
        )}
      </div>
    </li>
  );
}

function CheckTask({ canStart }: { canStart: boolean }) {
  const title = "Check your answers and submit";
  if (!canStart) {
    return (
      <li className="govuk-task-list__item">
        <div className="govuk-task-list__name-and-hint">
          <div>{title}</div>
        </div>
        <div className="govuk-task-list__status govuk-task-list__status--cannot-start-yet">
          Cannot start yet
        </div>
      </li>
    );
  }
  return (
    <li className="govuk-task-list__item govuk-task-list__item--with-link">
      <div className="govuk-task-list__name-and-hint">
        <Link
          className="govuk-link govuk-task-list__link"
          to={CHECK_ANSWERS}
          aria-describedby="check-status"
        >
          {title}
        </Link>
      </div>
      <div className="govuk-task-list__status" id="check-status">
        <strong className="govuk-tag govuk-tag--blue">Incomplete</strong>
      </div>
    </li>
  );
}

/**
 * The reliefs and supplementary pages tasks: the R&D claim, choosing the pages, then each page
 * chosen, followed by any relief answers it needs that it has no box for.
 */
function useSupplementaryTasks(): { supplementary: Task[]; repayment: Task[] } {
  const { draft } = useDraft();
  const schema = useSchemaPages(needsSchema(draft));
  const pages = schema.status === "ready" ? schema.pages : undefined;
  const chosen = draft.chosen_pages ?? [];
  const reliefs = reliefTasks(draft, pages);
  const due = useRepaymentDue(draft, pages);
  const reliefTask = (task: ReliefTask): Task => ({
    id: task,
    title: RELIEF_TASKS[task].title,
    to: `/file/${RELIEF_TASKS[task].slug}`,
    completed: reliefComplete(draft, task, pages),
  });
  const choose: Task = {
    id: "supplementary-pages",
    title: "Choose supplementary pages",
    to: CHOOSE_PAGES,
    completed: draft.chosen_pages !== undefined,
  };
  const supplementary = [
    reliefTask("research_and_development"),
    choose,
    ...chosen.flatMap((code) => {
      const page = pages?.find((candidate) => candidate.code === code);
      const pageTask = {
        id: `page-${code}`,
        title: page ? `${pageName(code)}: ${page.title}` : pageName(code),
        to: pagePath(code),
        completed: page !== undefined && pageComplete(draft, page),
      };
      const extras = reliefs.filter((task) => RELIEF_TASKS[task].page === code);
      return [pageTask, ...extras.map(reliefTask)];
    }),
  ];
  // Asked once the computation shows money due back, and kept once given.
  const repayment = due || reliefs.includes("repayment") ? [reliefTask("repayment")] : [];
  return { supplementary, repayment };
}

export function TaskListPage() {
  usePageTitle("Company Tax Return");
  const { draft, receipt } = useDraft();
  const { supplementary, repayment } = useSupplementaryTasks();
  const sections: Task[] = SECTION_ORDER.map((section) => ({
    id: section,
    title: SECTION_TITLES[section],
    to: `/file/${SECTION_SLUGS[section]}`,
    completed: sectionComplete(draft, section),
  }));
  const extras = [...supplementary, ...repayment];
  const total = sections.length + extras.length;
  const completed = completedCount(draft) + extras.filter((task) => task.completed).length;
  const started = completed > 0 || Object.keys(draft).length > 0;
  const periodEnd = savedPeriod(draft)?.end;

  return (
    <TwoThirds>
      <span className="govuk-caption-l">{draft.company?.name ?? "Your company"}</span>
      <h1 className="govuk-heading-xl">Company Tax Return</h1>
      <p className="govuk-body">
        You have completed {completed} of {total} sections.
      </p>
      {periodEnd ? <Deadlines periodEnd={periodEnd} /> : null}

      <h2 className="govuk-heading-m">Your company and its accounts</h2>
      <ul className="govuk-task-list">
        {sections.map((task) => (
          <TaskItem key={task.id} task={task} />
        ))}
      </ul>

      <h2 className="govuk-heading-m">Reliefs and supplementary pages</h2>
      <ul className="govuk-task-list">
        {supplementary.map((task) => (
          <TaskItem key={task.id} task={task} />
        ))}
      </ul>

      {repayment.length > 0 ? (
        <>
          <h2 className="govuk-heading-m">Money due back to the company</h2>
          <ul className="govuk-task-list">
            {repayment.map((task) => (
              <TaskItem key={task.id} task={task} />
            ))}
          </ul>
        </>
      ) : null}

      <h2 className="govuk-heading-m">Submit</h2>
      <ul className="govuk-task-list">
        <CheckTask canStart={completed === total} />
      </ul>

      <SavedAnswers canDelete={started || receipt !== null} />
    </TwoThirds>
  );
}

/** Where the answers are kept, how to take them elsewhere, and how to delete them. */
function SavedAnswers({ canDelete }: { canDelete: boolean }) {
  const { returns, deleteAnswers } = useDraft();
  const [deleted, setDeleted] = useState(false);
  const remaining = returns.length;

  function remove() {
    deleteAnswers();
    setDeleted(true);
  }

  return (
    <>
      <h2 className="govuk-heading-s">Your saved answers</h2>
      <div aria-live="polite">
        {deleted ? (
          <div className="govuk-inset-text">
            Your answers have been deleted.{" "}
            {remaining > 0
              ? `You still have ${remaining} ${remaining === 1 ? "return" : "returns"} saved. `
              : ""}
            <Link className="govuk-link" to={RETURNS}>
              Go to your returns
            </Link>
          </div>
        ) : null}
      </div>
      <p className="govuk-body">
        Your answers, and the receipt for any return you have submitted, are saved in this browser
        only. To keep a copy or carry on in another browser, export this return from{" "}
        <Link className="govuk-link" to={RETURNS}>
          your returns
        </Link>
        .
      </p>
      {canDelete ? (
        <>
          <p className="govuk-body">Delete your answers if you are using a shared computer.</p>
          <Button type="button" variant="warning" onClick={remove}>
            Delete your answers
          </Button>
        </>
      ) : null}
    </>
  );
}
