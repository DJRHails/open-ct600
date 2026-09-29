import { TwoThirds, usePageTitle } from "@/components/content";
import { REPOSITORY_URL } from "@/components/Layout";
import { ExternalLink, RECOGNISED_SOFTWARE_URL } from "@/content/guides";

function WhatThisServiceIs() {
  return (
    <>
      <h2 className="govuk-heading-l">What Open CT600 does</h2>
      <p className="govuk-body">
        Open CT600 prepares a Company Tax Return (CT600) with its supplementary pages, iXBRL
        accounts and tax computations, works out Corporation Tax, and checks the return against
        HMRC’s published schema and business rules.
      </p>
      <p className="govuk-body">
        It can send a return to HMRC only where whoever runs it has an HMRC vendor ID and has
        switched submission on. You can then send a test to HMRC’s Test in Live service, which does
        not file the return, or file it for real. Where submission is off, the last step gives you a
        demonstration receipt only: it does not mean your return has been filed.
      </p>
      <p className="govuk-body">
        HMRC has not yet published the computations taxonomy for periods ending after 31 March 2026,
        so returns for those periods cannot be sent until it does.
      </p>
      <p className="govuk-body">
        Open CT600 is not on HMRC’s list of recognised Corporation Tax software, and HMRC has not
        approved it. HMRC decides whether to accept each return. You can also file with{" "}
        <ExternalLink href={RECOGNISED_SOFTWARE_URL}>HMRC-recognised software</ExternalLink> or an
        accountant.
      </p>
      <h2 className="govuk-heading-l">Not tax advice</h2>
      <p className="govuk-body">
        Nothing on this site is tax, legal or financial advice. You are responsible for your
        company’s tax return, for checking that its figures are correct, and for any return you send
        to HMRC. If you are unsure, ask an accountant.
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
        <li>
          Only enter Government Gateway sign in details you are authorised to use for the company.
        </li>
        <li>We may change or stop this service at any time.</li>
      </ul>
      <h2 className="govuk-heading-l">Changes to these terms</h2>
      <p className="govuk-body">
        We may update these terms. Changes are recorded in the project’s history on GitHub.
      </p>
    </TwoThirds>
  );
}
