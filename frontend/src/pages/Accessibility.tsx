import { TwoThirds, usePageTitle } from "@/components/content";
import { REPOSITORY_URL, SERVICE_NAME } from "@/components/Layout";
import { ExternalLink } from "@/content/guides";

function UsingThisService() {
  return (
    <>
      <p className="govuk-body">
        This accessibility statement applies to {SERVICE_NAME}. It is run by the {SERVICE_NAME}{" "}
        open-source project. We want as many people as possible to be able to use it. For example,
        you should be able to:
      </p>
      <ul className="govuk-list govuk-list--bullet">
        <li>change colours, contrast levels and fonts using browser or device settings</li>
        <li>zoom in up to 400% without the text spilling off the screen</li>
        <li>navigate the whole service using just a keyboard or speech recognition software</li>
        <li>listen to the service using a screen reader</li>
      </ul>
      <p className="govuk-body">
        We have also made the text as simple as possible to understand.{" "}
        <ExternalLink href="https://mcmw.abilitynet.org.uk/">AbilityNet</ExternalLink> has advice on
        making your device easier to use if you have a disability.
      </p>
    </>
  );
}

function ComplianceStatus() {
  return (
    <>
      <h2 className="govuk-heading-l">Compliance status</h2>
      <p className="govuk-body">
        We aim to meet the{" "}
        <ExternalLink href="https://www.w3.org/TR/WCAG22/">
          Web Content Accessibility Guidelines version 2.2
        </ExternalLink>{" "}
        AA standard. The service is built with GOV.UK Frontend, which is designed and tested to meet
        this standard.
      </p>
      <p className="govuk-body">
        This service is partially compliant, because it has not been independently audited.
      </p>
      <h2 className="govuk-heading-l">Known limitations</h2>
      <ul className="govuk-list govuk-list--bullet">
        <li>The service has not had an independent accessibility audit.</li>
        <li>We have not tested it with a full range of assistive technologies.</li>
        <li>
          The service uses the Arial typeface, not the GOV.UK typeface, which is reserved for GOV.UK
          services.
        </li>
      </ul>
    </>
  );
}

export function AccessibilityPage() {
  usePageTitle("Accessibility statement");
  const issues = `${REPOSITORY_URL}/issues`;

  return (
    <TwoThirds>
      <h1 className="govuk-heading-xl">Accessibility statement for {SERVICE_NAME}</h1>
      <UsingThisService />
      <ComplianceStatus />
      <h2 className="govuk-heading-l">Reporting accessibility problems</h2>
      <p className="govuk-body">
        If you find a problem not listed on this page, or you think we are not meeting accessibility
        requirements, <ExternalLink href={issues}>open an issue on GitHub</ExternalLink>. Tell us
        the web address of the page, what you were trying to do and what assistive technology you
        use, if any.
      </p>
      <h2 className="govuk-heading-l">Preparation of this statement</h2>
      <p className="govuk-body">
        This statement was prepared on 28 September 2026. It is based on a self-assessment by the
        project’s developers.
      </p>
    </TwoThirds>
  );
}
