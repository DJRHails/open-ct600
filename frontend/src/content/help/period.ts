/**
 * Help for the accounting period questions, written from HMRC's guidance:
 * https://www.gov.uk/corporation-tax-accounting-period,
 * https://www.gov.uk/first-company-accounts-and-return, https://www.gov.uk/company-tax-returns
 * (the filing deadline) and https://www.gov.uk/pay-corporation-tax (the payment deadline).
 */
import type { QuestionHelp } from "@/content/help/types";

export const PERIOD_HELP: Record<"start" | "end", QuestionHelp> = {
  start: {
    topic: "the start of the accounting period",
    plain: {
      meaning: [
        "The first day of the period this Company Tax Return covers, called the accounting period for Corporation Tax.",
        "It is usually the first day of the financial year covered by the company's accounts, and the day after the end of the last return's period.",
        "The first accounting period usually starts when the company starts trading, which may be later than the day it was set up. HMRC's letter about the company's accounting period, or your business tax account, shows the dates.",
      ],
      example: [
        "The company's last return covered 1 April 2024 to 31 March 2025. This return starts on 1 April 2025.",
        "A company set up on 11 May 2025 that started trading on 22 July 2025 has a first accounting period that starts on 22 July 2025.",
      ],
      excludes: ["The date the company was set up, if it did not start trading until later."],
      effect: [
        "We show the date in box 30. It decides which tax rates and rules apply. For example, research and development claims for periods starting on or after 1 April 2024 use the merged scheme or enhanced R&D intensive support.",
      ],
    },
    hmrc: [
      { box: "30" },
      {
        quote: {
          guide: "corporation-tax-accounting-period",
          heading: "If your accounts cover more than 12 months",
          paragraphs: [
            "You must file 2 returns to cover the period of your accounts because your accounting period cannot be longer than 12 months.",
          ],
        },
      },
    ],
  },
  end: {
    topic: "the end of the accounting period",
    plain: {
      meaning: [
        "The last day of the period this return covers. It is usually the last day of the company's financial year, the date its accounts are made up to.",
        "An accounting period cannot be longer than 12 months. If the company's accounts cover more than 12 months, it must file 2 returns: one for the first 12 months and one for the rest.",
      ],
      example: [
        "The accounting period starts on 1 April 2025 and the accounts are made up to 31 March 2026. Enter 31 March 2026.",
        "A company set up and trading from 11 May 2025 makes its first accounts up to 31 May 2026. That is more than 12 months, so it files one return for 11 May 2025 to 10 May 2026 and another for 11 May 2026 to 31 May 2026.",
      ],
      excludes: [
        "The date the directors approved the accounts, or the date you file them.",
        "Accounts that cover more than 12 months. We prepare the accounts for the same dates as the return, so this service cannot file returns for them.",
      ],
      effect: [
        "We show the date in box 35. The company must file this return within 12 months after this date, and usually pay its Corporation Tax 9 months and 1 day after it.",
        "For a period ending on 31 March 2026, the tax is due by 1 January 2027 and the return by 31 March 2027. Companies with profits of more than £1.5 million usually pay in instalments instead. The £1.5 million is divided between the company and any associated companies, and reduced for a period shorter than 12 months. A company that was not over the limit in the previous 12 months usually does not pay in instalments if its profits are not more than £10 million.",
      ],
    },
    hmrc: [
      { box: "35" },
      {
        quote: {
          guide: "company-tax-returns",
          heading: "Deadlines",
          paragraphs: [
            "The deadline for your tax return is 12 months after the end of the accounting period it covers. You’ll have to pay a penalty for late filing if you miss the deadline.",
            "There’s a separate deadline to pay your Corporation Tax bill. It’s usually 9 months and one day after the end of the accounting period.",
          ],
        },
      },
    ],
  },
};
