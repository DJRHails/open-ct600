/**
 * Help for the balance sheet questions: the items of the micro-entity balance sheet (FRS 105),
 * which have no boxes on the return. Written from Companies House's guidance,
 * https://www.gov.uk/annual-accounts and
 * https://www.gov.uk/government/publications/filing-your-companies-house-accounts/life-of-a-company-part-1-accounts,
 * and HMRC's https://www.gov.uk/guidance/the-company-tax-return-guide (box 80) and
 * https://www.gov.uk/directors-loans.
 */
import type { HmrcRef, QuestionHelp } from "@/content/help/types";
import type { BALANCE_SHEET } from "@/filing/model";

type Key = (typeof BALANCE_SHEET)["fields"][number]["key"];

/** The accounts, with their balance sheet, go with the return (box 80). */
const ACCOUNTS: HmrcRef = { box: "80" };

const BALANCE_SHEET_MEANING: HmrcRef = {
  quote: {
    guide: "annual-accounts",
    heading: "How to put together statutory accounts",
    paragraphs: [
      "Statutory accounts must include:",
      "a ‘balance sheet’, which shows the value of everything the company owns, owes and is owed on the last day of the financial year",
    ],
  },
};

const BALANCE_SHEET_TOTAL: HmrcRef = {
  quote: {
    guide: "life-of-a-company-part-1-accounts",
    heading: "8. Company size thresholds",
    paragraphs: [
      "To determine whether your company is a micro-entity, small or medium-sized, there are thresholds for:",
      "balance sheet total (meaning the total of the fixed and current assets)",
    ],
  },
};

