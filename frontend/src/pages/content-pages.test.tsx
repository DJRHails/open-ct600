import { render, screen } from "@testing-library/react";
import type { ComponentType } from "react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it } from "vitest";

import { AccessibilityPage } from "@/pages/Accessibility";
import { CookiesPage } from "@/pages/Cookies";
import { FreeFilingPage } from "@/pages/FreeFiling";
import { GuidePage, GuidesPage } from "@/pages/Guides";
import { HelpPage } from "@/pages/Help";
import { HomePage } from "@/pages/Home";
import { NotFoundPage } from "@/pages/NotFound";
import { PricingPage } from "@/pages/Pricing";
import { PrivacyPage } from "@/pages/Privacy";
import { TermsPage } from "@/pages/Terms";

const PAGES: [string, ComponentType, string][] = [
  ["home", HomePage, "Prepare your Company Tax Return for free"],
  ["pricing", PricingPage, "Pricing"],
  ["HMRC free filing", FreeFilingPage, "HMRC’s free Company Tax Return filing has closed"],
  ["guides index", GuidesPage, "Guides"],
  ["help", HelpPage, "Help and frequently asked questions"],
  ["privacy", PrivacyPage, "Privacy notice"],
  ["terms", TermsPage, "Terms of use"],
  ["cookies", CookiesPage, "Cookies"],
  ["accessibility", AccessibilityPage, "Accessibility statement for Open CT600"],
  ["not found", NotFoundPage, "Page not found"],
];

function renderGuide(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/guides/:slug" element={<GuidePage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("content pages", () => {
  it.each(PAGES)("renders the %s page heading", (_name, Page, heading) => {
    render(
      <MemoryRouter>
        <Page />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(heading);
  });

  it.each(PAGES)("does not claim the %s page's service never submits to HMRC", (_n, Page) => {
    render(
      <MemoryRouter>
        <Page />
      </MemoryRouter>,
    );
    expect(document.body).not.toHaveTextContent(/does not (submit|send) (returns|anything)/i);
  });

  it("says Government Gateway credentials go straight to HMRC and are never kept", () => {
    render(
      <MemoryRouter>
        <PrivacyPage />
      </MemoryRouter>,
    );
    const section = screen.getByRole("heading", { name: "Sending your return to HMRC" });
    expect(section.nextElementSibling).toHaveTextContent(
      /passed straight to HMRC .* never stored, in your browser or on the server, and never logged/,
    );
  });

  it("explains when a return can be sent to HMRC", () => {
    render(
      <MemoryRouter>
        <HelpPage />
      </MemoryRouter>,
    );
    expect(document.body).toHaveTextContent(/needs an HMRC vendor ID/);
    expect(document.body).toHaveTextContent(/Test in Live/);
    expect(document.body).toHaveTextContent(
      /periods ending after 31 March 2026 cannot be sent yet/,
    );
  });

  it("renders a guide by its slug", () => {
    renderGuide("/guides/marginal-relief");
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Corporation Tax marginal relief explained",
    );
  });

  it("renders page not found for an unknown guide slug", () => {
    renderGuide("/guides/no-such-guide");
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Page not found");
  });
});
