import { type ReactNode, useEffect } from "react";
import { Link } from "react-router";

import { SERVICE_NAME } from "@/components/Layout";

/** Set the document title in GOV.UK style: "Error: Page – Service". */
export function usePageTitle(title: string, hasErrors = false) {
  useEffect(() => {
    document.title = `${hasErrors ? "Error: " : ""}${title} – ${SERVICE_NAME}`;
  }, [title, hasErrors]);
}

export type SummaryRow = {
  key: ReactNode;
  value: ReactNode;
  change?: { to: string; label: string };
};

export function SummaryList({ rows, noBorder }: { rows: SummaryRow[]; noBorder?: boolean }) {
  return (
    <dl
      className={
        noBorder ? "govuk-summary-list govuk-summary-list--no-border" : "govuk-summary-list"
      }
    >
      {rows.map((row, index) => (
        <div
          className={
            row.change
              ? "govuk-summary-list__row"
              : "govuk-summary-list__row govuk-summary-list__row--no-actions"
          }
          key={index}
        >
          <dt className="govuk-summary-list__key">{row.key}</dt>
          <dd className="govuk-summary-list__value">{row.value}</dd>
          {row.change ? (
            <dd className="govuk-summary-list__actions">
              <Link className="govuk-link" to={row.change.to}>
                {"Change "}
                <span className="govuk-visually-hidden">{row.change.label}</span>
              </Link>
            </dd>
          ) : null}
        </div>
      ))}
    </dl>
  );
}

/** A GOV.UK summary card: a titled group of answers with a link to change them. */
export function Card(props: { title: string; change: string; children: ReactNode }) {
  return (
    <div className="govuk-summary-card">
      <div className="govuk-summary-card__title-wrapper">
        <h2 className="govuk-summary-card__title">{props.title}</h2>
        <ul className="govuk-summary-card__actions">
          <li className="govuk-summary-card__action">
            <Link className="govuk-link" to={props.change}>
              {"Change "}
              <span className="govuk-visually-hidden">{props.title.toLowerCase()}</span>
            </Link>
          </li>
        </ul>
      </div>
      <div className="govuk-summary-card__content">{props.children}</div>
    </div>
  );
}

export function Panel({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="govuk-panel govuk-panel--confirmation">
      <h1 className="govuk-panel__title">{title}</h1>
      {children ? <div className="govuk-panel__body">{children}</div> : null}
    </div>
  );
}

/** A GOV.UK notification banner, for important information that is not an error. */
export function NotificationBanner({ title, children }: { title: string; children: ReactNode }) {
  const id = `banner-${title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
  return (
    <section className="govuk-notification-banner" aria-labelledby={id}>
      <div className="govuk-notification-banner__header">
        <h2 className="govuk-notification-banner__title" id={id}>
          {title}
        </h2>
      </div>
      <div className="govuk-notification-banner__content">{children}</div>
    </section>
  );
}

/** Says a section's answers came from Companies House, so the user checks them. */
export function PrefilledBanner() {
  return (
    <NotificationBanner title="Important">
      <p className="govuk-notification-banner__heading">
        We’ve filled in some answers from Companies House. Check them before you continue.
      </p>
    </NotificationBanner>
  );
}

export function WarningText({ children }: { children: ReactNode }) {
  return (
    <div className="govuk-warning-text">
      <span className="govuk-warning-text__icon" aria-hidden="true">
        !
      </span>
      <strong className="govuk-warning-text__text">
        <span className="govuk-visually-hidden">Warning</span>
        {children}
      </strong>
    </div>
  );
}

export function BackLink({ to, children = "Back" }: { to: string; children?: ReactNode }) {
  return (
    <Link to={to} className="govuk-back-link app-no-print">
      {children}
    </Link>
  );
}

/** A two-thirds column, the standard GOV.UK reading width. */
export function TwoThirds({ children }: { children: ReactNode }) {
  return (
    <div className="govuk-grid-row">
      <div className="govuk-grid-column-two-thirds">{children}</div>
    </div>
  );
}
