import { Link } from "react-router";

import { TwoThirds, usePageTitle, WarningText } from "@/components/content";
import { StartButton } from "@/components/forms";
import { TASK_LIST } from "@/filing/paths";

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
        It takes around 20 minutes. Your answers are saved in this browser as you go.
      </p>

      <WarningText>
        This service only sends returns to HMRC where whoever runs it has switched submission on.
        Otherwise you can check your return and get a demonstration receipt, and file for real with
        HMRC-recognised software or an accountant.
      </WarningText>

      <StartButton to={TASK_LIST} />

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
