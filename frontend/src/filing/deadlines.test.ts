import cases from "../../../backend/tests/fixtures/deadlines.json";

import { filingDeadline, paymentDeadline } from "@/filing/deadlines";

describe("deadlines", () => {
  it.each(cases)("match the backend's for $case", (deadline) => {
    expect(paymentDeadline(deadline.period_end)).toBe(deadline.payment_due);
    expect(filingDeadline(deadline.period_end)).toBe(deadline.filing_due);
  });

  it("cover month ends, leap years and short Februaries", () => {
    const ends = cases.map((deadline) => deadline.period_end);
    expect(ends).toEqual(expect.arrayContaining(["2024-02-29", "2023-05-29", "2022-05-30"]));
  });
});
