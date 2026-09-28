import { Link } from "react-router";

import { TwoThirds, usePageTitle } from "@/components/content";

export function NotFoundPage() {
  usePageTitle("Page not found");

  return (
    <TwoThirds>
      <h1 className="govuk-heading-l">Page not found</h1>
      <p className="govuk-body">If you typed the web address, check it is correct.</p>
      <p className="govuk-body">
        If you pasted the web address, check you copied the entire address.
      </p>
      <p className="govuk-body">
        You can go to the{" "}
        <Link className="govuk-link" to="/">
          Open CT600 home page
        </Link>{" "}
        or{" "}
        <Link className="govuk-link" to="/guides">
          read our guides
        </Link>
        .
      </p>
    </TwoThirds>
  );
}
