import { Link } from "react-router";

import { usePageTitle } from "@/components/content";
import { GUIDES } from "@/content/guides";
import { FAQS, FaqList } from "@/pages/Help";
import { StartButton } from "@/components/forms";
import { PriceCard } from "@/pages/Pricing";

const HERO_CLASSES =
  "app-masthead govuk-!-padding-left-6 govuk-!-padding-right-6 govuk-!-margin-bottom-8";

function Hero() {
  return (
    <div className={HERO_CLASSES}>
      <div className="govuk-grid-row">
        <div className="govuk-grid-column-two-thirds">
          <span className="govuk-caption-l">HMRC free filing closed on 31 March 2026</span>
          <h1 className="govuk-heading-xl">Prepare your Company Tax Return for free</h1>
          <p className="govuk-body-l">
            Answer questions about your company in plain English. Open CT600 works out your
            Corporation Tax and fills in the boxes on your CT600 form.
          </p>
          <StartButton to="/file" />
          <p className="govuk-body">
            Or{" "}
            <Link className="govuk-link" to="/calculator">
              estimate your Corporation Tax with the calculator
            </Link>
            .
          </p>
          <div className="govuk-inset-text govuk-!-margin-bottom-0">
            Open CT600 is free, open-source software. It is not on HMRC’s list of recognised
            software. It can send your return to HMRC only where whoever runs it has an HMRC vendor
            ID and has switched submission on; otherwise it gives you a demonstration receipt and
            nothing is sent.
          </div>
        </div>
      </div>
    </div>
  );
}

const SUMMARY = [
  {
    title: "Answer simple questions",
    text: "Tell us about your company’s income, costs and balance sheet. No tax jargon.",
  },
  {
    title: "We work out the figures",
    text: "Your Corporation Tax, marginal relief and every CT600 box are calculated for you.",
  },
  {
    title: "Check before you file",
    text:
      "Review your return against HMRC’s own rules, download the accounts, computations and " +
      "CT600, then send it to HMRC where submission is switched on.",
  },
];

function Summary() {
  return (
    <div className="govuk-grid-row">
      {SUMMARY.map((item) => (
        <div className="govuk-grid-column-one-third" key={item.title}>
          <h2 className="govuk-heading-m">{item.title}</h2>
          <p className="govuk-body">{item.text}</p>
        </div>
      ))}
    </div>
  );
}

const STEPS = [
  {
    title: "Enter your details",
    text: "Give your company details, accounting period and figures from your accounts.",
  },
  {
    title: "We work out your tax",
    text:
      "Open CT600 calculates your Corporation Tax, splits periods that cross 1 April and " +
      "prepares micro-entity accounts figures.",
  },
  {
    title: "Check and submit",
    text:
      "Check your answers against HMRC’s rules. Where submission is switched on, send a test " +
      "to HMRC’s Test in Live service or file the return with the company’s Government Gateway " +
      "sign in. Otherwise you get a demonstration receipt and nothing is sent to HMRC.",
  },
];

function HowItWorks() {
  return (
    <>
      <h2 className="govuk-heading-l">How it works</h2>
      <p className="govuk-body">Prepare your CT600 in 3 steps.</p>
      <ol className="govuk-list">
        {STEPS.map((step, index) => (
          <li key={step.title}>
            <h3 className="govuk-heading-m govuk-!-margin-bottom-2">
              <span className="app-step-number" aria-hidden="true">
                {index + 1}
              </span>
              {step.title}
            </h3>
            <p className="govuk-body">{step.text}</p>
          </li>
        ))}
      </ol>
    </>
  );
}

const FEATURES = [
  {
    title: "Automatic tax calculation",
    text: "Corporation Tax worked out at the right rates for each financial year.",
  },
  {
    title: "Marginal relief",
    text: "Relief for profits between £50,000 and £250,000, adjusted for associated companies.",
  },
  {
    title: "Micro-entity accounts",
    text: "Profit and loss and balance sheet figures in the micro-entity format, ready to check.",
  },
  {
    title: "Guided questions",
    text: "Plain English questions, a few at a time. You do not need to know the CT600 boxes.",
  },
  {
    title: "Free and open source",
    text: "No fees and no subscription. The code is public under the MIT licence.",
  },
  {
    title: "Your data stays with you",
    text:
      "No accounts to create. Your draft is saved in your own browser, and a Government " +
      "Gateway password is passed straight to HMRC, never stored.",
  },
];

function Features() {
  return (
    <>
      <h2 className="govuk-heading-l">Features</h2>
      <div className="govuk-grid-row">
        {FEATURES.map((feature) => (
          <div className="govuk-grid-column-one-third" key={feature.title}>
            <h3 className="govuk-heading-s">{feature.title}</h3>
            <p className="govuk-body">{feature.text}</p>
          </div>
        ))}
      </div>
    </>
  );
}

function GuidesTeaser() {
  return (
    <>
      <h2 className="govuk-heading-l">Guides</h2>
      <div className="govuk-grid-row">
        {GUIDES.map((guide) => (
          <div className="govuk-grid-column-one-half" key={guide.slug}>
            <h3 className="govuk-heading-s govuk-!-margin-bottom-2">
              <Link className="govuk-link" to={`/guides/${guide.slug}`}>
                {guide.title}
              </Link>
            </h3>
            <p className="govuk-body">{guide.summary}</p>
          </div>
        ))}
      </div>
      <p className="govuk-body">
        <Link className="govuk-link" to="/guides">
          See all guides
        </Link>
      </p>
    </>
  );
}

function SectionBreak() {
  return (
    <hr className="govuk-section-break govuk-section-break--xl govuk-section-break--visible" />
  );
}

export function HomePage() {
  usePageTitle("Prepare your Company Tax Return for free");

  return (
    <>
      <Hero />
      <Summary />
      <SectionBreak />
      <HowItWorks />
      <SectionBreak />
      <Features />
      <SectionBreak />
      <h2 className="govuk-heading-l">Pricing</h2>
      <PriceCard />
      <SectionBreak />
      <div className="govuk-grid-row">
        <div className="govuk-grid-column-two-thirds">
          <h2 className="govuk-heading-l">Frequently asked questions</h2>
          <FaqList faqs={FAQS.slice(0, 6)} />
          <p className="govuk-body">
            <Link className="govuk-link" to="/help">
              More help and answers
            </Link>
          </p>
        </div>
      </div>
      <SectionBreak />
      <GuidesTeaser />
    </>
  );
}
