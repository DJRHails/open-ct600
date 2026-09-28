import { Route, Routes } from "react-router";

import { AccountingPeriodPage } from "@/filing/AccountingPeriodPage";
import { AmountSectionPage } from "@/filing/AmountSectionPage";
import { CheckAnswersPage } from "@/filing/CheckAnswersPage";
import { CompanyDetailsPage } from "@/filing/CompanyDetailsPage";
import { ConfirmationPage } from "@/filing/ConfirmationPage";
import { DeclarationPage } from "@/filing/DeclarationPage";
import { DraftProvider } from "@/filing/draft";
import { BALANCE_SHEET, PROFIT_AND_LOSS, TAX_ADJUSTMENTS } from "@/filing/model";
import { StartPage } from "@/filing/StartPage";
import { TaskListPage } from "@/filing/TaskListPage";
import { NotFoundPage } from "@/pages/NotFound";

export function FilingRoutes() {
  return (
    <DraftProvider>
      <Routes>
        <Route index element={<StartPage />} />
        <Route path="tasks" element={<TaskListPage />} />
        <Route path="company-details" element={<CompanyDetailsPage />} />
        <Route path="accounting-period" element={<AccountingPeriodPage />} />
        <Route
          path={PROFIT_AND_LOSS.slug}
          element={<AmountSectionPage key="pnl" section={PROFIT_AND_LOSS} />}
        />
        <Route
          path={TAX_ADJUSTMENTS.slug}
          element={<AmountSectionPage key="adjustments" section={TAX_ADJUSTMENTS} />}
        />
        <Route
          path={BALANCE_SHEET.slug}
          element={<AmountSectionPage key="balance" section={BALANCE_SHEET} />}
        />
        <Route path="check-your-answers" element={<CheckAnswersPage />} />
        <Route path="declaration" element={<DeclarationPage />} />
        <Route path="confirmation" element={<ConfirmationPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </DraftProvider>
  );
}
