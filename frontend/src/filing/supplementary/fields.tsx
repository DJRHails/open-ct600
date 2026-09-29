/** GOV.UK form controls for any part of a supplementary page, rendered from its spec. */
import { createContext, type ReactNode, useContext, useEffect, useRef, useState } from "react";

import type { PageCode, SpecNode } from "@/api";
import {
  Button,
  Checkbox,
  type DateParts,
  DateInput,
  Radios,
  Select,
  TextInput,
} from "@/components/forms";
import {
  answeredByChoosing,
  chosenBranch,
  getAt,
  groupTree,
  isBlank,
  isDateParts,
  isRecord,
  NO_BRANCH,
  type RawTree,
  type RawValue,
} from "@/filing/supplementary/answers";
import {
  boxHint,
  choiceKey,
  fieldId,
  type FormItem,
  formItems,
  phrase,
  repeats,
  sentence,
  type TreePath,
} from "@/filing/supplementary/spec";
import { TreeSummary } from "@/filing/supplementary/summary";
import { BoxHelp, boxHelpKey } from "@/components/help";
import { useGuidance } from "@/content/help/hmrc/useGuidance";

/** Errors are keyed by the tree path of the answer they are about. */
export function pathKey(path: TreePath): string {
  return path.map(String).join("/");
}

type PageForm = {
  code: PageCode;
  answers: RawTree;
  setAnswer: (path: TreePath, value: RawValue) => void;
  errors: Record<string, string>;
  clearErrors: () => void;
};

const PageFormContext = createContext<PageForm | null>(null);

export function PageFormProvider({ value, children }: { value: PageForm; children: ReactNode }) {
  return <PageFormContext.Provider value={value}>{children}</PageFormContext.Provider>;
}

function usePageForm(): PageForm {
  const form = useContext(PageFormContext);
  if (!form) throw new Error("Page questions must be inside <PageFormProvider>");
  return form;
}

/**
 * The help already shown above a question on the screen, by ``boxHelpKey``: the columns of a
 * table, like A10A and A10B, share box A10's help, which is shown once, under the first.
 */
const HelpShown = createContext<ReadonlySet<string>>(new Set());

function useHelpKey(box: string | null): string | null {
  const guidance = useGuidance();
  return box ? boxHelpKey(box, guidance.status === "ready" ? guidance.index : null) : null;
}

/** Help for a box, unless a question above it on the screen has the same help. */
function HelpOnce({ id, box }: { id: string; box: string | null }) {
  const shown = useContext(HelpShown);
  const key = useHelpKey(box);
  if (!box || !key || shown.has(key)) return null;
  return <BoxHelp id={`${id}-help`} box={box} />;
}

/** Mark a box's help as shown for the questions inside it. */
function WithHelpShown({ box, children }: { box: string | null; children: ReactNode }) {
  const shown = useContext(HelpShown);
  const key = useHelpKey(box);
  const value = key && !shown.has(key) ? new Set([...shown, key]) : shown;
  return <HelpShown.Provider value={value}>{children}</HelpShown.Provider>;
}

/** The questions for ``items`` in the group at ``path``. */
export function Items({
  items,
  path,
  depth,
}: {
  items: FormItem[];
  path: TreePath;
  depth: number;
}) {
  const guidance = useGuidance();
  const index = guidance.status === "ready" ? guidance.index : null;
  // The help shown above each item: what was shown above this group, and by earlier items.
  const above: ReadonlySet<string>[] = [];
  let shown = useContext(HelpShown);
  for (const item of items) {
    above.push(shown);
    const key = item.type === "node" && item.node.box ? boxHelpKey(item.node.box, index) : null;
    if (key) shown = new Set([...shown, key]);
  }
  return (
    <>
      {items.map((item, position) =>
        item.type === "node" ? (
          <HelpShown.Provider key={item.node.name} value={above[position] ?? shown}>
            <Occurrence node={item.node} path={[...path, item.node.name]} depth={depth} />
          </HelpShown.Provider>
        ) : (
          <HelpShown.Provider key={item.id} value={above[position] ?? shown}>
            <Choice item={item} path={path} depth={depth} />
          </HelpShown.Provider>
        ),
      )}
    </>
  );
}

type NodeProps = { node: SpecNode; path: TreePath; depth: number };

function Occurrence({ node, path, depth }: NodeProps) {
  if (repeats(node)) {
    return node.kind === "group" ? (
      <RepeatingGroup node={node} path={path} depth={depth} />
    ) : (
      <RepeatingScalar node={node} path={path} />
    );
  }
  if (node.kind === "group") return <Group node={node} path={path} depth={depth} />;
  return <Field node={node} path={path} />;
}

