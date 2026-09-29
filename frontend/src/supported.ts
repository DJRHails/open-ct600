/**
 * Tell GOV.UK Frontend's styles and components that JavaScript is running in a browser they
 * support. This runs from the app bundle, before React renders any component, instead of an
 * inline script in index.html, so the page works under a Content-Security-Policy that forbids
 * inline scripts.
 */
export function markGovukFrontendSupported(body: HTMLElement): void {
  body.classList.add("js-enabled", "govuk-frontend-supported");
}
