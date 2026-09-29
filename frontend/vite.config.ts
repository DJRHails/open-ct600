import react from "@vitejs/plugin-react";
import { NodePackageImporter } from "sass-embedded";
import { createLogger } from "vite";
import { defineConfig } from "vitest/config";

import packageJson from "./package.json" with { type: "json" };

// GOV.UK Frontend's service navigation still ships an Internet Explorer 11 media query hack,
// `(min-width: 0\0)`, which LightningCSS reports while dropping it. The query only ever
// matched IE, so dropping it is correct; hide exactly that report and nothing else.
const logger = createLogger();
const warn = logger.warn.bind(logger);
logger.warn = (message, options) => {
  if (message.includes("Invalid media query") && message.includes("min-width: 0\\0")) return;
  warn(message, options);
};

export default defineConfig({
  customLogger: logger,
  define: { APP_VERSION: JSON.stringify(packageJson.version) },
  plugins: [react()],
  resolve: {
    alias: { "@": new URL("./src", import.meta.url).pathname },
  },
  css: {
    lightningcss: { errorRecovery: true },
    preprocessorOptions: {
      scss: { importers: [new NodePackageImporter()] },
    },
  },
  server: {
    proxy: { "/api": "http://127.0.0.1:8000" },
    // Tests read HMRC's page definitions from the backend's committed schema spec, the
    // boxes the service calculates from its page definitions, and HMRC's saved guides.
    fs: {
      allow: [
        ".",
        "../backend/src/open_ct600/schema",
        "../backend/src/open_ct600/pages",
        "../specs/hmrc/guidance",
      ],
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test-setup.ts"],
    css: false,
  },
});
