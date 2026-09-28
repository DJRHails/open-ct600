import { TwoThirds, usePageTitle } from "@/components/content";
import { REPOSITORY_URL } from "@/components/Layout";
import { ExternalLink, RECOGNISED_SOFTWARE_URL } from "@/content/guides";

function WhatThisServiceIs() {
  return (
    <>
      <h2 className="govuk-heading-l">A demonstration only</h2>
      <p className="govuk-body">
        Open CT600 prepares CT600 figures and works out Corporation Tax. It does not submit returns
        to HMRC. The submit step gives you a demo receipt only. It does not mean your return has
        been filed.
      </p>
      <p className="govuk-body">
        Open CT600 is not on HMRC’s list of recognised Corporation Tax software. To file your
        return, use{" "}
        <ExternalLink href={RECOGNISED_SOFTWARE_URL}>HMRC-recognised software</ExternalLink> or an
        accountant.
      </p>
      <h2 className="govuk-heading-l">Not tax advice</h2>
      <p className="govuk-body">
        Nothing on this site is tax, legal or financial advice. You are responsible for your
        company’s tax return and for checking that its figures are correct. If you are unsure, ask
        an accountant.
      </p>
    </>
  );
}

export function TermsPage() {
  usePageTitle("Terms of use");

  return (
    <TwoThirds>
      <h1 className="govuk-heading-xl">Terms of use</h1>
      <p className="govuk-body-l">By using Open CT600 you agree to these terms.</p>
      <WhatThisServiceIs />
      <h2 className="govuk-heading-l">Licence</h2>
      <p className="govuk-body">
        Open CT600 is open-source software released under the MIT licence. You can use, copy, change
        and share the code under the terms of that licence. The{" "}
        <ExternalLink href={REPOSITORY_URL}>source code is on GitHub</ExternalLink>.
      </p>
      <h2 className="govuk-heading-l">No warranty</h2>
      <p className="govuk-body">
        The software is provided ‘as is’, without warranty of any kind. The authors are not liable
        for any claim, damages or other liability arising from its use, including tax, penalties or
        interest you may have to pay.
      </p>
      <h2 className="govuk-heading-l">Using this site</h2>
      <ul className="govuk-list govuk-list--bullet">
        <li>Do not try to disrupt the service or access it in ways it is not designed for.</li>
        <li>Do not enter information you are not allowed to share.</li>
        <li>We may change or stop this demonstration at any time.</li>
      </ul>
      <h2 className="govuk-heading-l">Changes to these terms</h2>
      <p className="govuk-body">
        We may update these terms. Changes are recorded in the project’s history on GitHub.
      </p>
    </TwoThirds>
  );
}