export const BALANCE_SHEET_HELP: Record<Key, QuestionHelp> = {
  called_up_share_capital_not_paid: {
    topic: "called up share capital not paid",
    plain: {
      meaning: [
        "Money shareholders still owe the company for shares it has issued and asked them to pay for.",
        "Many small companies issue a few £1 shares when they are set up, and the shareholders do not pay for them straight away. Any amount still unpaid at the end of the period goes here.",
      ],
      example: [
        "The company issued 100 shares of £1 each when it was set up. The shareholders have not paid the £100. Enter £100 here, and £100 as called up share capital.",
      ],
      excludes: [
        "Shares the shareholders have paid for.",
        "Money a director or shareholder owes the company for other reasons, such as an overdrawn director's loan account. Include that in current assets.",
      ],
      effect: [
        "We show it as the first line of the balance sheet in the company's accounts. It counts as an asset of the company.",
      ],
    },
    hmrc: [ACCOUNTS, BALANCE_SHEET_MEANING],
  },
  fixed_assets: {
    topic: "fixed assets",
    plain: {
      meaning: [
        "Things the company owns and keeps to use in the business for more than a year, such as equipment, computers, vehicles, furniture and property. Long-term investments, and intangible assets such as goodwill from buying a business, are fixed assets too.",
        "Enter what they cost, less the depreciation charged on them so far. This is called their net book value.",
      ],
      example: [
        "The company owns computers that cost £4,500. The accounts have charged £2,000 of depreciation on them so far. Enter £2,500.",
      ],
      excludes: [
        "Stock the company holds to sell. Include that in current assets.",
        "Things the company rents or leases but does not own.",
        "Small items that are used up within the year, like stationery.",
      ],
      effect: [
        "We show them on the balance sheet in the company's accounts. They count towards the balance sheet total, which decides whether the company is a micro-entity or small company.",
      ],
    },
    hmrc: [ACCOUNTS, BALANCE_SHEET_TOTAL],
  },
  current_assets: {
    topic: "current assets",
    plain: {
      meaning: [
        "Money the company has, and things it expects to turn into money within a year: cash at the bank and in hand, money customers and others owe it (debtors), and stock.",
        "If a director owes the company money at the end of the period, for example because their director's loan account is overdrawn, include it here as a debtor.",
      ],
      example: [
        "At the end of the period the company has £12,000 in the bank, customers owe it £4,500 and it has £1,500 of stock. Enter £18,000.",
      ],
      excludes: [
        "Prepayments and accrued income, which you enter separately.",
        "Called up share capital not paid, which you enter separately.",
        "Equipment and other fixed assets.",
      ],
      effect: [
        "We show them on the balance sheet in the company's accounts. We add prepayments and accrued income and take off creditors due within a year to show net current assets.",
      ],
    },
    hmrc: [ACCOUNTS, BALANCE_SHEET_TOTAL],
  },
  prepayments_and_accrued_income: {
    topic: "prepayments and accrued income",
    plain: {
      meaning: [
        "A prepayment is something the company paid for in this period that covers time after the period ends. Accrued income is money the company earned in the period but had not yet invoiced when it ended.",
      ],
      example: [
        "The company paid £1,200 on 1 January 2026 for a year's insurance. Its period ends on 31 March 2026, so 9 months, £900, is a prepayment.",
        "It also finished a £2,000 job in March 2026 but invoiced it in April. Enter £900 plus £2,000, which is £2,900.",
      ],
      excludes: [
        "Invoices customers have not paid yet. Include those in current assets.",
        "Amounts already included in current assets as part of debtors. Leave this blank if so, so they are not counted twice.",
      ],
      effect: [
        "We show them on the balance sheet in the company's accounts, as part of net current assets.",
      ],
    },
    hmrc: [ACCOUNTS, BALANCE_SHEET_MEANING],
  },
  creditors_within_one_year: {
    topic: "creditors due within one year",
    plain: {
      meaning: [
        "Amounts the company owes at the end of the period that it must pay within 12 months, such as bills from suppliers, VAT, PAYE, bank overdrafts, loan repayments due within the year and Corporation Tax.",
        "Include money the company owes a director, such as a director's loan account in credit.",
      ],
      example: [
        "The company owes suppliers £2,500, VAT of £3,000, Corporation Tax of £4,750 and £1,000 to a director. Enter £11,250.",
      ],
      excludes: [
        "Loan repayments due more than 12 months after the end of the period. Enter those as creditors due after more than one year.",
        "Accruals and deferred income, if you enter them separately.",
        "Share capital, which is not a debt.",
      ],
      effect: [
        "We show them on the balance sheet in the company's accounts and take them off current assets to show net current assets.",
        "Include the Corporation Tax the company owes for this period. We show that tax when you check your answers.",
      ],
    },
    hmrc: [ACCOUNTS, BALANCE_SHEET_MEANING],
  },
  creditors_after_one_year: {
    topic: "creditors due after more than one year",
    plain: {
      meaning: [
        "Amounts the company owes at the end of the period that it does not have to pay for more than 12 months, such as the later repayments of a bank loan or hire purchase agreement.",
      ],
      example: [
        "The company owes £30,000 on a bank loan. £6,000 is due in the next 12 months and £24,000 after that. Enter £24,000 here, and include the £6,000 in creditors due within one year.",
      ],
      excludes: [
        "Anything the company must pay within 12 months.",
        "Provisions for liabilities whose amount or timing is uncertain.",
      ],
      effect: [
        "We show them on the balance sheet in the company's accounts and take them off to show net assets.",
      ],
    },
    hmrc: [ACCOUNTS, BALANCE_SHEET_MEANING],
  },
  provisions: {
    topic: "provisions for liabilities",
    plain: {
      meaning: [
        "Amounts the company has set aside in its accounts for something it is likely to have to pay, where the amount or the date is not certain.",
      ],
      example: [
        "The company's office lease says it must redecorate when it leaves. It sets aside an estimated £3,000 for this. Enter £3,000.",
      ],
      excludes: [
        "Bills and debts whose amount is known. Enter those as creditors.",
        "Costs of the period that have not been invoiced yet. Enter those as accruals.",
      ],
      effect: [
        "We show them on the balance sheet in the company's accounts and take them off to show net assets.",
      ],
    },
    hmrc: [ACCOUNTS, BALANCE_SHEET_MEANING],
  },
  accruals_and_deferred_income: {
    topic: "accruals and deferred income",
    plain: {
      meaning: [
        "Accruals are costs that belong to the period but that the company had not been invoiced for when it ended. Deferred income is money customers paid in advance for work the company will do after the period ends.",
      ],
      example: [
        "The company will be invoiced £1,200 for accountancy work on this period's accounts. A customer paid £3,000 in March 2026 for work in April. The period ended on 31 March 2026, so enter £4,200.",
      ],
      excludes: [
        "Bills the company has received but not paid. Include those in creditors.",
        "Amounts already included in creditors due within one year. Leave this blank if so, so they are not counted twice.",
      ],
      effect: [
        "We show them on the balance sheet in the company's accounts and take them off to show net assets.",
      ],
    },
    hmrc: [ACCOUNTS, BALANCE_SHEET_MEANING],
  },
  called_up_share_capital: {
    topic: "called up share capital",
    plain: {
      meaning: [
        "The nominal value of the shares the company has issued and asked shareholders to pay for. The nominal value is the value printed on each share, often £1.",
      ],
      example: [
        "The company has issued 100 ordinary shares of £1 each. Enter £100, whether or not the shareholders have paid for them.",
      ],
      excludes: [
        "Any amount shareholders paid above the nominal value, called share premium. This service does not show share premium separately.",
        "The company's retained profits. We work out the profit and loss reserve for you, as net assets less share capital.",
      ],
      effect: [
        "We show it in the capital and reserves section of the balance sheet in the company's accounts.",
      ],
    },
    hmrc: [ACCOUNTS, BALANCE_SHEET_MEANING],
  },
};
