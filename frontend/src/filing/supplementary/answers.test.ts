import type { SpecNode } from "@/api";
import { convertPage, type RawTree, xsdPattern } from "@/filing/supplementary/answers";
import { hmrcProblemLink, rejectedAnswerLink } from "@/filing/supplementary/links";
import { choiceKey, formItems, pageScreens, withComputed } from "@/filing/supplementary/spec";
import { schemaPage, schemaPages } from "@/test-schema";

const CT600A = schemaPage("A");

function loans(...entries: RawTree[]): RawTree {
  return {
    LoansByCloseCompanies: {
      BeforeEndPeriod: "no",
      LoansInformation: { Loan: entries, TotalLoans: "5,000", TaxChargeable: "1,687.50" },
      TaxPayable: "1687.50",
    },
  };
}

function messages(raw: RawTree, page = CT600A) {
  return convertPage(page, raw).problems.map((problem) => problem.message);
}

function walk(node: SpecNode): SpecNode[] {
  return [node, ...node.children.flatMap(walk)];
}

describe("pageScreens", () => {
  it("asks for each top-level group of CT600A on its own screen", () => {
    const screens = pageScreens(CT600A);

    expect(screens.map((screen) => screen.id)).toEqual([
      "BeforeEndPeriod",
      "LoansInformation",
      "ReliefEarlierThan",
      "LoanLaterReliefNow",
      "TotalLoansOutstanding",
    ]);
    expect(screens[1]?.title).toBe("Loans information");
    expect(screens[4]?.title).toBe(`${CT600A.title} (continued)`);
  });

  it("looks through a root element that only wraps one group", () => {
    const [first] = pageScreens(schemaPage("F"));

    expect(first?.path).toEqual(["TonnageTax", "TonnageTax"]);
    expect(first?.id).toBe("Information");
  });

  it("never asks for boxes the service works out, nor groups it works out entirely", () => {
    const later = ["A50A", "A50B", "A50C", "A50D", "A55", "A60", "A65", "A70"];
    const page = withComputed({ ...CT600A, computed: ["A15", "A20", "A80", ...later] });
    const names = (node: SpecNode) =>
      formItems(node).map((item) => (item.type === "node" ? item.node.name : item.id));
    const loansInformation = page.node.children.find((child) => child.name === "LoansInformation");

    expect(names(page.node)).toEqual([
      "BeforeEndPeriod",
      "LoansInformation",
      "ReliefEarlierThan",
      "TotalLoansOutstanding",
    ]);
    expect(loansInformation && names(loansInformation)).toEqual(["Loan"]);
    expect(pageScreens(page).map((screen) => screen.id)).not.toContain("LoanLaterReliefNow");
  });

  it("asks everything when the service calculates nothing", () => {
    const page = withComputed({ ...CT600A, computed: [] });

    expect(formItems(page.node)).toHaveLength(CT600A.node.children.length);
  });
});

