import type { BankDetails, CT600Return, ResearchAndDevelopment, SchemaPage } from "@/api";
import { Card, SummaryList, type SummaryRow } from "@/components/content";
import { useDraft } from "@/filing/draft";
import { RELIEF_TASKS, type ReliefTask, reliefTasks } from "@/filing/payload";
import { LOAN_TABLES, loanRows, surrenderingCompanies } from "@/filing/reliefs";
import { formatSortCode } from "@/filing/repayment";
import { formatDate, formatPounds } from "@/format";

const SCHEME_NAMES: Record<ResearchAndDevelopment["scheme"], string> = {
  sme: "SME scheme",
  rdec: "Research and development expenditure credit (RDEC)",
  eris: "Enhanced R&D intensive support (ERIS)",
};

const yes = (value: boolean) => (value ? "Yes" : "No");

function researchRows(claim: ResearchAndDevelopment | null | undefined): SummaryRow[] {
  if (!claim) return [{ key: "Claiming R&D relief", value: "No" }];
  const rows: (SummaryRow | null)[] = [
    { key: "Scheme", value: SCHEME_NAMES[claim.scheme] },
    claim.scheme === "rdec"
      ? { key: "Small or medium-sized enterprise", value: yes(claim.company_is_sme) }
      : null,
    { key: "Qualifying R&D expenditure", value: formatPounds(claim.qualifying_expenditure) },
    claim.rdec_expenditure
      ? { key: "Expenditure RDEC is claimed on", value: formatPounds(claim.rdec_expenditure) }
      : null,
    claim.intensity === null ? null : { key: "R&D intensity", value: `${claim.intensity}%` },
    claim.scheme === "rdec"
      ? null
      : { key: "Payable tax credit claimed", value: yes(claim.claim_payable_credit) },
    claim.rd_workers_paye_and_nic === null
      ? null
      : { key: "PAYE and NICs on R&D workers", value: formatPounds(claim.rd_workers_paye_and_nic) },
    {
      key: "Claimed R&D relief in the previous 3 years",
      value: yes(claim.claimed_in_previous_three_years),
    },
    claim.claim_notification_submitted ? { key: "Claim notification sent", value: "Yes" } : null,
    { key: "Additional information form submitted", value: "Yes" },
  ];
  return rows.filter((row): row is SummaryRow => row !== null);
}

function loanDateRows(ct600: CT600Return, pages: SchemaPage[]): SummaryRow[] {
  const dates = ct600.participator_loan_dates;
  const ct600a = ct600.supplementary_pages?.A;
  if (!dates || !ct600a || pages.length === 0) return [];
  const rows = loanRows(ct600a);
  return LOAN_TABLES.flatMap(({ table }) =>
    rows[table].map((name, index) => ({
      key: `Loan to ${name}`,
      value: formatDate(dates[table][index] ?? ""),
    })),
  );
}

function surrendererRows(ct600: CT600Return): SummaryRow[] {
  const ct600c = ct600.supplementary_pages?.C;
  const names = new Map(
    (ct600c ? surrenderingCompanies(ct600c) : []).map((company) => [
      company.reference,
      company.name,
    ]),
  );
  const given = ct600.group_relief_surrenderers ?? [];
  if (given.length === 0)
    return [{ key: "Figures from surrendering companies", value: "None given" }];
  return given.map((company) => ({
    key: `${names.get(company.tax_reference) ?? ""} (${company.tax_reference})`.trim(),
    value: [
      `Can surrender ${formatPounds(company.surrenderable_amount)}`,
      `already surrendered ${formatPounds(company.surrendered_to_others)}`,
      company.consortium_share === null ? null : `consortium share ${company.consortium_share}%`,
    ]
      .filter(Boolean)
      .join(", "),
  }));
}

function bankRows(details: BankDetails | null | undefined): SummaryRow[] {
  if (!details) return [];
  const rows: (SummaryRow | null)[] = [
    { key: "Name of bank or building society", value: details.bank_name },
    { key: "Name on the account", value: details.account_name },
    { key: "Sort code", value: formatSortCode(details.sort_code) },
    { key: "Account number", value: details.account_number },
    details.building_society_reference
      ? { key: "Building society roll number", value: details.building_society_reference }
      : null,
  ];
  return rows.filter((row): row is SummaryRow => row !== null);
}

function rowsFor(task: ReliefTask, ct600: CT600Return, pages: SchemaPage[]): SummaryRow[] {
  switch (task) {
    case "research_and_development":
      return researchRows(ct600.research_and_development);
    case "participator_loan_dates":
      return loanDateRows(ct600, pages);
    case "group_relief_surrenderers":
      return surrendererRows(ct600);
    case "creative_industries":
      return [{ key: "Additional information form submitted", value: "Yes" }];
    case "repayment":
      return bankRows(ct600.repayment);
  }
}

/** The relief answers the supplementary pages have no box for, one card per task. */
export function ReliefCards({ ct600, pages }: { ct600: CT600Return; pages: SchemaPage[] }) {
  const { draft } = useDraft();
  return (
    <>
      {reliefTasks(draft, pages).map((task) => (
        <Card
          key={task}
          title={RELIEF_TASKS[task].title}
          change={`/file/${RELIEF_TASKS[task].slug}?change=1`}
        >
          <SummaryList rows={rowsFor(task, ct600, pages)} />
        </Card>
      ))}
    </>
  );
}

/** The relief task a rejected answer's location belongs to, like ``research_and_development``. */
export function reliefTaskLink(location: string[]): string | null {
  const task = (Object.keys(RELIEF_TASKS) as ReliefTask[]).find((key) => key === location[0]);
  return task ? `/file/${RELIEF_TASKS[task].slug}?change=1` : null;
}
