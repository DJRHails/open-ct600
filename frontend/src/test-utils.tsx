import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { vi } from "vitest";

import { App } from "@/App";
import { RETURNS_KEY, STORAGE_VERSION } from "@/filing/returns/savedReturns";

export type Reply = { status: number; body: unknown };

/** Stub the network: each request to ``/api<path>`` gets the reply the handler returns. */
export function stubApi(handler: (path: string, body: unknown) => Reply) {
  const fetchMock = vi.fn<typeof fetch>(async (input, init) => {
    const path = String(input).replace(/^\/api/, "");
    const body: unknown = init?.body ? JSON.parse(String(init.body)) : undefined;
    const reply = handler(path, body);
    return new Response(JSON.stringify(reply.body), {
      status: reply.status,
      headers: { "Content-Type": "application/json" },
    });
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

/** The JSON body of the n-th stubbed request. */
export function requestBody(fetchMock: ReturnType<typeof stubApi>, index = 0): unknown {
  const init = fetchMock.mock.calls[index]?.[1];
  return init?.body ? JSON.parse(String(init.body)) : undefined;
}

/** The JSON body of the last stubbed request to ``/api<path>``. */
export function bodySentTo(fetchMock: ReturnType<typeof stubApi>, path: string): unknown {
  const call = fetchMock.mock.calls.findLast(([input]) => String(input) === `/api${path}`);
  const init = call?.[1];
  return init?.body ? JSON.parse(String(init.body)) : undefined;
}

/** Save ``draft`` as the only return in this browser, open on the filing pages. */
export function seedDraft(draft: object) {
  const saved = {
    id: "seeded-return",
    created_at: "2026-09-01T09:00:00.000Z",
    updated_at: "2026-09-01T09:00:00.000Z",
    draft,
  };
  const store = { version: STORAGE_VERSION, currentId: saved.id, returns: [saved] };
  window.localStorage.setItem(RETURNS_KEY, JSON.stringify(store));
}

/** The stored answers of the return open on the filing pages; ``{}`` if none is open. */
export function openDraft() {
  const stored = JSON.parse(window.localStorage.getItem(RETURNS_KEY) ?? "null");
  if (!stored) return {};
  const open = stored.returns.find((saved: { id: string }) => saved.id === stored.currentId);
  return open?.draft ?? {};
}

export function renderApp(path: string) {
  const user = userEvent.setup();
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
  return user;
}
