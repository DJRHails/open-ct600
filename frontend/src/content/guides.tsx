import type { ReactNode } from "react";
import { Link } from "react-router";

export type Guide = { slug: string; title: string; summary: string; body: ReactNode };

export const RECOGNISED_SOFTWARE_URL =
  "https://www.gov.uk/government/publications/corporation-tax-commercial-software-suppliers/" +
  "corporation-tax-commercial-software-suppliers";

export function ExternalLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <a className="govuk-link" href={href} rel="noreferrer noopener" target="_blank">
      {children} (opens in new tab)
    </a>
  );
}

function HowToFileBody() {
  return (
    <>
      <h2 className="govuk-heading-m">Before you start</h2>
      <p className="govuk-body">You will need:</p>
      <ul className="govuk-list govuk-list--bullet">
        <li>your company registration number, which is 8 characters, for example 01234567</li>
        <li>your company’s 10-digit Unique Taxpayer Reference (UTR)</li>
        <li>the start and end dates of the accounting period</li>
        <li>your profit and loss account and balance sheet figures</li>
      </ul>
      <h2 className="govuk-heading-m">Check your accounting period</h2>
      <p className="govuk-body">
        An accounting period for Corporation Tax cannot be longer than 12 months. If your company’s
        accounts cover a longer period, you must split it into 2 accounting periods and file a
        return for each.
      </p>
      <h2 className="govuk-heading-m">Know your deadlines</h2>
      <ul className="govuk-list govuk-list--bullet">
        <li>Pay your Corporation Tax 9 months and 1 day after the end of the accounting period.</li>
        <li>File your CT600 return 12 months after the end of the accounting period.</li>
      </ul>
      <p className="govuk-body">
        Paying and filing are separate deadlines. You usually have to pay before you file.
      </p>
      <h2 className="govuk-heading-m">Prepare your return</h2>
      <ol className="govuk-list govuk-list--number">
        <li>Prepare your company’s accounts for the period.</li>
        <li>
          Work out your taxable profits. Start with your accounting profit and add back costs that
          are not allowed for tax, such as client entertaining and depreciation.
        </li>
        <li>
          Work out the Corporation Tax due. Use the rate for each financial year the period falls
          in, including any marginal relief.
        </li>
        <li>Fill in the boxes on the CT600 form.</li>
      </ol>
      <p className="govuk-body">
        Open CT600 can help with all 4 steps: it prepares micro-entity or small company accounts and
        your tax computations in iXBRL. You can also try the{" "}
        <Link className="govuk-link" to="/calculator">
          Corporation Tax calculator
        </Link>
        .
      </p>
      <h2 className="govuk-heading-m">File your return</h2>
      <p className="govuk-body">
        You must file your return online with your accounts and tax computations, tagged in a format
        called iXBRL. Since HMRC’s free filing service closed on 31 March 2026, you need software
        that can send returns to HMRC, such as{" "}
        <ExternalLink href={RECOGNISED_SOFTWARE_URL}>HMRC-recognised software</ExternalLink>, or an
        accountant to do this.
      </p>
      <div className="govuk-inset-text">
        Open CT600 is not on HMRC’s list of recognised software. It can send your return to HMRC
        only where whoever runs it has an HMRC vendor ID and has switched submission on. Returns for
        periods ending after 31 March 2026 cannot be sent until HMRC publishes the computations
        taxonomy for them.
      </div>
    </>
  );
}

function DormantBody() {
  return (
    <>
      <h2 className="govuk-heading-m">What dormant means for Corporation Tax</h2>
      <p className="govuk-body">
        Your company is usually dormant for Corporation Tax if it is not trading and has no other
        income, such as bank interest or investment income.
      </p>
      <h2 className="govuk-heading-m">If HMRC has sent you a notice to file</h2>
      <p className="govuk-body">
        If HMRC has sent your company a ‘notice to deliver a Company Tax Return’, you must file a
        return, even if the company is dormant. For a dormant company this is a nil return, showing
        no income and no tax to pay.
      </p>
      <p className="govuk-body">
        The usual deadline still applies: 12 months after the end of the accounting period. Late
        filing penalties apply to nil returns too.
      </p>
      <h2 className="govuk-heading-m">Stop HMRC sending notices</h2>
      <p className="govuk-body">
        You can tell HMRC that your company is dormant. HMRC will then stop sending notices to file
        until the company starts trading again. You must tell HMRC when that happens.
      </p>
      <p className="govuk-body">
        Read more about{" "}
        <ExternalLink href="https://www.gov.uk/dormant-company">
          dormant companies on GOV.UK
        </ExternalLink>
        .
      </p>
      <h2 className="govuk-heading-m">Companies House</h2>
      <p className="govuk-body">
        A dormant company must still file annual accounts and a confirmation statement with
        Companies House. This is separate from Corporation Tax.
      </p>
    </>
  );
}

