import { act, screen, waitFor, within } from "@testing-library/react";

import { renderApp, seedDraft, stubApi } from "@/test-utils";

function stubSubmission(enabled: boolean) {
  stubApi((path) =>
    path === "/submission"
      ? { status: 200, body: { enabled, environments: enabled ? ["live"] : [] } }
      : { status: 404, body: {} },
  );
}

describe("what you'll need", () => {
  it("says where to find each thing before the user starts", async () => {
    stubSubmission(false);
    renderApp("/file");

    const heading = screen.getByRole("heading", { name: "What you'll need" });
    const list = within(heading.nextElementSibling as HTMLElement);
    expect(list.getByText(/company registration number/)).toBeInTheDocument();
    expect(heading.nextElementSibling).toHaveTextContent(/certificate of incorporation/);
    expect(heading.nextElementSibling).toHaveTextContent(/10 digits/);
    expect(heading.nextElementSibling).toHaveTextContent(/form CT41G/);
    expect(heading.nextElementSibling).toHaveTextContent(/the UTR is the last 10 digits/);
    expect(
      list.getByRole("link", { name: "ask HMRC for a copy (opens in new tab)" }),
    ).toHaveAttribute(
      "href",
      "https://www.tax.service.gov.uk/ask-for-copy-of-your-corporation-tax-utr",
    );
    await waitFor(() => expect(fetch).toHaveBeenCalled());
    await act(() => Promise.resolve());
    expect(screen.queryByText(/Government Gateway/)).not.toBeInTheDocument();
  });

  it("asks for Government Gateway sign in details only where the service can send returns", async () => {
    stubSubmission(true);
    renderApp("/file");

    expect(await screen.findByText(/Government Gateway user ID and password/)).toBeInTheDocument();
    expect(screen.getByText(/can take up to 10 days/)).toBeInTheDocument();
  });
});

describe("deadlines", () => {
  it("are on the task list once the accounting period is saved", () => {
    stubSubmission(false);
    seedDraft({
      period: {
        start: { day: "1", month: "7", year: "2024" },
        end: { day: "30", month: "6", year: "2025" },
      },
    });
    renderApp("/file/tasks");

    const deadlines = screen.getByTestId("deadlines");
    expect(deadlines).toHaveTextContent("File your return by 30 June 2026");
    expect(deadlines).toHaveTextContent("Pay Corporation Tax by 1 April 2026");
    expect(deadlines).toHaveTextContent(/over £1.5 million, it usually pays in instalments/);
  });

  it("are not shown before the accounting period is known", () => {
    stubSubmission(false);
    renderApp("/file/tasks");

    expect(screen.queryByTestId("deadlines")).not.toBeInTheDocument();
  });
});
