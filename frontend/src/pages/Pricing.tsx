import { TwoThirds, usePageTitle } from "@/components/content";
import { REPOSITORY_URL } from "@/components/Layout";
import { StartButton } from "@/components/forms";
import { ExternalLink } from "@/content/guides";

export function PriceCard() {
  return (
    <div className="govuk-grid-row">
      <div className="govuk-grid-column-one-half">
        <p className="app-price govuk-!-margin-bottom-2">Free</p>
        <p className="govuk-body-l">No subscription and no fees. You can also host it yourself.</p>
        <h3 className="govuk-heading-s">What’s included</h3>
        <ul className="govuk-list govuk-list--bullet">
          <li>CT600 box figures for your accounting period</li>
          <li>Corporation Tax calculation, including marginal relief</li>
          <li>Periods that cross 1 April split between financial years</li>
          <li>Micro-entity or small company accounts and tax computations in iXBRL</li>
          <li>Supplementary pages CT600A to CT600P, including R&D and group relief</li>
          <li>Offline checks against HMRC’s own CT600 schema and business rules</li>
          <li>Drafts saved in your own browser, with no account needed</li>
        </ul>
      </div>
      <div className="govuk-grid-column-one-half">
        <h3 className="govuk-heading-s">What you’ll need</h3>
        <ul className="govuk-list govuk-list--bullet">
          <li>your company registration number, for example 01234567 or SC123456</li>
          <li>your company’s 10-digit Unique Taxpayer Reference (UTR)</li>
          <li>the start and end dates of your accounting period</li>
          <li>your profit and loss account and balance sheet figures</li>
        </ul>
        <div className="govuk-inset-text">
          Open CT600 is not on HMRC’s list of recognised software. It sends returns to HMRC only
          where whoever runs it has an HMRC vendor ID and has switched submission on; otherwise the
          final step gives you a demonstration receipt. HMRC has not yet published the computations
          taxonomy for periods ending after 31 March 2026, so those returns cannot be sent yet.
        </div>
        <StartButton to="/file" />
      </div>
    </div>
  );
}

type ComparisonRow = { feature: string; openCt600: string; accountant: string; software: string };

const COMPARISON: ComparisonRow[] = [
  {
    feature: "Cost",
    openCt600: "Free",
    accountant: "Typically £300 to £1,000 or more a year",
    software: "Often £10 to £30 a month, or a fee per return",
  },
  {
    feature: "Prepares your CT600 figures",
    openCt600: "Yes",
    accountant: "Yes",
    software: "Yes",
  },
  {
    feature: "Works out Corporation Tax and marginal relief",
    openCt600: "Yes",
    accountant: "Yes",
    software: "Yes",
  },
  {
    feature: "Micro-entity accounts",
    openCt600: "Yes",
    accountant: "Yes",
    software: "Yes",
  },
  {
    feature: "iXBRL tagged accounts and computations",
    openCt600: "Yes, for periods ending by 31 March 2026",
    accountant: "Yes",
    software: "Usually",
  },
  {
    feature: "Submits your return to HMRC",
    openCt600: "Only where the operator has an HMRC vendor ID and switches it on",
    accountant: "Yes",
    software: "Yes, if HMRC-recognised",
  },
  { feature: "Subscription needed", openCt600: "No", accountant: "No", software: "Often" },
  { feature: "Professional advice", openCt600: "No", accountant: "Yes", software: "No" },
  { feature: "Source code you can check", openCt600: "Yes", accountant: "No", software: "Rarely" },
];

function ComparisonTable() {
  return (
    <table className="govuk-table">
      <caption className="govuk-table__caption govuk-table__caption--m">How we compare</caption>
      <thead className="govuk-table__head">
        <tr className="govuk-table__row">
          <th scope="col" className="govuk-table__header">
            Feature
          </th>
          <th scope="col" className="govuk-table__header">
            Open CT600
          </th>
          <th scope="col" className="govuk-table__header">
            Accountant
          </th>
          <th scope="col" className="govuk-table__header">
            Commercial filing software
          </th>
        </tr>
      </thead>
      <tbody className="govuk-table__body">
        {COMPARISON.map((row) => (
          <tr className="govuk-table__row" key={row.feature}>
            <th scope="row" className="govuk-table__header">
              {row.feature}
            </th>
            <td className="govuk-table__cell">{row.openCt600}</td>
            <td className="govuk-table__cell">{row.accountant}</td>
            <td className="govuk-table__cell">{row.software}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function PricingPage() {
  usePageTitle("Pricing");

  return (
    <>
      <TwoThirds>
        <h1 className="govuk-heading-xl">Pricing</h1>
        <p className="govuk-body-l">
          Open CT600 is free and open source. There is nothing to pay, now or later.
        </p>
      </TwoThirds>
      <h2 className="govuk-heading-l">One price: free</h2>
      <PriceCard />
      <hr className="govuk-section-break govuk-section-break--l govuk-section-break--visible" />
      <ComparisonTable />
      <p className="govuk-body govuk-!-font-size-16">
        Accountant and software prices are typical ranges, not quotes. Check with providers.
      </p>
      <TwoThirds>
        <h2 className="govuk-heading-l">Host it yourself</h2>
        <p className="govuk-body">
          Open CT600 is released under the MIT licence. You can download the code, run it on your
          own computer and change it. The{" "}
          <ExternalLink href={REPOSITORY_URL}>source code is on GitHub</ExternalLink>.
        </p>
      </TwoThirds>
    </>
  );
}