function PenaltiesTable() {
  const rows = [
    ["1 day", "£100"],
    ["3 months", "Another £100"],
    ["6 months", "HMRC estimates your tax bill and adds a penalty of 10% of the unpaid tax"],
    ["12 months", "Another 10% of any unpaid tax"],
  ];
  return (
    <table className="govuk-table">
      <caption className="govuk-table__caption govuk-table__caption--m">
        Penalties for filing your return late
      </caption>
      <thead className="govuk-table__head">
        <tr className="govuk-table__row">
          <th scope="col" className="govuk-table__header">
            Time after your deadline
          </th>
          <th scope="col" className="govuk-table__header">
            Penalty
          </th>
        </tr>
      </thead>
      <tbody className="govuk-table__body">
        {rows.map(([late, penalty]) => (
          <tr className="govuk-table__row" key={late}>
            <th scope="row" className="govuk-table__header">
              {late}
            </th>
            <td className="govuk-table__cell">{penalty}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function PenaltiesBody() {
  return (
    <>
      <p className="govuk-body">
        Your CT600 return is due 12 months after the end of your accounting period. HMRC charges a
        penalty if you miss this deadline, even if you have no tax to pay.
      </p>
      <PenaltiesTable />
      <p className="govuk-body">
        If your return is late 3 times in a row, each £100 penalty rises to £500.
      </p>
      <h2 className="govuk-heading-m">Paying late</h2>
      <p className="govuk-body">
        Corporation Tax is normally due 9 months and 1 day after the end of your accounting period.
        HMRC charges interest on tax you pay late, from the day after the payment was due.
      </p>
      <h2 className="govuk-heading-m">If you have a reasonable excuse</h2>
      <p className="govuk-body">
        You can appeal against a penalty if you had a reasonable excuse for filing late, for example
        a serious illness. HMRC decides whether your excuse is reasonable.
      </p>
      <h2 className="govuk-heading-m">Avoid penalties</h2>
      <ul className="govuk-list govuk-list--bullet">
        <li>Note both your payment and filing deadlines as soon as your accounting period ends.</li>
        <li>
          Work out your tax early using the{" "}
          <Link className="govuk-link" to="/calculator">
            Corporation Tax calculator
          </Link>
          .
        </li>
        <li>File a nil return if HMRC has asked for one, even if your company is dormant.</li>
      </ul>
    </>
  );
}

function MarginalReliefExample() {
  return (
    <>
      <h2 className="govuk-heading-m">Worked example</h2>
      <p className="govuk-body">
        Your company has taxable profits of £100,000 for the year to 31 March 2026. It has no
        associated companies and no exempt distributions, so its augmented profits are also
        £100,000.
      </p>
      <ol className="govuk-list govuk-list--number">
        <li>Tax at the main rate: £100,000 × 25% = £25,000.</li>
        <li>Marginal relief: 3/200 × (£250,000 − £100,000) × £100,000 / £100,000 = £2,250.</li>
        <li>Corporation Tax due: £25,000 − £2,250 = £22,750.</li>
      </ol>
      <p className="govuk-body">This is an effective rate of 22.75%.</p>
      <h2 className="govuk-heading-m">Associated companies</h2>
      <p className="govuk-body">
        If your company has associated companies, divide both limits by the number of associated
        companies plus 1. With 1 associated company, the limits become £25,000 and £125,000.
      </p>
      <h2 className="govuk-heading-m">Short accounting periods</h2>
      <p className="govuk-body">
        If your accounting period is shorter than 12 months, the limits are reduced in proportion.
        For a 6-month period, they are roughly halved.
      </p>
      <h2 className="govuk-heading-m">Periods that cross 1 April</h2>
      <p className="govuk-body">
        The financial year runs from 1 April to 31 March. If your accounting period includes 1
        April, your profits are split between the 2 financial years by the number of days in each,
        and the tax is worked out separately for each part. Before 1 April 2023 there was a single
        rate of 19% and no marginal relief.
      </p>
    </>
  );
}

function MarginalReliefBody() {
  return (
    <>
      <h2 className="govuk-heading-m">Corporation Tax rates from 1 April 2023</h2>
      <ul className="govuk-list govuk-list--bullet">
        <li>Profits of £50,000 or less: small profits rate of 19%.</li>
        <li>Profits over £250,000: main rate of 25%.</li>
        <li>Profits between £50,000 and £250,000: main rate, reduced by marginal relief.</li>
      </ul>
      <p className="govuk-body">
        Marginal relief means the effective rate rises gradually from 19% to 25%, rather than
        jumping when profits pass £50,000.
      </p>
      <h2 className="govuk-heading-m">How marginal relief is worked out</h2>
      <div className="govuk-inset-text">
        Marginal relief = 3/200 × (upper limit − augmented profits) × taxable profits / augmented
        profits
      </div>
      <p className="govuk-body">
        The upper limit is £250,000. Augmented profits are your taxable profits plus any exempt
        distributions, such as dividends from companies outside your group.
      </p>
      <MarginalReliefExample />
    </>
  );
}

export const GUIDES: Guide[] = [
  {
    slug: "how-to-file-a-ct600",
    title: "How to file a CT600 Company Tax Return",
    summary: "What you need, when it is due, and the steps to prepare and file your return.",
    body: <HowToFileBody />,
  },
  {
    slug: "dormant-companies",
    title: "Company Tax Returns for dormant companies",
    summary: "When a company that is not trading still has to file, and how to tell HMRC.",
    body: <DormantBody />,
  },
  {
    slug: "late-filing-penalties",
    title: "Penalties for filing your CT600 late",
    summary: "The penalties and interest HMRC charges if you file or pay late.",
    body: <PenaltiesBody />,
  },
  {
    slug: "marginal-relief",
    title: "Corporation Tax marginal relief explained",
    summary: "How the 19% and 25% rates work, with a worked example.",
    body: <MarginalReliefBody />,
  },
];
