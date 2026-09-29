import type { ReliefsSummary as Reliefs, ResearchAndDevelopmentScheme } from "@/api";
import { SummaryList, type SummaryRow } from "@/components/content";
import { formatMoney, formatPounds } from "@/format";

const SCHEMES: Record<ResearchAndDevelopmentScheme, string> = {
  sme: "SME scheme",
  large_company_rdec: "Research and development expenditure credit (large companies)",
  merged_rdec: "Merged scheme expenditure credit",
  eris: "Enhanced support for R&D intensive SMEs (ERIS)",
};

/** Whole pounds arrive as numbers and pounds and pence as strings. */
type Line = [label: string, amount: number | string | null];

function rows(lines: Line[]): SummaryRow[] {
  return lines
    .filter((line): line is [string, number | string] => line[1] !== null && Number(line[1]) !== 0)
    .map(([label, amount]) => ({
      key: label,
      value: typeof amount === "number" ? formatPounds(amount) : formatMoney(amount),
    }));
}

function researchRows(relief: NonNullable<Reliefs["research_and_development"]>): SummaryRow[] {
  return [
    { key: "R&D scheme", value: SCHEMES[relief.scheme] },
    ...rows([
      ["R&D qualifying expenditure", relief.qualifying_expenditure],
      ["R&D additional deduction", relief.additional_deduction],
      ["R&D expenditure credit", relief.rdec],
      ["R&D credits set against tax", relief.set_off],
      ["R&D expenditure credit paid to the company", relief.payable_rdec],
      ["R&D tax credit paid to the company", relief.payable_credit],
      ["R&D expenditure credit carried forward", relief.rdec_carried_forward],
    ]),
  ];
}

function creativeRows(relief: NonNullable<Reliefs["creative_industries"]>): SummaryRow[] {
  return rows([
    ["Creative expenditure credit", relief.expenditure_credit],
    ["Creative expenditure credit set against tax", relief.expenditure_credit_set_off],
    ["Creative expenditure credit paid to the company", relief.expenditure_credit_payable],
    ["Creative additional deduction", relief.additional_deduction],
    ["Creative tax credit", relief.tax_credit],
    ["Creative tax credit paid to the company", relief.tax_credit_payable],
  ]);
}

/** The reliefs and credits claimed through supplementary pages, leaving out any that are nil. */
export function ReliefsSummary({ reliefs }: { reliefs: Reliefs }) {
  const group = reliefs.group_relief;
  const loans = reliefs.loans_to_participators;
  const research = reliefs.research_and_development;
  const creative = reliefs.creative_industries;
  const found = [
    ...(group
      ? rows([
          ["Group relief claimed", group.claimed],
          [
            "Group relief claimed for carried-forward losses",
            group.claimed_for_carried_forward_losses,
          ],
        ])
      : []),
    ...(research ? researchRows(research) : []),
    ...(loans ? rows([["Tax on loans to participators (section 455)", loans.tax_payable]]) : []),
    ...(creative ? creativeRows(creative) : []),
  ];
  if (found.length === 0) return null;
  return (
    <>
      <h2 className="govuk-heading-m">Reliefs and credits</h2>
      <SummaryList rows={found} />
    </>
  );
}
