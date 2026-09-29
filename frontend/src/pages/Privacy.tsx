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
        CT600 server to work out your tax, check the return against HMRC’s rules and create your
        accounts, computations and CT600 documents. The server uses them for that request only and
        does not store them.
      </p>
      <h2 className="govuk-heading-l">Your saved returns</h2>
      <p className="govuk-body">
        The returns you prepare are saved in your own browser, using a feature called local storage.
        They are not sent to us to be stored. They stay on your device until you delete them.
      </p>
      <p className="govuk-body">
        You can export a return to a file, to keep a copy or to import it into another browser. The
        file is saved wherever you choose, and it is not encrypted, so it holds your company’s tax
        details in plain text. Keep it somewhere safe. We never see the file.
      </p>
      <p className="govuk-body">
        You can delete a return from{" "}
        <Link className="govuk-link" to="/file/returns">
          Your returns
        </Link>
        . Clearing your browser’s site data deletes all of them.
      </p>
      <SendingToHmrc />
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

function SendingToHmrc() {
  return (
    <>
      <h2 className="govuk-heading-l">Sending your return to HMRC</h2>
      <p className="govuk-body">
        If you choose to send your return to HMRC, the server sends it to HMRC’s Transaction Engine
        with the Government Gateway user ID and password you enter. Those credentials are passed
        straight to HMRC for that one submission. They are never stored, in your browser or on the
        server, and never logged. The password is cleared from the page as soon as it has been sent.
      </p>
      <p className="govuk-body">
        HMRC’s receipt is kept in your browser for the current tab only, so you can print or save
        it. It is deleted when you close the tab. Sending returns to HMRC only works where whoever
        runs the service has an HMRC vendor ID and has switched submission on.
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
        Open CT600 is open-source software that anyone can run. Use a copy run by someone you trust,
        or run it yourself, before you enter your company’s real details or Government Gateway sign
        in.
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
