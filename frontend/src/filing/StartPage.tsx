import { Link } from "react-router";

import { TwoThirds, usePageTitle, WarningText } from "@/components/content";
import { StartButton } from "@/components/forms";
import { useDraft } from "@/filing/draft";
import { RETURNS, TASK_LIST } from "@/filing/paths";

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

      <h2 className="govuk-heading-m">Before you start</h2>
      <p className="govuk-body">You'll need your company's:</p>
      <ul className="govuk-list govuk-list--bullet">
        <li>company registration number, like 01234567 or SC123456</li>
        <li>Unique Taxpayer Reference (UTR), which is 10 digits</li>
        <li>accounting period start and end dates</li>
        <li>profit and loss account and balance sheet figures</li>
      </ul>
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
