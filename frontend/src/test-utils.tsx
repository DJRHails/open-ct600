import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { vi } from "vitest";

import { App } from "@/App";

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

export function renderApp(path: string) {
  const user = userEvent.setup();
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
  return user;
}