function optional(node: SpecNode, label: string): string {
  return node.min === 0 && node.kind !== "yes" ? `${label} (optional)` : label;
}

function Legend({ depth, children }: { depth: number; children: ReactNode }) {
  const size = depth === 0 ? "m" : "s";
  return (
    <legend className={`govuk-fieldset__legend govuk-fieldset__legend--${size}`}>{children}</legend>
  );
}

function Group({ node, path, depth }: NodeProps) {
  const { code } = usePageForm();
  const hint = boxHint(node);
  return (
    <div className="govuk-form-group">
      <fieldset className="govuk-fieldset">
        <Legend depth={depth}>{optional(node, node.label)}</Legend>
        {hint ? <div className="govuk-hint">{hint}</div> : null}
        <HelpOnce id={fieldId(code, path)} box={node.box} />
        <WithHelpShown box={node.box}>
          <Items items={formItems(node)} path={path} depth={depth + 1} />
        </WithHelpShown>
      </fieldset>
    </div>
  );
}

function Choice(props: {
  item: Extract<FormItem, { type: "choice" }>;
  path: TreePath;
  depth: number;
}) {
  const { item, path, depth } = props;
  const { code, answers, setAnswer, errors } = usePageForm();
  const group = getAt(answers, path);
  const here = isRecord(group) ? group : {};
  const selected = chosenBranch(item, here);
  const keyPath = [...path, choiceKey(item.id)];
  const recorded = here[choiceKey(item.id)];
  const options = item.branches.map((branch) => ({
    value: branch.name,
    label: branch.label,
    // A branch's own questions show their boxes; a tick-box branch has only the radio to show it.
    hint: answeredByChoosing(branch) && branch.members[0] ? boxHint(branch.members[0]) : undefined,
    conditional: answeredByChoosing(branch) ? undefined : (
      <Items
        items={branch.members.map((node) => ({ type: "node", node }) as const)}
        path={path}
        depth={depth + 1}
      />
    ),
  }));
  if (item.min === 0)
    options.push({
      value: NO_BRANCH,
      label: "None of these",
      hint: undefined,
      conditional: undefined,
    });
  const value = selected?.name ?? (recorded === NO_BRANCH ? NO_BRANCH : "");
  const ticked = item.branches.filter(answeredByChoosing).map((branch) => branch.members[0]);
  return (
    <Radios
      name={fieldId(code, keyPath)}
      legend="Which of these applies?"
      options={options}
      value={value}
      onChange={(branch) => setAnswer(keyPath, branch)}
      error={errors[pathKey(keyPath)]}
      help={<ChoiceHelp id={fieldId(code, keyPath)} boxes={ticked.map((node) => node?.box)} />}
    />
  );
}

/** Help for the boxes a choice's radios tick, each once. */
function ChoiceHelp({ id, boxes }: { id: string; boxes: (string | null | undefined)[] }) {
  const guidance = useGuidance();
  const shown = useContext(HelpShown);
  const index = guidance.status === "ready" ? guidance.index : null;
  const byKey = new Map<string, string>();
  for (const box of boxes) {
    const key = box ? boxHelpKey(box, index) : null;
    if (box && key && !shown.has(key) && !byKey.has(key)) byKey.set(key, box);
  }
  return (
    <>
      {[...byKey.values()].map((box) => (
        <BoxHelp key={box} id={`${id}-${box}-help`} box={box} />
      ))}
    </>
  );
}

const TEXT_WIDTHS = [2, 3, 4, 5, 10, 20, 30] as const;

function textWidth(node: SpecNode) {
  const longest = node.maxLength;
  if (longest === null) return undefined;
  const width = TEXT_WIDTHS.find((candidate) => candidate >= longest);
  return width === undefined ? undefined : (String(width) as `${(typeof TEXT_WIDTHS)[number]}`);
}

const EMPTY_DATE: DateParts = { day: "", month: "", year: "" };
const MAX_RADIOS = 7;

