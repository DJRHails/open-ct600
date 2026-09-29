// Extract HMRC's box-by-box guidance, and the sources of every saved guide, from
// specs/hmrc/guidance into the frontend's guidance module. Run with `pnpm guidance:extract`;
// a test checks the module is up to date.
import { readdirSync, readFileSync, writeFileSync } from "node:fs";

import { extractGuidance, schemaBoxes } from "../src/content/help/hmrc/extract.ts";

const root = new URL("../../", import.meta.url);
const read = (path: string) => readFileSync(new URL(path, root), "utf8");

const guides = Object.fromEntries(
  readdirSync(new URL("specs/hmrc/guidance/", root))
    .filter((file) => file.endsWith(".md"))
    .map((file) => [file.replace(/\.md$/, ""), read(`specs/hmrc/guidance/${file}`)]),
);
const spec = JSON.parse(read("backend/src/open_ct600/schema/ct600-v1.994.json"));
const { guidance, unknown } = extractGuidance(guides, schemaBoxes(spec.root));
writeFileSync(
  new URL("frontend/src/content/help/hmrc/guidance.json", root),
  `${JSON.stringify(guidance, null, 2)}\n`,
);
const boxes = new Set(guidance.entries.flatMap((entry) => entry.boxes));
console.log(`Wrote ${guidance.entries.length} entries covering ${boxes.size} boxes`);
console.log(`Headings naming boxes the schema does not have: ${unknown.join(", ") || "none"}`);
