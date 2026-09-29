import { Link } from "react-router";

import { TwoThirds, usePageTitle } from "@/components/content";
import { Button } from "@/components/forms";
import { useDraft } from "@/filing/draft";
import { CHECK_ANSWERS } from "@/filing/paths";
import {
  completedCount,
  sectionComplete,
  SECTION_ORDER,
  SECTION_SLUGS,
  SECTION_TITLES,
  type SectionKey,
} from "@/filing/model";

function TaskItem({ section, completed }: { section: SectionKey; completed: boolean }) {
  const statusId = `${section}-status`;
  return (
    <li className="govuk-task-list__item govuk-task-list__item--with-link">
      <div className="govuk-task-list__name-and-hint">
        <Link
          className="govuk-link govuk-task-list__link"
          to={`/file/${SECTION_SLUGS[section]}`}
          aria-describedby={statusId}
        >
          {SECTION_TITLES[section]}
        </Link>
      </div>
      <div className="govuk-task-list__status" id={statusId}>
        {completed ? (
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

export function TaskListPage() {
  usePageTitle("Company Tax Return");
  const { draft, receipt, deleteAnswers } = useDraft();
  const completed = completedCount(draft);
  const allDone = completed === SECTION_ORDER.length;

  return (
    <TwoThirds>
      <span className="govuk-caption-l">{draft.company?.name ?? "Your company"}</span>
      <h1 className="govuk-heading-xl">Company Tax Return</h1>
      <p className="govuk-body">
        You have completed {completed} of {SECTION_ORDER.length} sections.
      </p>

      <h2 className="govuk-heading-m">Your company and its accounts</h2>
      <ul className="govuk-task-list">
        {SECTION_ORDER.map((section) => (
          <TaskItem key={section} section={section} completed={sectionComplete(draft, section)} />
        ))}
      </ul>

      <h2 className="govuk-heading-m">Submit</h2>
      <ul className="govuk-task-list">
        <CheckTask canStart={allDone} />
      </ul>

      {completed > 0 || receipt !== null ? (
        <>
          <h2 className="govuk-heading-s">Your saved answers</h2>
          <p className="govuk-body">
            Your answers, and the receipt for any return you have submitted, are saved in this
            browser only. Delete them if you are using a shared computer.
          </p>
          <Button type="button" variant="warning" onClick={deleteAnswers}>
            Delete your answers
          </Button>
        </>
      ) : null}
    </TwoThirds>
  );
}
