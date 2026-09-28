import { Link } from "react-router";

import { TwoThirds, usePageTitle } from "@/components/content";
import { REPOSITORY_URL } from "@/components/Layout";
import { ExternalLink } from "@/content/guides";

function FiguresAndDrafts() {
  return (
    <>
      <h2 className="govuk-heading-l">Figures you enter</h2>
      <p className="govuk-body">
        When you use the calculator or prepare a return, the figures you enter are sent to the Open
        CT600 server to work out your tax. The server uses them to do the calculation and does not
        store them.
      </p>
      <h2 className="govuk-heading-l">Your draft return</h2>
      <p className="govuk-body">
        Your draft return is saved in your own browser, using a feature called local storage. It is
        not sent to us to be stored. It stays on your device until you delete it.
      </p>
      <p className="govuk-body">
        You can delete your draft from the{" "}
        <Link className="govuk-link" to="/file/tasks">
          task list page
        </Link>
        . Clearing your browser’s site data also deletes it.
      </p>
      <h2 className="govuk-heading-l">Cookies and analytics</h2>
      <p className="govuk-body">
        We do not use cookies or analytics. Read our{" "}
        <Link className="govuk-link" to="/cookies">
          cookies page
        </Link>{" "}
        for details.
      </p>
    </>
  );
}

export function PrivacyPage() {
  usePageTitle("Privacy notice");

  return (
    <TwoThirds>
      <h1 className="govuk-heading-xl">Privacy notice</h1>
      <p className="govuk-body-l">
        This notice explains what information Open CT600 collects and what happens to it.
      </p>
      <p className="govuk-body">
        Open CT600 is a demonstration. Do not enter your company’s real tax references or anything
        you would not want someone else to see.
      </p>
      <FiguresAndDrafts />
      <h2 className="govuk-heading-l">Technical logs</h2>
      <p className="govuk-body">
        The server that hosts this site may keep standard technical logs, such as your IP address
        and the pages you request, to keep the service running.
      </p>
      <h2 className="govuk-heading-l">Contact</h2>
      <p className="govuk-body">
        To ask about your information or have it deleted,{" "}
        <ExternalLink href={`${REPOSITORY_URL}/issues`}>open an issue on GitHub</ExternalLink>. Do
        not include personal details in the issue.
      </p>
    </TwoThirds>
  );
}
