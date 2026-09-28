import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, beforeEach, vi } from "vitest";

beforeEach(() => {
  // index.html adds this class before React starts; GOV.UK Frontend JS requires it.
  document.body.classList.add("govuk-frontend-supported");
  // Tests do not load styles.scss, which defines the breakpoint the menu toggle reads.
  document.documentElement.style.setProperty("--govuk-breakpoint-tablet", "40.0625rem");
  window.matchMedia = vi.fn<typeof window.matchMedia>((query) => {
    const list = new EventTarget() as MediaQueryList;
    return Object.assign(list, { matches: true, media: query, onchange: null });
  });
  vi.spyOn(window, "scrollTo").mockImplementation(() => undefined);
  Element.prototype.scrollIntoView = vi.fn<typeof Element.prototype.scrollIntoView>();
});

afterEach(() => {
  cleanup();
  window.localStorage.clear();
  window.sessionStorage.clear();
  vi.unstubAllGlobals();
});
