import { ServiceNavigation } from "govuk-frontend";
import { useEffect, useRef } from "react";
import { Link, Outlet, useLocation, useMatch } from "react-router";

export const SERVICE_NAME = "Open CT600";
export const REPOSITORY_URL = "https://github.com/DJRHails/open-ct600";

const NAVIGATION = [
  { to: "/file", label: "File a return" },
  { to: "/calculator", label: "Tax calculator" },
  { to: "/pricing", label: "Pricing" },
  { to: "/guides", label: "Guides" },
  { to: "/hmrc-free-filing", label: "HMRC free filing" },
  { to: "/sign-up", label: "Sign up" },
];

function Header() {
  const navigation = useRef<HTMLElement>(null);
  const toggle = useRef<ServiceNavigation>(null);

  useEffect(() => {
    if (navigation.current && !toggle.current) {
      toggle.current = new ServiceNavigation(navigation.current);
    }
  }, []);

  return (
    <header className="app-header">
      <div className="govuk-generic-header">
        <div className="govuk-generic-header__container govuk-width-container">
          <div className="govuk-generic-header__logo">
            <Link to="/" className="govuk-generic-header__homepage-link">
              <span className="app-header__logo-mark" aria-hidden="true">
                CT
              </span>
              {SERVICE_NAME}
            </Link>
          </div>
        </div>
      </div>
      <section
        aria-label="Menu"
        className="govuk-service-navigation"
        data-module="govuk-service-navigation"
        ref={navigation}
      >
        <div className="govuk-width-container">
          <div className="govuk-service-navigation__container">
            <nav aria-label="Menu" className="govuk-service-navigation__wrapper">
              <button
                type="button"
                className="govuk-service-navigation__toggle govuk-js-service-navigation-toggle"
                aria-controls="navigation"
                hidden
              >
                Menu
              </button>
              <ul className="govuk-service-navigation__list" id="navigation">
                {NAVIGATION.map((item) => (
                  <NavigationItem key={item.to} to={item.to} label={item.label} />
                ))}
              </ul>
            </nav>
          </div>
        </div>
      </section>
    </header>
  );
}

function NavigationItem({ to, label }: { to: string; label: string }) {
  const isActive = useMatch({ path: to, end: false }) !== null;
  const itemClass = isActive
    ? "govuk-service-navigation__item govuk-service-navigation__item--active"
    : "govuk-service-navigation__item";

  return (
    <li className={itemClass}>
      <Link
        className="govuk-service-navigation__link"
        to={to}
        aria-current={isActive ? "page" : undefined}
      >
        {isActive ? (
          <strong className="govuk-service-navigation__active-fallback">{label}</strong>
        ) : (
          label
        )}
      </Link>
    </li>
  );
}

function PhaseBanner() {
  return (
    <div className="govuk-phase-banner">
      <p className="govuk-phase-banner__content">
        <strong className="govuk-tag govuk-phase-banner__content__tag">Demo</strong>
        <span className="govuk-phase-banner__text">
          This is an open-source demonstration. It does not submit returns to HMRC.{" "}
          <a className="govuk-link" href={REPOSITORY_URL}>
            View the source code
          </a>
          .
        </span>
      </p>
    </div>
  );
}

const FOOTER_LINKS = [
  { to: "/help", label: "Help" },
  { to: "/privacy", label: "Privacy" },
  { to: "/cookies", label: "Cookies" },
  { to: "/accessibility", label: "Accessibility statement" },
  { to: "/terms", label: "Terms and conditions" },
];

function Footer() {
  return (
    <footer className="govuk-footer app-no-print">
      <div className="govuk-width-container">
        <div className="govuk-footer__meta">
          <div className="govuk-footer__meta-item govuk-footer__meta-item--grow">
            <h2 className="govuk-visually-hidden">Support links</h2>
            <ul className="govuk-footer__inline-list">
              {FOOTER_LINKS.map((item) => (
                <li className="govuk-footer__inline-list-item" key={item.to}>
                  <Link className="govuk-footer__link" to={item.to}>
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
            <span className="govuk-footer__licence-description">
              {SERVICE_NAME} is open source under the{" "}
              <a className="govuk-footer__link" href={`${REPOSITORY_URL}/blob/main/LICENSE`}>
                MIT licence
              </a>
              . It is not affiliated with HMRC or GOV.UK, and it is not tax advice.
            </span>
          </div>
          <div className="govuk-footer__meta-item">
            <a className="govuk-footer__link" href={REPOSITORY_URL}>
              Source code on GitHub
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}

/** Move focus to the top of the page on navigation, as a full page load would. */
function useResetFocusOnNavigate() {
  const { pathname } = useLocation();
  const previous = useRef(pathname);

  useEffect(() => {
    if (previous.current === pathname) return;
    previous.current = pathname;
    window.scrollTo(0, 0);
    document.getElementById("top")?.focus();
  }, [pathname]);
}

export function Layout() {
  useResetFocusOnNavigate();

  return (
    <>
      <span id="top" tabIndex={-1} />
      <a href="#main-content" className="govuk-skip-link" data-module="govuk-skip-link">
        Skip to main content
      </a>
      <Header />
      <div className="govuk-width-container">
        <PhaseBanner />
        <main className="govuk-main-wrapper" id="main-content" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
      <Footer />
    </>
  );
}