/** One answer: a text box, date, tick box, or radios, by the element's kind. */
function Field({ node, path, label }: { node: SpecNode; path: TreePath; label?: string }) {
  const { code, answers, setAnswer, errors } = usePageForm();
  const raw = getAt(answers, path);
  const text = typeof raw === "string" ? raw : "";
  const id = fieldId(code, path);
  const common = {
    id,
    label: optional(node, label ?? node.label),
    hint: boxHint(node),
    error: errors[pathKey(path)],
    help: <HelpOnce id={id} box={node.box} />,
  };
  const setText = (value: string) => setAnswer(path, value);
  switch (node.kind) {
    case "pounds":
    case "money":
      return (
        <TextInput
          {...common}
          value={text}
          onChange={setText}
          prefix="£"
          width="10"
          inputMode={node.kind === "money" ? "decimal" : "numeric"}
          spellCheck={false}
        />
      );
    case "percent":
      return (
        <TextInput
          {...common}
          value={text}
          onChange={setText}
          suffix="%"
          width="5"
          inputMode="decimal"
        />
      );
    case "integer":
    case "decimal":
    case "year":
      return (
        <TextInput
          {...common}
          value={text}
          onChange={setText}
          width={node.kind === "year" ? "4" : "10"}
          inputMode={node.kind === "decimal" ? "decimal" : "numeric"}
        />
      );
    case "text":
      return <TextInput {...common} value={text} onChange={setText} width={textWidth(node)} />;
    case "date":
      return (
        <DateInput
          id={common.id}
          legend={common.label}
          hint={common.hint}
          error={common.error}
          help={common.help}
          value={isDateParts(raw) ? raw : EMPTY_DATE}
          onChange={(parts) => setAnswer(path, parts)}
        />
      );
    default:
      return <ChoiceField node={node} path={path} common={common} text={text} />;
  }
}

type Common = {
  id: string;
  label: string;
  hint: string | undefined;
  error: string | undefined;
  help: ReactNode;
};

function ChoiceField(props: { node: SpecNode; path: TreePath; common: Common; text: string }) {
  const { node, path, common, text } = props;
  const { setAnswer } = usePageForm();
  const { id, label, hint, error, help } = common;
  const set = (value: string) => setAnswer(path, value);
  switch (node.kind) {
    case "yes":
      return (
        <Checkbox
          id={id}
          label={label}
          hint={hint}
          checked={text === "yes"}
          onChange={(checked) => set(checked ? "yes" : "")}
          error={error}
          help={help}
        />
      );
    case "yesno": {
      const options = [
        { value: "yes", label: "Yes" },
        { value: "no", label: "No" },
      ];
      return (
        <Radios
          name={id}
          legend={label}
          hint={hint}
          options={options}
          value={text}
          onChange={set}
          error={error}
          help={help}
          inline
        />
      );
    }
    case "enum": {
      const options = node.enum ?? [];
      return options.length > MAX_RADIOS ? (
        <Select
          id={id}
          label={label}
          hint={hint}
          options={options}
          value={text}
          onChange={set}
          error={error}
          help={help}
        />
      ) : (
        <Radios
          name={id}
          legend={label}
          hint={hint}
          options={options}
          value={text}
          onChange={set}
          error={error}
          help={help}
        />
      );
    }
    default:
      return (
        <div className="govuk-inset-text" id={id}>
          {sentence(node.label)} cannot be answered in this service.
        </div>
      );
  }
}

/** A repeating single answer, like the lines of an address: one box per line allowed. */
function RepeatingScalar({ node, path }: { node: SpecNode; path: TreePath }) {
  const { answers } = usePageForm();
  const entries = getAt(answers, path);
  const given = Array.isArray(entries) ? entries.length : 0;
  const count = node.max ?? Math.max(node.min, given + 1);
  return (
    <div className="govuk-form-group">
      <fieldset className="govuk-fieldset">
        <Legend depth={1}>{optional(node, node.label)}</Legend>
        {Array.from({ length: count }, (_, index) => (
          <Field
            key={index}
            node={{ ...node, min: index < node.min ? 1 : 0, box: index === 0 ? node.box : null }}
            path={[...path, index]}
            label={`${sentence(node.label)} ${index + 1}`}
          />
        ))}
      </fieldset>
    </div>
  );
}

function hasErrorsUnder(errors: Record<string, string>, path: TreePath): boolean {
  const prefix = pathKey(path);
  return Object.keys(errors).some((key) => key === prefix || key.startsWith(`${prefix}/`));
}

/**
 * GOV.UK "add another": each item added is summarised with Change and Remove links, and edited
 * in place; up to the element's maximum can be added.
 */