describe("convertPage", () => {
  it("builds the element tree the service checks, with every value a string", () => {
    const converted = convertPage(
      CT600A,
      loans({ Name: " Ada Lovelace ", AmountOfLoan: "£5,000" }),
    );

    expect(converted.problems).toEqual([]);
    expect(converted.value).toEqual({
      BeforeEndPeriod: "no",
      LoansInformation: {
        Loan: [{ Name: "Ada Lovelace", AmountOfLoan: "5000" }],
        TotalLoans: "5000",
        TaxChargeable: "1687.50",
      },
      TaxPayable: "1687.50",
    });
  });

  it("asks for required answers but leaves blank optional groups out", () => {
    const converted = convertPage(CT600A, {});

    expect(converted.problems.map((problem) => problem.path)).toEqual([
      ["LoansByCloseCompanies", "BeforeEndPeriod"],
      ["LoansByCloseCompanies", "TaxPayable"],
    ]);
    expect(converted.problems[1]?.message).toBe("Enter tax payable s419");
    expect(converted.value).toEqual({});
  });

  it("names the list item a problem is in and ignores blank items", () => {
    const converted = convertPage(
      CT600A,
      loans({ Name: "Ada Lovelace", AmountOfLoan: "5000" }, { Name: "C£", AmountOfLoan: "-3" }, {}),
    );

    expect(converted.problems).toMatchObject([
      {
        path: ["LoansByCloseCompanies", "LoansInformation", "Loan", 1, "Name"],
        message: "Name of participator or associate contains a character that is not allowed",
        context: "loan 2",
      },
      { message: "Amount of loan cannot be negative", context: "loan 2" },
    ]);
  });

  it("needs at least one loan once the loans information is answered", () => {
    expect(messages(loans())).toEqual(["Add at least one loan"]);
  });

  it("checks amounts, dates and lengths as the service does", () => {
    const raw: RawTree = {
      LoansByCloseCompanies: {
        BeforeEndPeriod: "maybe",
        ReliefEarlierThan: {
          Loan: [
            { Name: "A", AmountRepaid: "0", Date: { day: "31", month: "2", year: "2025" } },
            { Name: "Ada", AmountRepaid: "12.5", Date: { day: "31", month: "1", year: "2025" } },
          ],
          TotalLoans: "100",
          ReliefDue: "1.234",
        },
        TaxPayable: "0",
      },
    };

    expect(messages(raw)).toEqual([
      "Select yes or no for have loans made during the period been released, or written off before the end of the period?",
      "Enter name of participator or associate, 2 to 56 characters",
      "Amount repaid must be £1 or more",
      "Date of repayment, release or write off must be a real date",
      "Amount repaid must be a whole number of pounds, like 1234",
      "Relief due must be an amount in pounds and pence, like 1234.56",
    ]);
  });

  it("gives dates as ISO dates", () => {
    const loan = { Name: "Ada", Date: { day: "31", month: "1", year: "2025" } };
    const relief = { Loan: [loan], TotalLoans: "100", ReliefDue: "12.50" };
    const raw = {
      LoansByCloseCompanies: { BeforeEndPeriod: "no", ReliefEarlierThan: relief, TaxPayable: "0" },
    };

    expect(convertPage(CT600A, raw).value.ReliefEarlierThan).toEqual({
      Loan: [{ Name: "Ada", Date: "2025-01-31" }],
      TotalLoans: "100",
      ReliefDue: "12.50",
    });
  });

  it("keeps only the branch of a choice the user chose", () => {
    const cfc = schemaPage("B");
    const company = {
      Name: "Overseas Ltd",
      Territory: "Jersey",
      [choiceKey("ExemptionDue|CFCTaxCalculation")]: "CFCTaxCalculation",
      ExemptionDue: "Left over from before",
      CFCTaxCalculation: {
        Percentage: "50",
        ChargeableProfits: "1000",
        TaxOnChargeable: "250",
        CFCchargeDue: "250",
      },
    };
    const converted = convertPage(cfc, {
      ControlledForeignCompanies: { CompanyInformation: [company] },
    });

    expect(converted.problems).toEqual([]);
    expect(converted.value).toEqual({
      CompanyInformation: [
        {
          Name: "Overseas Ltd",
          Territory: "Jersey",
          CFCTaxCalculation: {
            Percentage: "50",
            ChargeableProfits: "1000",
            TaxOnChargeable: "250",
            CFCchargeDue: "250",
          },
        },
      ],
    });
  });

  it("asks which branch applies when a required choice is unanswered", () => {
    const cfc = schemaPage("B");
    const raw = { ControlledForeignCompanies: { CompanyInformation: [{ Name: "Overseas Ltd" }] } };

    expect(messages(raw, cfc)).toContain("Select exemption due (if any) or CFCTaxCalculation");
  });

  it("answers a tick-box branch by choosing it", () => {
    const charity = schemaPage("E");
    const raw = {
      Charity: {
        ClaimExemption: {
          Status: {
            ClaimingExemptionAllOrPart: "yes",
            AllCharitable: { [choiceKey("AllExempt|SomeNotOnlyCharitable")]: "AllExempt" },
          },
        },
      },
    };

    expect(convertPage(charity, raw)).toEqual({
      value: {
        ClaimExemption: {
          Status: { ClaimingExemptionAllOrPart: "yes", AllCharitable: { AllExempt: "yes" } },
        },
      },
      problems: [],
    });
  });

  it("accepts only the listed values of an enumeration", () => {
    const tonnage = schemaPage("F");
    const information = { TrainingCertificate: "na", CompanyMetCharteredInLimit: "maybe" };
    const found = messages({ TonnageTax: { TonnageTax: { Information: information } } }, tonnage);

    expect(found).toContain(
      "Select the company met the prescribed limit on chartered-in tonnage from the list",
    );
    expect(found.join()).not.toMatch(/training certificate/);
  });
});

describe("xsdPattern", () => {
  it("compiles every pattern in HMRC's supplementary pages", () => {
    const patterns = schemaPages().flatMap((page) =>
      walk(page.node).flatMap((node) => node.patterns),
    );

    expect(patterns.length).toBeGreaterThan(50);
    for (const pattern of patterns) expect(() => xsdPattern(pattern)).not.toThrow();
  });

  it("matches the whole value, as XSD patterns do", () => {
    expect(xsdPattern("[0-9]{10}").test("1234567890")).toBe(true);
    expect(xsdPattern("[0-9]{10}").test("12345678901")).toBe(false);
  });
});

describe("links to the answer at fault", () => {
  it("follows HMRC's element path to the field on its screen", () => {
    const path = "/IRenvelope/CompanyTaxReturn/LoansByCloseCompanies/LoansInformation/Loan[2]/Name";

    expect(hmrcProblemLink(schemaPages(), path)).toBe(
      "/file/supplementary-pages/A/LoansInformation?change=1&check=1&from=check" +
        "#A-LoansByCloseCompanies-LoansInformation-Loan-1-Name",
    );
    expect(hmrcProblemLink(schemaPages(), "/IRenvelope/CompanyTaxReturn/Turnover")).toBeNull();
  });

  it("follows the service's location for a rejected answer, to a date's day input", () => {
    const location = ["supplementary_pages", "A", "ReliefEarlierThan", "Loan", "0", "Date"];

    expect(rejectedAnswerLink(schemaPages(), location)).toBe(
      "/file/supplementary-pages/A/ReliefEarlierThan?change=1&check=1&from=check" +
        "#A-LoansByCloseCompanies-ReliefEarlierThan-Loan-0-Date-day",
    );
  });
});
