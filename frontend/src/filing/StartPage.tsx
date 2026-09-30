import { Link } from "react-router";

import { TwoThirds, usePageTitle, WarningText } from "@/components/content";
import { StartButton } from "@/components/forms";
import { ExternalLink } from "@/content/guides";
import { useDraft } from "@/filing/draft";
import { RETURNS, TASK_LIST } from "@/filing/paths";
import { useSubmissionEnvironments } from "@/filing/useSubmissionEnvironments";

function SavedReturnsLink() {
  const { returns } = useDraft();
  const count = returns.length;
  return (
    <p className="govuk-body">
      {count > 0
        ? `You have ${count} ${count === 1 ? "return" : "returns"} saved in this browser. `
        : "Have a return exported from Open CT600? "}
      <Link className="govuk-link" to={RETURNS}>
        {count > 0 ? "Go to your returns" : "Import it from Your returns"}
      </Link>
      .
    </p>
  );
}

const COMPANIES_HOUSE_SEARCH = "https://find-and-update.company-information.service.gov.uk/";
const UTR_COPY = "https://www.tax.service.gov.uk/ask-for-copy-of-your-corporation-tax-utr";
const HMRC_SIGN_IN = "https://www.gov.uk/log-in-register-hmrc-online-services";

/**
 * What to have ready, and where to find it. Checked against gov.uk on 29 September 2026:
 * - Registration number: HMRC's Company Tax Return guide, box 2
 *   (https://www.gov.uk/guidance/the-company-tax-return-guide).
 * - UTR: 10 digits (https://www.gov.uk/find-utr-number); the last 10 digits of the 13-digit
 *   number on HMRC's letters (the guide, box 3); on HMRC's CT41G letter "Corporation Tax:
 *   Company Unique Taxpayer Reference (UTR)" sent after the company is set up
 *   (http://www.hmrc.gov.uk/gds/com/attachments/ct41g.pdf); a copy can be requested online and
 *   is posted to the registered office.
 * - Accounting period: https://www.gov.uk/corporation-tax-accounting-period.
 * - Government Gateway: add Corporation Tax to the business tax account; the activation code
 *   "can take up to 10 days" by post (https://www.gov.uk/government/publications/
 *   use-hmrcs-business-tax-account/use-hmrcs-business-tax-account).
 */
function WhatYoullNeed() {
  const environments = useSubmissionEnvironments();
  const canSubmit = environments !== null && environments.length > 0;
  return (
    <>
      <h2 className="govuk-heading-m">What you'll need</h2>
      <ul className="govuk-list govuk-list--bullet govuk-list--spaced">
        <li>
          <strong>The company registration number</strong>, like 01234567 or SC123456. It is on the
          company's certificate of incorporation and letters from Companies House, or you can{" "}
          <ExternalLink href={COMPANIES_HOUSE_SEARCH}>
            search the Companies House register
          </ExternalLink>
          .
        </li>
        <li>
          <strong>The company's Corporation Tax Unique Taxpayer Reference (UTR)</strong>, which is
          10 digits. It is on the letter HMRC sent when the company was set up (form CT41G), and on
          notices to file a return and payment reminders. If a letter shows a 13-digit number, the
          UTR is the last 10 digits. If you cannot find it,{" "}
          <ExternalLink href={UTR_COPY}>ask HMRC for a copy</ExternalLink>, which is posted to the
          company's registered office.
        </li>
        <li>
          <strong>The accounting period's start and end dates</strong>. This is usually the period
          the company's annual accounts cover, and it cannot be longer than 12 months.
        </li>
        <li>
          <strong>Figures from the company's accounts</strong> for the period: its profit and loss
          account and balance sheet, the directors' names and the date the accounts were approved.
        </li>
        <li>
          <strong>Details for tax</strong>, if they apply: capital allowances on equipment or
          vehicles (including writing down allowances on things bought before), trading losses from
          earlier periods (on its last Company Tax Return), assets it sold, donations to charity,
          dividends it received and other companies it is connected with.
        </li>
        {canSubmit ? (
          <li>
            <strong>The company's Government Gateway user ID and password</strong>, to send the
            return to HMRC. If the company does not have one,{" "}
            <ExternalLink href={HMRC_SIGN_IN}>register for HMRC online services</ExternalLink> and
            add Corporation Tax. HMRC posts an activation code, which can take up to 10 days to
            arrive, so do this well before your deadline.
          </li>
        ) : null}
      </ul>
    </>
  );
}

export function StartPage() {
  usePageTitle("File your Company Tax Return");

  return (
    <TwoThirds>
      <h1 className="govuk-heading-xl">File your Company Tax Return (CT600)</h1>
      <p className="govuk-body-l">
        Use this service to prepare your company's Corporation Tax return, work out the tax it owes,
        and produce the figures for its micro-entity accounts.
      </p>
      <p className="govuk-body">You can use this service if your company:</p>
      <ul className="govuk-list govuk-list--bullet">
        <li>is a UK resident limited company that trades or has been dormant</li>
        <li>qualifies as a micro-entity or small company</li>
        <li>has an accounting period of 12 months or less</li>
      </ul>
      <p className="govuk-body">
        If the company needs supplementary pages, such as for loans to participators, group relief
        or research and development, you can complete them too.
      </p>
      <p className="govuk-body">
        It takes around 20 minutes. Your answers are saved in this browser as you go. You can export
        a return to a file to keep a copy, or to carry on in another browser.
      </p>

      <WarningText>
        This service only sends returns to HMRC where whoever runs it has an HMRC vendor ID and has
        switched submission on. Otherwise you can check your return and get a demonstration receipt,
        and file for real with HMRC-recognised software or an accountant. Returns for periods ending
        after 31 March 2026 cannot be sent until HMRC publishes the computations taxonomy for them.
      </WarningText>

      <StartButton to={TASK_LIST} />
      <SavedReturnsLink />

      <WhatYoullNeed />
      <p className="govuk-body">
        Want an estimate first?{" "}
        <Link className="govuk-link" to="/calculator">
          Use the Corporation Tax calculator
        </Link>
        .
      </p>
    </TwoThirds>
  );
}
