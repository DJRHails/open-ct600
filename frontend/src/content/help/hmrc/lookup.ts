/** Finding HMRC's guidance for a box, from the entries ``extract`` takes from its guides. */
import type { Guidance, GuidanceEntry, GuidanceSource } from "@/content/help/hmrc/extract";

/**
 * The ids to look a box up by, most specific first. The schema numbers table columns and
 * pairs of boxes that its guides explain together: "A10A" is column A of box A10, "K15.1A" a
 * column of the first K15 row, and "688/689" is boxes 688 and 689.
 */
export function boxLookups(box: string): string[] {
  const ids = [box];
  for (const part of box.split("/")) {
    ids.push(part);
    let id = part;
    for (;;) {
      const letters = id.replace(/[A-Za-z]{1,2}$/, "");
      const shorter = letters === id ? id.replace(/\.\d$/, "") : letters;
      if (shorter === id || !/\d$/.test(shorter)) break;
      ids.push(shorter);
      id = shorter;
    }
  }
  return [...new Set(ids)];
}

export type BoxGuidance = { entry: GuidanceEntry; source: GuidanceSource };

export type GuidanceIndex = {
  /** HMRC's guidance for a box: the entries for its most specific id that has any. */
  forBox: (box: string) => BoxGuidance[];
  /** A saved guide's source by its slug. */
  source: (guide: string) => GuidanceSource | undefined;
};

export function indexGuidance(guidance: Guidance): GuidanceIndex {
  const byBox = new Map<string, GuidanceEntry[]>();
  for (const entry of guidance.entries) {
    for (const box of entry.boxes) byBox.set(box, [...(byBox.get(box) ?? []), entry]);
  }
  const bySlug = new Map(guidance.sources.map((source) => [source.guide, source]));
  const byForm = new Map(guidance.sources.map((source) => [source.form, source]));
  const forOneBox = (box: string): BoxGuidance[] => {
    for (const id of boxLookups(box)) {
      const entries = byBox.get(id);
      if (!entries) continue;
      // An entry for fewer boxes says more about each of them.
      const specific = [...entries].sort((a, b) => a.boxes.length - b.boxes.length);
      return specific.flatMap((entry) => {
        const source = byForm.get(entry.form);
        return source ? [{ entry, source }] : [];
      });
    }
    return [];
  };
  // A pair like "780/785" is two boxes: each one's guidance, once each.
  const forBox = (box: string): BoxGuidance[] => {
    const found = box.split("/").flatMap(forOneBox);
    return found.filter(
      ({ entry }, index) => found.findIndex((other) => other.entry === entry) === index,
    );
  };
  return { forBox, source: (guide) => bySlug.get(guide) };
}
