/**
 * Help for the company details questions, written from HMRC's guidance:
 * https://www.gov.uk/guidance/the-company-tax-return-guide (boxes 1 to 4),
 * https://www.gov.uk/find-utr-number,
 * https://www.tax.service.gov.uk/ask-for-copy-of-your-corporation-tax-utr,
 * https://www.gov.uk/pay-corporation-tax (the payment reference),
 * https://www.gov.uk/corporation-tax-rates (the main rate),
 * https://www.gov.uk/guidance/corporation-tax-trading-and-non-trading (what a company does) and
 * the Company Taxation Manual (CTM60710 for close investment-holding companies). Type 3 follows
 * the guide's box 4 instruction: 0 in the first year of liquidation, 3 from the second, which
 * HMRC's business rule 9143 then charges at the main rate.
 */
import type { QuestionHelp } from "@/content/help/types";
import type { CompanyAnswers } from "@/filing/model";

export const COMPANY_HELP: Record<keyof CompanyAnswers, QuestionHelp> = {
  name: {
    topic: "the company name",
    plain: {
      meaning: [
        "The company's registered name, exactly as it appears on the Companies House register. This includes words like Limited or Ltd at the end.",
      ],
      example: [
        "The Companies House register shows the company as BRIGHT PIXEL STUDIO LTD. Enter Bright Pixel Studio Ltd.",
      ],
      excludes: [
        "A trading name or brand the company uses with customers, if it is different from the registered name.",
        "A name the company had before it changed its name. Use the name it has now.",
      ],
      effect: [
        "We show the name on the return, in box 1, and on the accounts and tax computations we prepare for you.",
      ],
    },
    hmrc: [{ box: "1" }],
  },
  registration_number: {
    topic: "the company registration number",
    plain: {
      meaning: [
        "The number Companies House gave the company when it was set up. It is also called the company number.",
        "It has 8 characters. Companies registered in England and Wales usually have 8 digits. Companies registered in Scotland start with SC and those in Northern Ireland start with NI.",
        "You can find it on the company's certificate of incorporation and on letters from Companies House. You can also search the Companies House register for the company's name.",
      ],
      example: [
        "The certificate of incorporation says Company No. 01234567. Enter 01234567, including the 0 at the start.",
        "A company registered in Scotland might have the number SC123456.",
      ],
      excludes: [
        "The company's Unique Taxpayer Reference (UTR), which comes from HMRC.",
        "The company's VAT registration number or PAYE reference.",
      ],
      effect: [
        "We show the number on the return, in box 2, and use it to identify the company in the accounts and tax computations we prepare.",
      ],
    },
    hmrc: [{ box: "2" }],
  },
  utr: {
    topic: "the Corporation Tax Unique Taxpayer Reference (UTR)",
    plain: {
      meaning: [
        "The company's 10-digit reference for Corporation Tax. HMRC sends it in a letter when the company is set up, called Corporation Tax: Company Unique Taxpayer Reference (UTR), or form CT41G.",
        "It is also on other letters from HMRC, such as a notice to deliver a Company Tax Return and payment reminders. There, it is the last 10 digits of the 13-digit number at the top of the letter.",
        "If you cannot find it, you can ask HMRC for a copy online. HMRC posts it to the company's registered office address.",
      ],
      example: [
        "The number at the top of a notice to file a return is 1231234567890. The company's UTR is the last 10 digits, so enter 1234567890.",
      ],
      excludes: [
        "A director's or shareholder's own UTR for Self Assessment.",
        "The company's 17-character payment reference, which you use to pay Corporation Tax.",
        "The company registration number from Companies House.",
      ],
      effect: [
        "We show it on the return, in box 3. HMRC uses it to match the return to the company, so check it carefully. If you claim research and development relief, it must match the UTR on the forms you send HMRC for the claim.",
      ],
    },
    hmrc: [
      { box: "3" },
      {
        quote: {
          guide: "find-utr-number",
          heading: "If you have a limited company",
          paragraphs: [
            "You can request your Corporation Tax UTR online. HMRC will send it to the business address that’s registered with Companies House.",
          ],
        },
      },
    ],
  },
  company_type: {
    topic: "the type of company",
    plain: {
      meaning: [
        "HMRC puts some companies in special categories that are taxed differently. Most companies, including most small trading companies, are none of these.",
        "A close investment-holding company is controlled by 5 or fewer people, or by its directors, and does not exist mainly to trade or to let property to people it is not connected with. A company that only holds shares and savings for its owners may be one.",
        "A company in liquidation is in its first year of liquidation for the first accounting period after the liquidation starts. Later periods are its second or later year.",
      ],
      example: [
        "A company that designs websites for clients and is owned by its 2 directors is none of these.",
        "A company that went into liquidation on 1 March 2025 and is now filing for the accounting period starting 1 March 2026 is in its second year of liquidation.",
      ],
      excludes: [
        "Community interest companies, which are none of these.",
        "Insurance companies and REIT C tax-exempt companies. This service cannot prepare their returns.",
      ],
      effect: [
        "We enter the type's code in box 4. Close investment-holding companies, companies in their second or later year of liquidation, REIT C residual companies and non-resident companies pay the main rate of 25% on all their profits. They cannot use the 19% small profits rate or marginal relief.",
        "HMRC's guide says to choose none of these in the first year of liquidation, unless another type applies, and the type for companies in liquidation from the second year on.",
      ],
    },
    hmrc: [
      {
        quote: {
          guide: "the-company-tax-return-guide",
          heading:
            "Company in liquidation which is chargeable at the main rate following the first period after liquidation",
          paragraphs: [
            "Enter 0, if the company is in the first year of liquidation, unless one of the other company types apply.",
            "Enter 3, if the company is in the second or later year of liquidation.",
          ],
        },
      },
      { box: "4" },
    ],
  },
  principal_activity: {
    topic: "the company's principal activity",
    plain: {
      meaning: [
        "A short description of the company's main business during the period, in a few words.",
      ],
      example: [
        "Software development.",
        "Retail sale of books through its own website.",
        "Letting and operating of property it owns.",
      ],
      excludes: [
        "A long list of everything the company does. Describe its main activity in a few words.",
        "The standard industrial classification (SIC) code on the Companies House register, which is a number. Describe the activity in words.",
      ],
      effect: [
        "We use it in the directors' report in the company's accounts, and to describe the company's trade in the tax computations. It does not change the tax the company pays.",
      ],
    },
    hmrc: [
      {
        quote: {
          guide: "corporation-tax-trading-and-non-trading",
          heading: "What is active for Corporation Tax purposes",
          paragraphs: [
            "Generally your company or organisation is considered to be active for Corporation Tax purposes when it is, for example:",
            "carrying on a business activity such as a trade or professional activity",
            "buying and selling goods with a view to making a profit or surplus",
            "providing services",
            "earning interest",
            "managing investments",
            "receiving any other income",
          ],
        },
      },
    ],
  },
};
