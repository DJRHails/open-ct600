import { Link } from "react-router";

import { TwoThirds, usePageTitle, WarningText } from "@/components/content";
import { ExternalLink, RECOGNISED_SOFTWARE_URL } from "@/content/guides";

function WhatHasChanged() {
  return (
    <>
      <h2 className="govuk-heading-l">What has changed</h2>
      <p className="govuk-body">
        For many years, small companies could file their accounts and Company Tax Return through a
        free online service run jointly by HMRC and Companies House. It was called Company Accounts
        and Tax Online, often shortened to CATO.
      </p>
      <p className="govuk-body">
        That service closed on 31 March 2026. You can no longer file a CT600 through HMRC’s own
        website. You must now use commercial software or an agent, such as an accountant.
      </p>
      <h2 className="govuk-heading-l">Who is affected</h2>
      <p className="govuk-body">
        The change affects companies that filed their own returns through the free service. These
        are mostly small companies with simple affairs, such as:
      </p>
      <ul className="govuk-list govuk-list--bullet">
        <li>companies run by a single director</li>
        <li>dormant companies that HMRC has asked to file a return</li>
        <li>small trading companies with straightforward accounts</li>
      </ul>
      <p className="govuk-body">
        If you already use an accountant or commercial software, nothing changes for you.
      </p>
    </>
  );
}

function YourOptions() {
  return (
    <>
      <h2 className="govuk-heading-l">Your options</h2>
      <h3 className="govuk-heading-m">Use an accountant</h3>
      <p className="govuk-body">
        An accountant will prepare and file your accounts and tax return for you. Fees are typically
        £300 to £1,000 or more a year, depending on your company.
      </p>
      <h3 className="govuk-heading-m">Use HMRC-recognised software</h3>
      <p className="govuk-body">
        Commercial software can prepare and submit your return. Many products charge a monthly
        subscription or a fee per return. HMRC publishes a{" "}
        <ExternalLink href={RECOGNISED_SOFTWARE_URL}>
          list of recognised Corporation Tax software
        </ExternalLink>
        . Some products on the list are marked as suitable for companies that file their own
        returns.
      </p>
      <h3 className="govuk-heading-m">Prepare your figures with Open CT600</h3>
      <p className="govuk-body">
        Open CT600 is free and open source. It helps you work out your Corporation Tax and the
        figures for each CT600 box, so you know what to expect before you file.
      </p>
      <WarningText>
        Open CT600 is a demonstration. It does not submit returns to HMRC and is not on HMRC’s list
        of recognised software. You still need to file using one of the other options.
      </WarningText>
    </>
  );
}

function WhatToDoNow() {
  return (
    <>
      <h2 className="govuk-heading-l">What to do now</h2>
      <ol className="govuk-list govuk-list--number">
        <li>
          Check your deadlines. Your Corporation Tax is due 9 months and 1 day after the end of your
          accounting period. Your return is due 12 months after it ends.
        </li>
        <li>
          Gather your records, including bank statements, invoices and receipts for the period.
        </li>
        <li>
          Estimate your bill using the{" "}
          <Link className="govuk-link" to="/calculator">
            Corporation Tax calculator
          </Link>
          .
        </li>
        <li>Choose an accountant or HMRC-recognised software to file your return.</li>
      </ol>
      <h2 className="govuk-heading-l">Companies House accounts</h2>
      <p className="govuk-body">
        Filing your annual accounts with Companies House is a separate obligation, with its own
        deadline. For a private company this is usually 9 months after the end of its financial
        year. Read how to{" "}
        <ExternalLink href="https://www.gov.uk/file-your-company-annual-accounts">
          file your annual accounts with Companies House
        </ExternalLink>
        .
      </p>
    </>
  );
}

export function FreeFilingPage() {
  usePageTitle("HMRC’s free Company Tax Return filing has closed");

  return (
    <TwoThirds>
      <h1 className="govuk-heading-xl">HMRC’s free Company Tax Return filing has closed</h1>
      <p className="govuk-body-l">
        If you filed your company’s CT600 yourself using HMRC’s free online service, you need a new
        way to file from 1 April 2026.
      </p>
      <WhatHasChanged />
      <YourOptions />
      <WhatToDoNow />
      <p className="govuk-body">
        Read our guide on{" "}
        <Link className="govuk-link" to="/guides/how-to-file-a-ct600">
          how to file a CT600
        </Link>
        .
      </p>
    </TwoThirds>
  );
}
