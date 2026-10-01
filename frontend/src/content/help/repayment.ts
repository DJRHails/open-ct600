/**
 * Help for the bank details for a repayment, CT600 boxes 920 to 940. Sources: the Company Tax
 * Return guide, https://www.gov.uk/guidance/the-company-tax-return-guide ("Overpayments and
 * repayments" and "Bank details (for person to whom the repayment is to be made)").
 */
import type { HmrcRef, QuestionHelp } from "@/content/help/types";
import type { RepaymentAnswers } from "@/filing/repayment";

const GUIDE = "the-company-tax-return-guide";

/** Why HMRC needs the details, and when. */
const WHY_HMRC_NEEDS_THEM: HmrcRef[] = [
  {
    quote: {
      guide: GUIDE,
      heading: "Bank details (for person to whom the repayment is to be made)",
      paragraphs: [
        "The quickest and safest method of repayment is a direct transfer from HMRC to your nominated bank or building society account. If you’re submitting more than one return at the same time, you must enter the account details on each return. It’s best to do this whether or not you think a repayment is due.",
        "To avoid delays in receiving your payment, you need to enter account details if you are claiming:",
      ],
    },
  },
  {
    quote: {
      guide: GUIDE,
      heading: "Overpayments and repayments",
      paragraphs: [
        "HMRC can make repayments direct to a bank or building society account but, for security reasons, only the details entered in boxes 920 to 940 from your latest return will be used.",
      ],
    },
  },
];

export const REPAYMENT_HELP: Record<keyof RepaymentAnswers, QuestionHelp> = {
  bank_name: {
    topic: "the bank or building society",
    plain: {
      meaning: [
        "The name of the bank or building society that holds the company’s account. HMRC pays money due back to the company into it, such as a payable R&D tax credit or tax the company overpaid.",
      ],
      example: [
        "The company’s account is with a high street bank: enter the bank’s name as it appears on the company’s bank statements.",
      ],
      excludes: ["The branch’s address. HMRC does not need it."],
      effect: [
        "We put it in box 920 of the return. HMRC only uses the account on the company’s latest return, so give it on every return.",
      ],
    },
    hmrc: [{ box: "920" }, ...WHY_HMRC_NEEDS_THEM],
  },
  account_name: {
    topic: "the name on the account",
    plain: {
      meaning: [
        "The name the account is in, as it appears on the bank statements. For the company’s own account this is usually the company’s name.",
      ],
      example: ["The account is in the name of Acme Widgets Ltd: enter Acme Widgets Ltd."],
      excludes: [
        "An account in someone else’s name. HMRC pays someone other than the company only if the company nominates them on the return, which this service does not do.",
      ],
      effect: ["We put it in box 935 of the return. HMRC’s form takes up to 28 characters."],
    },
    hmrc: [{ box: "935" }],
  },
  sort_code: {
    topic: "the sort code",
    plain: {
      meaning: [
        "The 6-digit number that identifies the bank branch. It is on the company’s bank statements and cards.",
      ],
      example: ["A sort code of 30-94-30 can be entered as 30-94-30, 30 94 30 or 309430."],
      excludes: ["The account number, which is asked separately."],
      effect: ["We put its 6 digits in box 925 of the return."],
    },
    hmrc: [{ box: "925" }],
  },
  account_number: {
    topic: "the account number",
    plain: {
      meaning: ["The 8-digit number of the company’s account, on its bank statements."],
      example: [
        "Some older accounts have a 7-digit number, like 7334450. Add a zero to the start to make 8 digits: 07334450.",
      ],
      excludes: ["The sort code and any building society roll number, which are asked separately."],
      effect: ["We put it in box 930 of the return."],
    },
    hmrc: [{ box: "930" }],
  },
  building_society_reference: {
    topic: "a building society roll number",
    plain: {
      meaning: [
        "Some building society accounts have a roll number as well as a sort code and account number. It identifies the account within the building society.",
      ],
      example: [
        "The account’s roll number is 1234/567-8: enter it as it is written, with any letters, slashes or hyphens.",
      ],
      excludes: ["Bank accounts, which do not have roll numbers. Leave it blank for them."],
      effect: [
        "We put it in box 940 of the return. If the account has no roll number, the box is left blank.",
      ],
    },
    hmrc: [{ box: "940" }],
  },
};
