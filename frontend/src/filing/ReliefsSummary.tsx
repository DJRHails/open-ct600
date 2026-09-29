import type { ReliefsSummary as Reliefs } from "@/api";
import { SummaryList } from "@/components/content";
import { formatMoney } from "@/format";

const AMOUNTS: { key: Exclude<keyof Reliefs, "research_and_development_scheme">; label: string }[] =
  [
    { key: "group_relief", label: "Group relief claimed" },
    { key: "research_and_development_deduction", label: "R&D enhanced deduction" },
    { key: "research_and_development_credit", label: "R&D expenditure credit" },
    { key: "research_and_development_payable_credit", label: "R&D credit payable to the company" },
    {
      key: "loans_to_participators_tax",
      label: "Tax on loans to participators (section 455)",
    },
  ];

/** The reliefs and charges the computation applied, leaving out any that are nil. */
export function ReliefsSummary({ reliefs }: { reliefs: Reliefs }) {
  const rows = AMOUNTS.filter(({ key }) => Number(reliefs[key]) !== 0).map(({ key, label }) => ({
    key: label,
    value: formatMoney(reliefs[key]),
  }));
  const scheme = reliefs.research_and_development_scheme;
  if (scheme) rows.unshift({ key: "R&D scheme", value: scheme });
  if (rows.length === 0) return null;
  return (
    <>
      <h2 className="govuk-heading-m">Reliefs</h2>
      <SummaryList rows={rows} />
    </>
  );
}
