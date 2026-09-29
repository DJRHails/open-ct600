/**
 * Types for the standalone build of alphagov's accessible-autocomplete (3.0.2), which bundles its
 * own Preact and renders into ``element``. Only the options this service uses are declared; see
 * the package README for the rest.
 */
declare module "accessible-autocomplete" {
  type Populate<T> = (results: T[]) => void;

  export type AutocompleteOptions<T> = {
    element: HTMLElement;
    id: string;
    name?: string;
    source: (query: string, populateResults: Populate<T>) => void;
    onConfirm?: (confirmed: T | undefined) => void;
    templates?: {
      inputValue?: (suggestion: T | undefined) => string;
      /** Returns HTML: escape anything that is not trusted. */
      suggestion?: (suggestion: T | string) => string;
    };
    minLength?: number;
    displayMenu?: "inline" | "overlay";
    confirmOnBlur?: boolean;
    showNoOptionsFound?: boolean;
    defaultValue?: string;
    inputClasses?: string;
    tNoResults?: () => string;
    tStatusQueryTooShort?: (minQueryLength: number) => string;
    tStatusNoResults?: () => string;
    tStatusResults?: (length: number, contentSelectedOption: string) => string;
    tAssistiveHint?: () => string;
  };

  export default function accessibleAutocomplete<T>(options: AutocompleteOptions<T>): void;
}

declare module "accessible-autocomplete/dist/accessible-autocomplete.min.css";
