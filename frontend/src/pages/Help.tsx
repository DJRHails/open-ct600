import type { ReactNode } from "react";
import { Link } from "react-router";

import { TwoThirds, usePageTitle } from "@/components/content";
import { REPOSITORY_URL } from "@/components/Layout";
import { ExternalLink, RECOGNISED_SOFTWARE_URL } from "@/content/guides";

export type Faq = { question: string; answer: ReactNode };

export const FAQS: Faq[] = [
  {
    question: "What is a CT600?",
    answer: (
      <p className="govuk-body">
        The CT600 is the Company Tax Return form. It tells HMRC your company’s taxable profits and
        how much Corporation Tax it owes for an accounting period.
      </p>
    ),
  },
  {
    question: "Who needs to file a CT600?",
    answer: (
      <p className="govuk-body">
        Your company must file a return if it is liable for Corporation Tax, or if HMRC has sent it
        a ‘notice to deliver a Company Tax Return’. This applies even if the company made a loss or
        did not trade.
      </p>
    ),
  },
  {
    question: "Can I file my return with Open CT600?",
    answer: (
      <>
        <p className="govuk-body">
          Only where whoever runs the service has switched submission on. Sending returns to HMRC
          needs an HMRC vendor ID, which HMRC gives to software developers, and the operator has to
          enable it. Where it is on, you can send a test to HMRC’s Test in Live service, which
          checks the return without filing it, or file it for real with the company’s Government
          Gateway user ID and password.
        </p>
        <p className="govuk-body">
          Where it is off, the last step gives you a demonstration receipt and nothing is sent to
          HMRC. You can still download the return, accounts and computations and file them with{" "}
          <ExternalLink href={RECOGNISED_SOFTWARE_URL}>HMRC-recognised software</ExternalLink> or an
          accountant.
        </p>
        <p className="govuk-body">
          Returns for periods ending after 31 March 2026 cannot be sent yet. HMRC needs tax
          computations in its computations taxonomy, and it has not yet published the 2025 version
          that covers those periods.
        </p>
      </>
    ),
  },
  {
    question: "Is Open CT600 recognised by HMRC?",
    answer: (
      <p className="govuk-body">
        No. It is not on HMRC’s list of recognised Corporation Tax software, and HMRC has not
        approved or endorsed it. It checks returns against HMRC’s published schema and business
        rules before sending them, but HMRC decides whether to accept each return.
      </p>
    ),
  },
  {
    question: "What happened to HMRC’s free filing service?",
    answer: (
      <p className="govuk-body">
        HMRC and Companies House’s joint online service for company accounts and tax returns closed
        on 31 March 2026. Read{" "}
        <Link className="govuk-link" to="/hmrc-free-filing">
          what the closure means for you
        </Link>
        .
      </p>
    ),
  },
  {
    question: "How much does it cost?",
    answer: (
      <p className="govuk-body">
        Nothing. Open CT600 is free and open source. There is no subscription and no fee.
      </p>
    ),
  },
  {
    question: "Does it file my accounts with Companies House?",
    answer: (
      <p className="govuk-body">
        No. Filing annual accounts with Companies House is a separate obligation, with its own
        deadline.
      </p>
    ),
  },
  {
    question: "Do I need an account?",
    answer: (
      <p className="govuk-body">
        No. There are no accounts to create. Your returns are saved in your own browser, and you can
        export one to a file to carry on in another browser. To send a return to HMRC you enter the
        company’s Government Gateway user ID and password, which are passed straight to HMRC and
        never stored.
      </p>
    ),
  },
  {
    question: "Do I need to know about tax?",
    answer: (
      <p className="govuk-body">
        No. You answer questions about your company in plain English and we work out the figures.
        You will need your company registration number, Unique Taxpayer Reference and your accounts.
      </p>
    ),
  },
  {
    question: "Is this tax advice?",
    answer: (
      <p className="govuk-body">
        No. Always check the figures. Ask an accountant if your company’s affairs are complex.
      </p>
    ),
  },
];

export function FaqList({ faqs }: { faqs: Faq[] }) {
  return (
    <>
      {faqs.map((faq) => (
        <details className="govuk-details" key={faq.question}>
          <summary className="govuk-details__summary">
            <span className="govuk-details__summary-text">{faq.question}</span>
          </summary>
          <div className="govuk-details__text">{faq.answer}</div>
        </details>
      ))}
    </>
  );
}

const HMRC_ENQUIRIES_URL =
  "https://www.gov.uk/government/organisations/hm-revenue-customs/contact/" +
  "corporation-tax-enquiries";

function GetHelp() {
  return (
    <>
      <h2 className="govuk-heading-l">Get help</h2>
      <p className="govuk-body">
        To report a problem with Open CT600 or ask a question about it,{" "}
        <ExternalLink href={`${REPOSITORY_URL}/issues`}>open an issue on GitHub</ExternalLink>. Do
        not include your company’s real figures or tax references.
      </p>
      <p className="govuk-body">
        We cannot help with your tax affairs. For questions about your company’s Corporation Tax,
        contact{" "}
        <ExternalLink href={HMRC_ENQUIRIES_URL}>HMRC Corporation Tax enquiries</ExternalLink> or an
        accountant.
      </p>
    </>
  );
}

export function HelpPage() {
  usePageTitle("Help and frequently asked questions");

  return (
    <TwoThirds>
      <h1 className="govuk-heading-xl">Help and frequently asked questions</h1>
      <p className="govuk-body-l">
        Answers to common questions about Open CT600 and Company Tax Returns.
      </p>
      <p className="govuk-body">
        Our{" "}
        <Link className="govuk-link" to="/guides">
          guides
        </Link>{" "}
        explain deadlines, penalties, dormant companies and marginal relief in more detail.
      </p>
      <h2 className="govuk-heading-l">Frequently asked questions</h2>
      <FaqList faqs={FAQS} />
      <GetHelp />
    </TwoThirds>
  );
}
