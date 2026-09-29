import { useState } from "react";
import { useNavigate } from "react-router";

import type { PageCode, SchemaPage } from "@/api";
import { Checkboxes } from "@/components/forms";
import { useDraft } from "@/filing/draft";
import { useNextPage } from "@/filing/paths";
import { SectionFrame } from "@/filing/SectionFrame";
import { PAGE_DESCRIPTIONS, pageName } from "@/filing/supplementary/content";
import { SchemaGate } from "@/filing/supplementary/SchemaGate";

const NONE = "none";
const TITLE = "Supplementary pages";

type Choice = PageCode | typeof NONE;

function description(page: SchemaPage): string | undefined {
  return page.code === "G" ? undefined : PAGE_DESCRIPTIONS[page.code];
}

function ChoosePages({ pages }: { pages: SchemaPage[] }) {
  const { draft, saveChosenPages } = useDraft();
  const { next } = useNextPage();
  const navigate = useNavigate();
  const saved = draft.chosen_pages;
  const [chosen, setChosen] = useState<Choice[]>(
    saved === undefined ? [] : saved.length === 0 ? [NONE] : saved,
  );
  const [error, setError] = useState<string | undefined>();
  const offered = pages.filter((page) => !page.dormant);

  function save() {
    if (chosen.length === 0) {
      setError("Select the supplementary pages the company needs, or select none of these");
      return;
    }
    const codes = offered.map((page) => page.code).filter((code) => chosen.includes(code));
    saveChosenPages(codes);
    navigate(next);
  }

  return (
    <SectionFrame
      title={TITLE}
      errors={error ? { pages: error } : {}}
      fieldOrder={["pages"]}
      onSubmit={save}
      intro={
        "Supplementary pages give HMRC details of particular claims and circumstances. " +
        "Most small companies do not need any."
      }
    >
      <Checkboxes<Choice>
        name="pages"
        legend="Which supplementary pages does the company need to complete?"
        hint="Select all that apply."
        options={offered.map((page) => ({
          value: page.code,
          label: `${pageName(page.code)}: ${page.title}`,
          ...(description(page) ? { hint: description(page) } : {}),
        }))}
        exclusive={{ value: NONE, label: "None of these" }}
        value={chosen}
        onChange={setChosen}
        error={error}
      />
    </SectionFrame>
  );
}

export function ChoosePagesPage() {
  return <SchemaGate title={TITLE}>{(pages) => <ChoosePages pages={pages} />}</SchemaGate>;
}
