import {
  formatDate,
  formatMoney,
  formatPercent,
  formatPounds,
  parseDateParts,
  parseWholePounds,
  twelveMonthPeriodEnd,
} from "@/format";

describe("parseWholePounds", () => {
  it.each([
    ["120000", 120_000],
    ["£120,000", 120_000],
    [" 1 250 ", 1_250],
    ["", 0],
  ])("reads %j as %d", (raw, expected) => {
    expect(parseWholePounds(raw, "turnover")).toEqual({ ok: true, value: expected });
  });

  it.each([
    ["", "Enter turnover", true],
    ["12.50", "Enter turnover in whole pounds, without pence", false],
    ["-5", "Turnover cannot be negative", false],
    ["twelve", "Turnover must be a number, like 12500", false],
    ["100000000000", "Turnover must be £99,999,999,999 or less", false],
  ])("rejects %j", (raw, error, required) => {
    expect(parseWholePounds(raw, "turnover", required)).toEqual({ ok: false, error });
  });
});

describe("parseDateParts", () => {
  it("builds an ISO date", () => {
    expect(parseDateParts({ day: "1", month: "4", year: "2025" }, "start date")).toEqual({
      ok: true,
      value: "2025-04-01",
    });
  });

  it.each([
    [{ day: "", month: "", year: "" }, "Enter the start date"],
    [{ day: "1", month: "", year: "2025" }, "Start date must include a month"],
    [{ day: "", month: "", year: "2025" }, "Start date must include a day and month"],
    [{ day: "31", month: "2", year: "2025" }, "Start date must be a real date"],
    [{ day: "1", month: "4", year: "25" }, "Start date must be a real date"],
  ])("rejects %j", (parts, error) => {
    expect(parseDateParts(parts, "start date")).toEqual({ ok: false, error });
  });
});

describe("twelveMonthPeriodEnd", () => {
  it.each([
    ["2025-04-01", "2026-03-31"],
    ["2024-01-01", "2024-12-31"],
    ["2024-02-29", "2025-02-28"],
    ["2023-03-01", "2024-02-29"],
  ])("a period starting %s ends by %s", (start, end) => {
    expect(twelveMonthPeriodEnd(start)).toBe(end);
  });
});

describe("formatting", () => {
  it("uses GOV.UK styles", () => {
    expect(formatMoney("22750.00")).toBe("£22,750.00");
    expect(formatPercent("0.2275")).toBe("22.75%");
    expect(formatPercent("25.00", false)).toBe("25%");
    expect(formatDate("2026-01-01")).toBe("1 January 2026");
    expect(formatPounds(-0)).toBe("£0");
    expect(formatMoney(-Number("0.00"))).toBe("£0.00");
  });
});
