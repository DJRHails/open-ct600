import { Route, Routes } from "react-router";

import { TAX_ADJUSTMENTS_HELP } from "@/content/help/taxAdjustments";
import { AccountingPeriodPage } from "@/filing/AccountingPeriodPage";
import { AccountsDetailsPage } from "@/filing/AccountsDetailsPage";
import { AmountQuestionsPage } from "@/filing/AmountQuestionsPage";
import { AmountSectionPage } from "@/filing/AmountSectionPage";
import { CheckAnswersPage } from "@/filing/CheckAnswersPage";
import { CompanyDetailsPage } from "@/filing/CompanyDetailsPage";
import { ConfirmationPage } from "@/filing/ConfirmationPage";
import { DeclarationPage } from "@/filing/DeclarationPage";
import { DraftProvider } from "@/filing/draft";
import { BALANCE_SHEET, PROFIT_AND_LOSS, TAX_ADJUSTMENTS } from "@/filing/model";
import { RELIEF_TASKS } from "@/filing/payload";
import { CreativeFormPage } from "@/filing/reliefs/CreativeFormPage";
import { LoanDatesPage } from "@/filing/reliefs/LoanDatesPage";
import { ResearchAndDevelopmentPage } from "@/filing/reliefs/ResearchAndDevelopmentPage";
import { SurrenderersPage } from "@/filing/reliefs/SurrenderersPage";
import { DeleteReturnPage } from "@/filing/returns/DeleteReturnPage";
import { ImportReturnPage } from "@/filing/returns/ImportReturnPage";
import { ReturnsPage } from "@/filing/returns/ReturnsPage";
import { StartPage } from "@/filing/StartPage";
import { ChoosePagesPage } from "@/filing/supplementary/ChoosePagesPage";
import { PageAnswersPage } from "@/filing/supplementary/PageAnswersPage";
import { PageScreenPage } from "@/filing/supplementary/PageScreenPage";
import { SchemaProvider } from "@/filing/supplementary/schema";
import { TaskListPage } from "@/filing/TaskListPage";
import { NotFoundPage } from "@/pages/NotFound";

export function FilingRoutes() {
  return (
    <DraftProvider>
      <SchemaProvider>
        <FilingPages />
      </SchemaProvider>
    </DraftProvider>
  );
}

function FilingPages() {
  return (
    <Routes>
      <Route index element={<StartPage />} />
      <Route path="tasks" element={<TaskListPage />} />
      <Route path="returns" element={<ReturnsPage />} />
      <Route path="returns/import" element={<ImportReturnPage />} />
      <Route path="returns/:id/delete" element={<DeleteReturnPage />} />
      <Route path="company-details" element={<CompanyDetailsPage />} />
      <Route path="accounting-period" element={<AccountingPeriodPage />} />
      <Route
        path={PROFIT_AND_LOSS.slug}
        element={<AmountSectionPage key="pnl" section={PROFIT_AND_LOSS} />}
      />
      <Route
        path={TAX_ADJUSTMENTS.slug}
        element={
          <AmountQuestionsPage
            key="adjustments"
            section={TAX_ADJUSTMENTS}
            help={TAX_ADJUSTMENTS_HELP}
          />
        }
      />
      <Route
        path={BALANCE_SHEET.slug}
        element={<AmountSectionPage key="balance" section={BALANCE_SHEET} />}
      />
      <Route path="accounts-details" element={<AccountsDetailsPage />} />
      <Route
        path={RELIEF_TASKS.research_and_development.slug}
        element={<ResearchAndDevelopmentPage />}
      />
      <Route path={RELIEF_TASKS.participator_loan_dates.slug} element={<LoanDatesPage />} />
      <Route path={RELIEF_TASKS.group_relief_surrenderers.slug} element={<SurrenderersPage />} />
      <Route path={RELIEF_TASKS.creative_industries.slug} element={<CreativeFormPage />} />
      <Route path="supplementary-pages" element={<ChoosePagesPage />} />
      <Route path="supplementary-pages/:code" element={<PageAnswersPage />} />
      <Route path="supplementary-pages/:code/:screen" element={<PageScreenPage />} />
      <Route path="check-your-answers" element={<CheckAnswersPage />} />
      <Route path="declaration" element={<DeclarationPage />} />
      <Route path="confirmation" element={<ConfirmationPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
