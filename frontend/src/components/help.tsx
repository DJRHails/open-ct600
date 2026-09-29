/**
 * Help under a question: a GOV.UK details component holding two tabs, "In plain English"
 * (written for this service) and HMRC's own guidance, quoted word for word with its source.
 */
import { type ReactNode, useState } from "react";

import { Tabs } from "@/components/Tabs";
import { ExternalLink } from "@/content/guides";
import type { GuidanceBlock, GuidanceSource } from "@/content/help/hmrc/extract";
import { type BoxGuidance, boxLookups, type GuidanceIndex } from "@/content/help/hmrc/lookup";
import { type GuidanceState, useGuidance } from "@/content/help/hmrc/useGuidance";
import { PAGE_BOX_HELP } from "@/content/help/pages";
import type { HmrcQuote, HmrcRef, PlainHelp, QuestionHelp as Help } from "@/content/help/types";
import { formatDate } from "@/format";

export const OGL_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/";
const HMRC = "HM Revenue and Customs";

/** A GOV.UK details component, whose content is only built once it is opened. */
function Details({ summary, children }: { summary: string; children: ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <details className="govuk-details" onToggle={(event) => setOpen(event.currentTarget.open)}>
      <summary className="govuk-details__summary">
        <span className="govuk-details__summary-text">{summary}</span>
      </summary>
      <div className="govuk-details__text">{open ? children : null}</div>
    </details>
  );
}

function Paragraphs({ texts }: { texts: string[] }) {
  return (
    <>
      {texts.map((text) => (
        <p className="govuk-body" key={text}>
          {text}
        </p>
      ))}
    </>
  );
}

/** Plain-English help, always as: what it means, an example, what it does not include, and effect. */
export function PlainText({ plain }: { plain: PlainHelp }) {
  return (
    <>
      <h3 className="govuk-heading-s">What it means</h3>
      <Paragraphs texts={plain.meaning} />
      <h3 className="govuk-heading-s">Example</h3>
      <Paragraphs texts={plain.example} />
      <h3 className="govuk-heading-s">What it does not include</h3>
      <ul className="govuk-list govuk-list--bullet">
        {plain.excludes.map((text) => (
          <li key={text}>{text}</li>
        ))}
      </ul>
      <h3 className="govuk-heading-s">What your answer changes</h3>
      <Paragraphs texts={plain.effect} />
    </>
  );
}

function Blocks({ blocks }: { blocks: GuidanceBlock[] }) {
  return (
    <>
      {blocks.map((block, index) => {
        if (block.type === "heading") {
          return (
            <h4 className="govuk-heading-s" key={index}>
              {block.text}
            </h4>
          );
        }
        if (block.type === "list") {
          return (
            <ul className="govuk-list govuk-list--bullet" key={index}>
              {block.items.map((item, position) => (
                <li key={position}>{item}</li>
              ))}
            </ul>
          );
        }
        return (
          <p className="govuk-body" key={index}>
            {block.text}
          </p>
        );
      })}
    </>
  );
}

function Source({ source, anchor }: { source: GuidanceSource; anchor: string | null }) {
  const href = anchor ? `${source.url}#${anchor}` : source.url;
  return (
    <p className="govuk-body-s">
      From <ExternalLink href={href}>{source.title}</ExternalLink>, published by {source.publisher}
      {source.updated ? `, last updated ${formatDate(source.updated.slice(0, 10))}` : ""}.
    </p>
  );
}

function Quoted({ heading, children }: { heading: string; children: ReactNode }) {
  return (
    <>
      <h3 className="govuk-heading-s">{heading}</h3>
      <div className="govuk-inset-text">{children}</div>
    </>
  );
}

/** HMRC's heading for a box, after its table's when it is a column, like "A Previously activated". */
function boxHeading({ entry }: BoxGuidance): string {
  const column = /^[A-J]\s/.test(entry.heading) && entry.context;
  return column ? `${entry.context}: ${entry.heading}` : entry.heading;
}

function entryKey({ entry }: BoxGuidance): string {
  return `${entry.form}:${entry.anchor ?? entry.heading}`;
}

type Found =
  | { type: "box"; key: string; guidance: BoxGuidance }
  | { type: "quote"; key: string; quote: HmrcQuote; source: GuidanceSource };

/** The guidance each reference names, each shown once. */
export function findGuidance(refs: HmrcRef[], index: GuidanceIndex): Found[] {
  const found = new Map<string, Found>();
  for (const ref of refs) {
    if ("box" in ref) {
      for (const guidance of index.forBox(ref.box)) {
        const key = entryKey(guidance);
        if (!found.has(key)) found.set(key, { type: "box", key, guidance });
      }
      continue;
    }
    const source = index.source(ref.quote.guide);
    if (!source) throw new Error(`No saved guide ${ref.quote.guide} for a quote`);
    const key = `${ref.quote.guide}:${ref.quote.heading}`;
    if (!found.has(key)) found.set(key, { type: "quote", key, quote: ref.quote, source });
  }
  return [...found.values()];
}

