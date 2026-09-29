/** HMRC's saved gov.uk guides (``specs/hmrc/guidance``), by slug, for tests. */
const files = import.meta.glob<string>("../../../../specs/hmrc/guidance/*.md", {
  query: "?raw",
  import: "default",
  eager: true,
});

export const SAVED_GUIDES: Record<string, string> = Object.fromEntries(
  Object.entries(files).map(([path, text]) => [
    (path.split("/").at(-1) ?? "").replace(/\.md$/, ""),
    text,
  ]),
);

/** Text with runs of whitespace as single spaces, to compare words, not line breaks. */
export function words(text: string): string {
  return text.replace(/\s+/g, " ").trim();
}
