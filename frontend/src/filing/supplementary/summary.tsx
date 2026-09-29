import type { ReactNode } from "react";

import type { ElementTree, JsonValue, SpecNode } from "@/api";
import { SummaryList, type SummaryRow } from "@/components/content";
import { sentence } from "@/filing/supplementary/spec";
import { formatDate, formatMoney, formatPounds } from "@/format";

/** An element tree's value as the user reads it: "£1,250", "31 March 2025", "Yes". */
export function formatAnswer(node: SpecNode, value: string): string {
  switch (node.kind) {
    case "pounds":
      return formatPounds(value);
    case "money":
      return formatMoney(value);
    case "percent":
      return `${value}%`;
    case "date":
      return formatDate(value);
    case "yes":
      return "Yes";
    case "yesno":
      return value === "yes" ? "Yes" : "No";
    case "enum":
      return node.enum?.find((option) => option.value === value)?.label ?? value;
    default:
      return value;
  }
}

function Key({ node, label }: { node: SpecNode; label?: string }) {
  return (
    <>
      {label ?? node.label}
      {node.box ? <span className="govuk-hint govuk-!-margin-bottom-0">Box {node.box}</span> : null}
    </>
  );
}

function asTree(value: JsonValue | undefined): ElementTree {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? value : {};
}

function valueCell(node: SpecNode, value: JsonValue): ReactNode {
  if (node.kind === "group")
    return <TreeSummary nodes={node.children} tree={asTree(value)} nested />;
  const shown = typeof value === "string" ? formatAnswer(node, value) : "";
  if (!node.computed) return shown;
  return (
    <>
      {shown}
      <span className="govuk-hint govuk-!-margin-bottom-0">Worked out for you</span>
    </>
  );
}

function rows(nodes: SpecNode[], tree: ElementTree): SummaryRow[] {
  const found: SummaryRow[] = [];
  for (const node of nodes) {
    const value = tree[node.name];
    if (value === undefined || value === null) continue;
    if (!Array.isArray(value)) {
      found.push({ key: <Key node={node} />, value: valueCell(node, value) });
      continue;
    }
    if (node.kind !== "group") {
      const lines = value.filter((line): line is string => typeof line === "string");
      found.push({ key: <Key node={node} />, value: lines.join(", ") });
      continue;
    }
    value.forEach((item, index) => {
      const label = `${sentence(node.label)} ${index + 1}`;
      found.push({ key: <Key node={node} label={label} />, value: valueCell(node, item) });
    });
  }
  return found;
}

/** The answers in an element tree, as a GOV.UK summary list in schema order. */
export function TreeSummary(props: { nodes: SpecNode[]; tree: ElementTree; nested?: boolean }) {
  const found = rows(props.nodes, props.tree);
  if (found.length === 0) return <p className="govuk-body">No answers given.</p>;
  return <SummaryList rows={found} noBorder={props.nested ?? false} />;
}