function Attribution() {
  return (
    <p className="govuk-body-s">
      Contains public sector information licensed under the{" "}
      <ExternalLink href={OGL_URL}>Open Government Licence v3.0</ExternalLink>.
    </p>
  );
}

/** HMRC's guidance for ``refs``, word for word, each with a link to where it is on GOV.UK. */
export function OfficialGuidance({ refs, state }: { refs: HmrcRef[]; state: GuidanceState }) {
  if (state.status === "loading") return <p className="govuk-body">Loading HMRC's guidance.</p>;
  if (state.status === "failed") {
    return (
      <p className="govuk-body">
        HMRC's guidance could not be loaded. Read the{" "}
        <ExternalLink href="https://www.gov.uk/guidance/the-company-tax-return-guide">
          Company Tax Return guide on GOV.UK
        </ExternalLink>
        .
      </p>
    );
  }
  return (
    <>
      {findGuidance(refs, state.index).map((found) =>
        found.type === "box" ? (
          <div key={found.key}>
            <Quoted heading={boxHeading(found.guidance)}>
              <Blocks blocks={found.guidance.entry.blocks} />
            </Quoted>
            <Source source={found.guidance.source} anchor={found.guidance.entry.anchor} />
          </div>
        ) : (
          <div key={found.key}>
            <Quoted heading={found.quote.heading}>
              <Paragraphs texts={found.quote.paragraphs} />
            </Quoted>
            <Source source={found.source} anchor={null} />
          </div>
        ),
      )}
      <Attribution />
    </>
  );
}

/** "HMRC's guidance", or whose it is when a question quotes another publisher's guide. */
export function officialLabel(refs: HmrcRef[], state: GuidanceState): string {
  if (state.status !== "ready") return "HMRC's guidance";
  const publishers = new Set(
    findGuidance(refs, state.index).map((found) =>
      found.type === "box" ? found.guidance.source.publisher : found.source.publisher,
    ),
  );
  const [only] = publishers;
  if (publishers.size > 1) return "Official guidance";
  return only && only !== HMRC ? `${only} guidance` : "HMRC's guidance";
}

/** Help for a question in the return: plain English, and HMRC's guidance. */
export function QuestionHelp({ id, help }: { id: string; help: Help }) {
  const state = useGuidance();
  return (
    <Details summary={`Help with ${help.topic}`}>
      <Tabs
        title="Help"
        tabs={[
          { id: `${id}-plain`, label: "In plain English", panel: <PlainText plain={help.plain} /> },
          {
            id: `${id}-official`,
            label: officialLabel(help.hmrc, state),
            panel: <OfficialGuidance refs={help.hmrc} state={state} />,
          },
        ]}
      />
    </Details>
  );
}

/**
 * The id a supplementary page box's help is kept under: the box's own, or the table or pair it
 * belongs to ("A10" for column "A10A"). ``null`` if there is no help for it.
 */
export function boxHelpKey(box: string, index: GuidanceIndex | null): string | null {
  for (const id of boxLookups(box)) {
    const hmrc = index?.forBox(id).some(({ entry }) => entry.boxes.includes(id));
    if (PAGE_BOX_HELP[id] || hmrc) return id;
  }
  return null;
}

/**
 * Help for a supplementary page box: plain English where we have written it, with HMRC's
 * guidance for the box; or HMRC's guidance alone, saying so.
 */
export function BoxHelp({ id, box }: { id: string; box: string }) {
  const state = useGuidance();
  const key = boxHelpKey(box, state.status === "ready" ? state.index : null);
  if (!key) return null;
  const plain = PAGE_BOX_HELP[key];
  const refs = [{ box }];
  const official = <OfficialGuidance refs={refs} state={state} />;
  if (!plain) {
    return (
      <Details summary={`HMRC's guidance for box ${key}`}>
        <p className="govuk-body">
          We have not written a plain English explanation of this box yet. This is HMRC's guidance
          for it.
        </p>
        {official}
      </Details>
    );
  }
  return (
    <Details summary={`Help with box ${key}`}>
      <Tabs
        title="Help"
        tabs={[
          { id: `${id}-plain`, label: "In plain English", panel: <PlainText plain={plain} /> },
          { id: `${id}-official`, label: "HMRC's guidance", panel: official },
        ]}
      />
    </Details>
  );
}
