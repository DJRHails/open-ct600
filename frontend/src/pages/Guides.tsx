import { Link, useParams } from "react-router";

import { BackLink, TwoThirds, usePageTitle } from "@/components/content";
import { GUIDES, type Guide } from "@/content/guides";
import { NotFoundPage } from "@/pages/NotFound";

export function GuidesPage() {
  usePageTitle("Guides");

  return (
    <TwoThirds>
      <h1 className="govuk-heading-xl">Guides</h1>
      <p className="govuk-body-l">
        Plain English guides to Corporation Tax and the CT600 Company Tax Return.
      </p>
      <ul className="govuk-list">
        {GUIDES.map((guide) => (
          <li key={guide.slug} className="govuk-!-margin-bottom-6">
            <h2 className="govuk-heading-m govuk-!-margin-bottom-2">
              <Link className="govuk-link" to={`/guides/${guide.slug}`}>
                {guide.title}
              </Link>
            </h2>
            <p className="govuk-body">{guide.summary}</p>
          </li>
        ))}
      </ul>
    </TwoThirds>
  );
}

function GuideArticle({ guide }: { guide: Guide }) {
  usePageTitle(guide.title);
  const related = GUIDES.filter((other) => other.slug !== guide.slug);

  return (
    <>
      <BackLink to="/guides">All guides</BackLink>
      <TwoThirds>
        <span className="govuk-caption-l">Guide</span>
        <h1 className="govuk-heading-xl">{guide.title}</h1>
        <p className="govuk-body-l">{guide.summary}</p>
        {guide.body}
        <hr className="govuk-section-break govuk-section-break--l govuk-section-break--visible" />
        <p className="govuk-body govuk-!-font-size-16">
          This guide is general information, not tax advice. Check the latest rules on GOV.UK or ask
          an accountant if you are unsure.
        </p>
        <h2 className="govuk-heading-s">Related guides</h2>
        <ul className="govuk-list">
          {related.map((other) => (
            <li key={other.slug}>
              <Link className="govuk-link" to={`/guides/${other.slug}`}>
                {other.title}
              </Link>
            </li>
          ))}
        </ul>
      </TwoThirds>
    </>
  );
}

export function GuidePage() {
  const { slug } = useParams();
  const guide = GUIDES.find((candidate) => candidate.slug === slug);
  if (!guide) return <NotFoundPage />;
  return <GuideArticle key={guide.slug} guide={guide} />;
}
