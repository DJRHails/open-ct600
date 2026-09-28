import { Route, Routes } from "react-router";

import { Layout } from "@/components/Layout";
import { FilingRoutes } from "@/filing/FilingRoutes";
import { AccessibilityPage } from "@/pages/Accessibility";
import { CalculatorPage } from "@/pages/Calculator";
import { CookiesPage } from "@/pages/Cookies";
import { FreeFilingPage } from "@/pages/FreeFiling";
import { GuidePage, GuidesPage } from "@/pages/Guides";
import { HelpPage } from "@/pages/Help";
import { HomePage } from "@/pages/Home";
import { NotFoundPage } from "@/pages/NotFound";
import { PricingPage } from "@/pages/Pricing";
import { PrivacyPage } from "@/pages/Privacy";
import { TermsPage } from "@/pages/Terms";

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="file/*" element={<FilingRoutes />} />
        <Route path="calculator" element={<CalculatorPage />} />
        <Route path="pricing" element={<PricingPage />} />
        <Route path="guides" element={<GuidesPage />} />
        <Route path="guides/:slug" element={<GuidePage />} />
        <Route path="hmrc-free-filing" element={<FreeFilingPage />} />
        <Route path="help" element={<HelpPage />} />
        <Route path="privacy" element={<PrivacyPage />} />
        <Route path="cookies" element={<CookiesPage />} />
        <Route path="accessibility" element={<AccessibilityPage />} />
        <Route path="terms" element={<TermsPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
