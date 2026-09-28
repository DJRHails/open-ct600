import { Link } from "react-router";

import { TwoThirds, usePageTitle } from "@/components/content";

export function CookiesPage() {
  usePageTitle("Cookies");

  return (
    <TwoThirds>
      <h1 className="govuk-heading-xl">Cookies</h1>
      <p className="govuk-body-l">Open CT600 does not use cookies.</p>
      <p className="govuk-body">
        We do not use analytics or advertising tools, and we do not track you across other websites.
        That is why you do not see a cookie banner.
      </p>
      <h2 className="govuk-heading-l">How we save your draft return</h2>
      <p className="govuk-body">
        When you prepare a return, your answers are saved in your browser’s local storage. This is
        not a cookie. It is never sent to our server with your requests, and we cannot read it.
      </p>
      <p className="govuk-body">
        This lets you leave and come back to your return on the same device and browser. Your draft
        stays there until you delete it.
      </p>
      <h2 className="govuk-heading-l">Delete your draft</h2>
      <p className="govuk-body">
        You can delete your draft from the{" "}
        <Link className="govuk-link" to="/file/tasks">
          task list page
        </Link>
        . You can also clear this site’s data in your browser settings.
      </p>
      <p className="govuk-body">
        Read our{" "}
        <Link className="govuk-link" to="/privacy">
          privacy notice
        </Link>{" "}
        to find out what other information we collect.
      </p>
    </TwoThirds>
  );
}
