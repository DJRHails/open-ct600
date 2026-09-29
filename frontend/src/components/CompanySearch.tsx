import "accessible-autocomplete/dist/accessible-autocomplete.min.css";

import accessibleAutocomplete from "accessible-autocomplete";
import { useEffect, useRef } from "react";

import type { CompanySearchResult } from "@/api";

/** Wait for a pause in typing before searching, to spare Companies House's rate limit. */
export const SEARCH_DELAY_MS = 300;

const HTML_ESCAPES: Record<string, string> = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
};

/** The autocomplete renders suggestions as HTML, and company names come from outside. */
export function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, (character) => HTML_ESCAPES[character] ?? character);
}

function suggestion(company: CompanySearchResult | string): string {
  if (typeof company === "string") return escapeHtml(company);
  const address = company.address
    ? `<span class="app-suggestion-detail">${escapeHtml(company.address)}</span>`
    : "";
  return `${escapeHtml(company.name)} (${escapeHtml(company.number)})${address}`;
}

type CompanySearchProps = {
  id: string;
  label: string;
  hint: string;
  error?: string | undefined;
  search: (query: string) => Promise<CompanySearchResult[]>;
  onChoose: (company: CompanySearchResult) => void;
  onSearchError: (error: unknown) => void;
};

/**
 * Search Companies House by name or number with alphagov's accessible-autocomplete: a combobox
 * that announces how many results there are and lets keyboard users move through them with the
 * arrow keys. Searches are debounced, and only the latest search's results are shown.
 */
export function CompanySearch(props: CompanySearchProps) {
  const { id, label, hint, error } = props;
  const container = useRef<HTMLDivElement>(null);
  const handlers = useRef(props);
  useEffect(() => {
    handlers.current = props;
  });

  useEffect(() => {
    const element = container.current;
    if (!element) return;
    let timer: number | undefined;
    let latest = 0;
    // Until a search answers there are no results yet, which is not the same as none found.
    let searching = false;
    const noResults = () => (searching ? "Searching…" : "No companies found");
    accessibleAutocomplete<CompanySearchResult>({
      element,
      id,
      name: id,
      minLength: 2,
      displayMenu: "overlay",
      confirmOnBlur: false,
      inputClasses: "govuk-input",
      source: (query, populate) => {
        window.clearTimeout(timer);
        const request = ++latest;
        searching = true;
        populate([]);
        timer = window.setTimeout(() => {
          handlers.current.search(query).then(
            (companies) => {
              if (request !== latest) return;
              searching = false;
              populate(companies);
            },
            (failure: unknown) => {
              if (request !== latest) return;
              searching = false;
              populate([]);
              handlers.current.onSearchError(failure);
            },
          );
        }, SEARCH_DELAY_MS);
      },
      onConfirm: (company) => {
        if (company) handlers.current.onChoose(company);
      },
      templates: { inputValue: (company) => company?.name ?? "", suggestion },
      tNoResults: noResults,
      tStatusQueryTooShort: (length) => `Type ${length} or more characters to search`,
      tStatusNoResults: noResults,
    });
    return () => {
      window.clearTimeout(timer);
      element.replaceChildren();
    };
  }, [id]);

  return (
    <div className={error ? "govuk-form-group govuk-form-group--error" : "govuk-form-group"}>
      <label className="govuk-label govuk-label--s" htmlFor={id}>
        {label}
        {error ? <span className="govuk-visually-hidden">. Error: {error}</span> : null}
      </label>
      <div className="govuk-hint">{hint}</div>
      {error ? (
        <p className="govuk-error-message" id={`${id}-error`}>
          <span className="govuk-visually-hidden">Error:</span> {error}
        </p>
      ) : null}
      <div ref={container} />
    </div>
  );
}