function RepeatingGroup({ node, path, depth }: NodeProps) {
  const { code, answers, setAnswer, errors, clearErrors } = usePageForm();
  const stored = getAt(answers, path);
  const list = Array.isArray(stored) ? stored : [];
  const count = Math.max(list.length, 1);
  // Items are summarised once answered, so on arrival only unanswered items are open for
  // editing; items added or changed here stay open while the user types.
  const [open, setOpen] = useState<number[]>(() =>
    Array.from({ length: count }, (_, index) => index).filter((index) => isBlank(list[index])),
  );
  const focusAdded = useRef<string | null>(null);
  const addId = `${fieldId(code, path)}-add`;
  const name = phrase(node.label);
  const canAdd = node.max === null || count < node.max;

  useEffect(() => {
    if (focusAdded.current === null) return;
    document.getElementById(focusAdded.current)?.focus();
    focusAdded.current = null;
  });

  function add() {
    const padded = Array.from({ length: count }, (_, index) => list[index] ?? {});
    setAnswer(path, [...padded, {}]);
    setOpen([...open, count]);
    focusAdded.current = `${fieldId(code, [...path, count])}-legend`;
  }

  function remove(index: number) {
    setAnswer(
      path,
      list.filter((_, position) => position !== index),
    );
    const shifted = open
      .filter((item) => item !== index)
      .map((item) => (item > index ? item - 1 : item));
    // Removing the last item leaves an empty one to fill in.
    setOpen(list.length <= 1 ? [0] : shifted);
    clearErrors();
  }

  return (
    <div className="govuk-form-group" id={fieldId(code, path)}>
      {depth > 0 ? (
        <h2 className="govuk-heading-m">{optional(node, sentence(node.label))}</h2>
      ) : null}
      {boxHint(node) ? <div className="govuk-hint">{boxHint(node)}</div> : null}
      <HelpOnce id={fieldId(code, path)} box={node.box} />
      <WithHelpShown box={node.box}>
        {Array.from({ length: count }, (_, index) => {
          const item = list[index];
          const itemPath = [...path, index];
          const editing = open.includes(index) || hasErrorsUnder(errors, itemPath);
          const title = `${sentence(node.label)} ${index + 1}`;
          const removable = count > 1 || !isBlank(item);
          return editing ? (
            <EditItem key={index} node={node} path={itemPath} depth={depth} title={title}>
              {removable ? (
                <Button type="button" variant="secondary" onClick={() => remove(index)}>
                  {"Remove "}
                  <span className="govuk-visually-hidden">{phrase(title)}</span>
                </Button>
              ) : null}
            </EditItem>
          ) : (
            <SummaryItem
              key={index}
              node={node}
              item={item}
              title={title}
              onChange={() => setOpen([...open, index])}
              onRemove={() => remove(index)}
            />
          );
        })}
      </WithHelpShown>
      {canAdd ? (
        <Button type="button" variant="secondary" id={addId} onClick={add}>
          Add another {name}
        </Button>
      ) : (
        <p className="govuk-body">You can add up to {node.max} of these.</p>
      )}
    </div>
  );
}

type EditItemProps = NodeProps & { title: string; children: ReactNode };

function EditItem({ node, path, depth, title, children }: EditItemProps) {
  const { code } = usePageForm();
  return (
    <div className="govuk-form-group">
      <fieldset className="govuk-fieldset">
        <legend
          className="govuk-fieldset__legend govuk-fieldset__legend--s"
          id={`${fieldId(code, path)}-legend`}
          tabIndex={-1}
        >
          {title}
        </legend>
        <Items items={formItems(node)} path={path} depth={depth + 1} />
        {children}
      </fieldset>
    </div>
  );
}

type SummaryItemProps = {
  node: SpecNode;
  item: RawValue | undefined;
  title: string;
  onChange: () => void;
  onRemove: () => void;
};

function SummaryItem({ node, item, title, onChange, onRemove }: SummaryItemProps) {
  const hidden = <span className="govuk-visually-hidden">{phrase(title)}</span>;
  return (
    <div className="govuk-summary-card">
      <div className="govuk-summary-card__title-wrapper">
        <h3 className="govuk-summary-card__title">{title}</h3>
        <ul className="govuk-summary-card__actions">
          <li className="govuk-summary-card__action">
            <button type="button" className="govuk-link app-link-button" onClick={onChange}>
              {"Change "}
              {hidden}
            </button>
          </li>
          <li className="govuk-summary-card__action">
            <button type="button" className="govuk-link app-link-button" onClick={onRemove}>
              {"Remove "}
              {hidden}
            </button>
          </li>
        </ul>
      </div>
      <div className="govuk-summary-card__content">
        <TreeSummary nodes={node.children} tree={groupTree(node, item)} />
      </div>
    </div>
  );
}
