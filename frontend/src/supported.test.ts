import indexHtml from "../index.html?raw";

import { markGovukFrontendSupported } from "@/supported";

describe("the page shell", () => {
  it("has no inline scripts, so a strict Content-Security-Policy can forbid them", () => {
    const page = new DOMParser().parseFromString(indexHtml, "text/html");
    const inline = [...page.querySelectorAll("script")].filter((script) => !script.src);

    expect(inline.map((script) => script.outerHTML)).toEqual([]);
  });

  it("marks the body as running JavaScript that GOV.UK Frontend supports", () => {
    const body = document.createElement("body");
    body.className = "govuk-template__body";

    markGovukFrontendSupported(body);

    expect([...body.classList]).toEqual([
      "govuk-template__body",
      "js-enabled",
      "govuk-frontend-supported",
    ]);
  });
});
