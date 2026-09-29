import "@/styles.scss";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router";

import { App } from "@/App";
import { markGovukFrontendSupported } from "@/supported";

// Before rendering: GOV.UK Frontend's components check for this class when they initialise.
markGovukFrontendSupported(document.body);

const root = document.getElementById("root");
if (!root) throw new Error("index.html is missing the #root element");

createRoot(root).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
