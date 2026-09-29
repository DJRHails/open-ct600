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

type Context = string[];

function Key({ node, context, label }: { node: SpecNode; context: Context; label?: string }) {
  return (
    <>
      {context.length > 0 ? (
        <span className="govuk-caption-s govuk-!-display-block">{context.join(": ")}</span>
      ) : null}
      {label ?? node.label}
      {node.box ? (
        <span className="govuk-hint govuk-!-display-block govuk-!-margin-bottom-0">
          Box {node.box}
        </span>
      ) : null}
    </>
  );
}

function asTree(value: JsonValue | undefined): ElementTree {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? value : {};
}

function valueCell(node: SpecNode, value: string): ReactNode {
  const shown = formatAnswer(node, value);
  if (!node.computed) return shown;
  return (
    <>
      {shown}
      <span className="govuk-hint govuk-!-display-block govuk-!-margin-bottom-0">
        Worked out for you
      </span>
    </>
  );
}

/**
 * One row per answer, in schema order. Answers inside groups and list items get their own
 * rows, captioned with where they belong, like "Loan 2".
 */
function rows(nodes: SpecNode[], tree: ElementTree, context: Context): SummaryRow[] {
  const found: SummaryRow[] = [];
  for (const node of nodes) {
    const value = tree[node.name];
    if (value === undefined || value === null) continue;
    if (node.kind === "group") {
      const items = Array.isArray(value) ? value : [value];
      items.forEach((item, index) => {
        const name = Array.isArray(value) ? `${sentence(node.label)} ${index + 1}` : node.label;
        found.push(...rows(node.children, asTree(item), [...context, name]));
      });
    } else if (Array.isArray(value)) {
      const lines = value.filter((line): line is string => typeof line === "string");
      found.push({ key: <Key node={node} context={context} />, value: lines.join(", ") });
    } else if (typeof value === "string") {
      found.push({ key: <Key node={node} context={context} />, value: valueCell(node, value) });
    }
  }
  return found;
}

/** The answers in an element tree, as a GOV.UK summary list in schema order. */
export function TreeSummary(props: { nodes: SpecNode[]; tree: ElementTree }) {
  const found = rows(props.nodes, props.tree, []);
  if (found.length === 0) return <p className="govuk-body">No answers given.</p>;
  return <SummaryList rows={found} />;
}
