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
