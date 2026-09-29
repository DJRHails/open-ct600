/**
 * Help for the accounts details questions, written from Companies House's guidance,
 * https://www.gov.uk/government/publications/filing-your-companies-house-accounts/life-of-a-company-part-1-accounts
 * (the size limits, approving and signing accounts, and dormant company accounts) and
 * https://www.gov.uk/annual-accounts, HMRC's https://www.gov.uk/dormant-company and
 * https://www.gov.uk/guidance/the-company-tax-return-guide (box 80), and section 382(6) of the
 * Companies Act 2006 (the average number of employees).
 */
import type { HmrcRef, QuestionHelp } from "@/content/help/types";
import type { AccountsAnswers } from "@/filing/model";

/** The accounts go with the return (box 80). */
const ACCOUNTS: HmrcRef = { box: "80" };

const COMPANIES_HOUSE = "life-of-a-company-part-1-accounts";

const APPROVING_AND_SIGNING = "3.3 Approving and signing accounts";

export const ACCOUNTS_HELP: Record<keyof AccountsAnswers, QuestionHelp> = {
  standard: {
    topic: "micro-entity and small company accounts",
    plain: {
      meaning: [
        "Micro-entity accounts follow FRS 105, the simplest accounting standard, meant for the smallest companies. Small company accounts follow section 1A of FRS 102 and give a little more detail.",
        "A company can prepare micro-entity accounts if it meets at least 2 of these: turnover of £1 million or less, a balance sheet total of £500,000 or less, and 10 employees or fewer on average. For small company accounts the limits are £15 million, £7.5 million and 50 employees.",
        "These limits are for accounting periods starting on or after 6 April 2025. For earlier periods, the micro-entity limits were £632,000 of turnover and a £316,000 balance sheet total, and the small company limits £10.2 million and £5.1 million. After its first year, a company's size depends on this year and the year before.",
      ],
      example: [
        "A company's period starts on 1 July 2025. It has turnover of £420,000, a balance sheet total of £90,000 and 3 employees. It meets all 3 micro-entity conditions, so it can prepare micro-entity accounts.",
      ],
      excludes: [
        "Charities, public companies, and parent companies that prepare group accounts, which cannot prepare micro-entity accounts.",
        "Medium-sized and large companies, and accounts under international standards. This service cannot prepare those.",
      ],
      effect: [
        "We prepare the company's accounts in this format, tagged in iXBRL so they can go with the return. Both use the micro-entity balance sheet you entered.",
        "Micro-entity accounts use the micro-entity profit and loss account. Small company accounts show cost of sales, gross profit and administrative expenses.",
      ],
    },
    hmrc: [
      ACCOUNTS,
      {
        quote: {
          guide: COMPANIES_HOUSE,
          heading: "For accounting periods that begin on or after 6 April 2025",
          paragraphs: [
            "A micro-entity must meet at least 2 of the following conditions:",
            "an annual turnover no more than £1 million",
            "a balance sheet total no more than £500,000",
            "no more than 10 employees on average",
          ],
        },
      },
      {
        quote: {
          guide: COMPANIES_HOUSE,
          heading: "For accounting periods beginning between 30 September 2013 and 5 April 2025",
          paragraphs: [
            "A micro-entity must have met at least 2 of the following conditions:",
            "an annual turnover no more than £632,000",
            "a balance sheet total no more than £316,000",
            "no more than 10 employees on average",
          ],
        },
      },
    ],
  },
  directors: {
    topic: "the company's directors",
    plain: {
      meaning: [
        "Everyone who was a director of the company at any time during the accounting period, including anyone who joined or left during it.",
        "Use each director's full name, as it appears on the Companies House register.",
      ],
      example: [
        "Priya Shah was a director for the whole period. Tom Evans resigned on 30 September 2025, part-way through the period. List both of them.",
      ],
      excludes: [
        "Company secretaries, shareholders and accountants who are not directors.",
        "Directors who left before the period started or joined after it ended.",
      ],
      effect: [
        "We list them in the directors' report in the company's accounts, as the directors who served during the period.",
      ],
    },
    hmrc: [ACCOUNTS],
  },
  signing_director: {
    topic: "the director who signed the accounts",
    plain: {
      meaning: [
        "One director signs the balance sheet on behalf of the board of directors, once the board has approved the accounts. Their name is printed under the signature.",
      ],
      example: [
        "The board, Priya Shah and Tom Evans, approves the accounts, and Priya signs the balance sheet for the board. Select Priya Shah.",
      ],
      excludes: ["Anyone who is not a director, such as the company secretary or an accountant."],
      effect: [
        "We print their name on the balance sheet in the company's accounts, below the statements the accounts must include, as the director who signed on behalf of the board.",
      ],
    },
    hmrc: [
      ACCOUNTS,
      {
        quote: {
          guide: COMPANIES_HOUSE,
          heading: APPROVING_AND_SIGNING,
          paragraphs: [
            "A director must sign the balance sheet on behalf of the board and print their name. Any exemption statements must appear above the director’s signature.",
          ],
        },
      },
    ],
  },
  approval_date: {
    topic: "the date the accounts were approved",
    plain: {
      meaning: [
        "The date the company's board of directors formally agreed the accounts, at a board meeting or in writing. The accounts can only be approved after the accounting period has ended.",
        "The directors should approve the accounts before you file them with the return.",
      ],
      example: [
        "The accounting period ended on 31 March 2026. The directors met on 15 June 2026 and approved the accounts. Enter 15 June 2026.",
      ],
      excludes: [
        "The date the accounting period ended.",
        "The date you file the return or send the accounts to Companies House.",
      ],
      effect: [
        "We state it on the balance sheet in the company's accounts, as the date the board approved them. It must be after the end of the accounting period.",
      ],
    },
    hmrc: [
      ACCOUNTS,
      {
        quote: {
          guide: COMPANIES_HOUSE,
          heading: APPROVING_AND_SIGNING,
          paragraphs: [
            "The company’s board of directors must approve the accounts before they send them to the company’s members.",
          ],
        },
      },
    ],
  },
  average_employees: {
    topic: "the average number of employees",
    plain: {
      meaning: [
        "The average number of people the company employed during the accounting period, including directors.",
        "To work it out, count the people employed in each month of the period, counting anyone employed for any part of the month. Add the monthly numbers together and divide by the number of months. Enter it as a whole number, rounding if you need to.",
      ],
      example: [
        "For the first 8 months of a 12-month period the company employed its 2 directors. For the last 4 months it also employed 3 staff, so 5 people. That is 2 times 8 plus 5 times 4, which is 36. Divided by 12 months, the average is 3. Enter 3.",
      ],
      excludes: [
        "Freelancers, contractors and agency workers, who are not employed by the company.",
        "Shareholders who do not work for the company.",
      ],
      effect: [
        "We show it in a note to the company's accounts. It also counts towards the limits for micro-entity and small company accounts.",
      ],
    },
    hmrc: [
      ACCOUNTS,
      {
        quote: {
          guide: COMPANIES_HOUSE,
          heading: "8. Company size thresholds",
          paragraphs: [
            "To determine whether your company is a micro-entity, small or medium-sized, there are thresholds for:",
            "the average number of employees",
          ],
        },
      },
    ],
  },
  trading_status: {
    topic: "whether the company traded",
    plain: {
      meaning: [
        "Whether the company carried on its business during the accounting period, has never started doing business, or did business in the past but has stopped.",
        "Trading includes buying and selling, providing services, renting out property, advertising and employing people.",
      ],
      example: [
        "A company that sold its services to clients during the period traded.",
        "A company set up in May 2025 that has not yet started its business has never traded.",
        "A company that closed its shop in 2024 and now only holds money in the bank has stopped trading.",
      ],
      excludes: [
        "A dormant company cannot have traded. If the company traded, it was not dormant.",
      ],
      effect: [
        "We state it in the company's accounts. If the company has never traded and has no trading figures, we leave the trading calculation out of the tax computations.",
      ],
    },
    hmrc: [
      ACCOUNTS,
      {
        quote: {
          guide: "dormant-company",
          heading: "Dormant for Corporation Tax",
          paragraphs: [
            "Your company is usually dormant for Corporation Tax if it:",
            "has stopped trading and has no other income, for example investments",
            "is a new limited company that has not started trading",
            "Trading includes buying, selling, renting property, advertising, employing someone or getting interest. HMRC has detailed guidance on what counts as dormant for Corporation Tax.",
          ],
        },
      },
    ],
  },
  dormant: {
    topic: "dormant companies",
    plain: {
      meaning: [
        "A company is dormant if it had no significant accounting transactions for the whole accounting period. That means nothing that would normally go in its accounting records: no sales, costs, income or gains.",
        "You can ignore money paid for shares when the company was set up, fees paid to Companies House and penalties for filing accounts late.",
      ],
      example: [
        "A company was set up on 1 April 2025 to protect a brand name. In its first year the only money that moved was the £100 its shareholders paid for their shares when it was set up, and the fee for its confirmation statement. It was dormant.",
        "A company whose only income was £5 of bank interest was not dormant.",
      ],
      excludes: [
        "A company that stopped trading part-way through the period. It must be dormant for the whole period.",
        "Being dormant for Corporation Tax, which is different. If you have told HMRC the company is dormant, it may not need to file a return at all, unless it gets a notice to deliver one.",
      ],
      effect: [
        "We prepare dormant accounts. They leave out the profit and loss account and say the company is exempt from audit as a dormant company.",
        "Every amount in the profit and loss account and any chargeable gains must be 0, the company cannot have traded, and it has no Corporation Tax to pay.",
      ],
    },
    hmrc: [
      ACCOUNTS,
      {
        quote: {
          guide: COMPANIES_HOUSE,
          heading: "13. Dormant company accounts",
          paragraphs: [
            "A company is dormant if it has had no ‘significant accounting transactions’ during the accounting period. A significant accounting transaction is one which the company should enter in its accounting records.",
            "When determining if a company is dormant, you can disregard:",
            "payment for shares taken by subscribers to the memorandum of association",
            "fees paid to Companies House for a change of company name, the re-registration of a company and filing confirmation statements (or annual returns)",
            "payment of a civil penalty for late filing of accounts",
          ],
        },
      },
      {
        quote: {
          guide: "dormant-company",
          heading: "Limited companies",
          paragraphs: [
            "You do not need to pay Corporation Tax or file another Company Tax Return once you’ve told HMRC your company is dormant, unless you receive a further notice to deliver a Company Tax Return.",
          ],
        },
      },
    ],
  },
  legal_form: {
    topic: "the company's legal form",
    plain: {
      meaning: [
        "This is the kind of company it was set up as. Most small businesses are private companies limited by shares: the owners hold shares, and can only lose what they paid for them.",
        "A company limited by guarantee has members instead of shareholders, who each promise to pay a small fixed amount if it closes owing money. Clubs and charities are often set up this way. A community interest company is a limited company run for the benefit of a community.",
        "It is on the certificate of incorporation, and on the company's page on the Companies House register.",
      ],
      example: [
        "Alex set up a consultancy as Alex Smith Consulting Ltd and holds its 100 £1 shares. It is a private company limited by shares.",
      ],
      excludes: [
        "Public limited companies (plc) and limited liability partnerships (LLPs). This service cannot prepare their accounts.",
        "Sole traders and partnerships, which are not companies and do not file a Company Tax Return.",
      ],
      effect: [
        "We record the legal form in the accounts. For a company limited by guarantee, the balance sheet shows members' funds instead of shareholders' funds.",
      ],
    },
    hmrc: [
      ACCOUNTS,
      {
        quote: {
          guide: COMPANIES_HOUSE,
          heading: "4.1 Private and public limited companies",
          paragraphs: [
            "All private and public limited companies must file their accounts at Companies House. Dormant subsidiaries may be able to apply for an exemption.",
          ],
        },
      },
    ],
  },
  first_period: {
    topic: "the first period of account",
    plain: {
      meaning: [
        "A company's first period of account starts on the day it was set up. After that, each period starts the day after the last one ended.",
        "From the second period on, the accounts show last period's figures beside this period's so they can be compared. These are called comparatives.",
      ],
      example: [
        "A company was set up on 10 May 2024 and made its first accounts up to 31 May 2025. For that period, answer yes. For the period from 1 June 2025 to 31 May 2026, answer no, and enter the first period's figures as the previous period.",
      ],
      excludes: [
        "The company's first Corporation Tax accounting period, if that is shorter than its first period of account. Answer about the accounts.",
      ],
      effect: [
        "If you answer no, we ask for the previous period's figures with the profit and loss account, balance sheet and number of employees, and show them in the accounts.",
      ],
    },
    hmrc: [
      ACCOUNTS,
      {
        quote: {
          guide: COMPANIES_HOUSE,
          heading: "1.1 A company’s financial year",
          paragraphs: [
            "For an existing company, your financial year starts on the day after the previous financial year ended.",
            "For a new company, your financial year starts on the day of incorporation.",
          ],
        },
      },
    ],
  },
};

/** Help for the previous period's figures (comparatives) asked after a first period. */
export const COMPARATIVES_HELP: Record<
  "previous_period" | "tax_on_profit" | "previous_employees",
  QuestionHelp
> = {
  previous_period: {
    topic: "the previous period of account",
    plain: {
      meaning: [
        "The accounts show last period's figures beside this period's. Enter the dates of the period the company's last accounts covered.",
        "They are on the last accounts, and on the company's filing history at Companies House.",
      ],
      example: [
        "The company's last accounts were for 1 April 2024 to 31 March 2025. Enter 1 4 2024 and 31 3 2025.",
      ],
      excludes: ["This period's dates, which you entered as the accounting period."],
      effect: [
        "We label the previous period column in the accounts with these dates. They must end the day before this period starts.",
      ],
    },
    hmrc: [
      ACCOUNTS,
      {
        quote: {
          guide: COMPANIES_HOUSE,
          heading: "1.1 A company’s financial year",
          paragraphs: [
            "For an existing company, your financial year starts on the day after the previous financial year ended.",
          ],
        },
      },
    ],
  },
  tax_on_profit: {
    topic: "last period's tax on profit",
    plain: {
      meaning: [
        "The Corporation Tax charge shown in last period's profit and loss account, just above the profit for the period.",
        "We work out this period's tax ourselves, so you only need last period's for the comparison.",
      ],
      example: [
        "Last period's accounts show a profit before tax of £40,000, tax on profit of £7,600 and profit for the period of £32,400. Enter 7600.",
        "If the accounts show a tax credit of £1,200, enter -1200.",
      ],
      excludes: ["This period's tax, which we work out.", "VAT, PAYE or National Insurance."],
      effect: [
        "We show it in the previous period column of the profit and loss account, so last period's profit for the period matches the accounts filed then.",
      ],
    },
    hmrc: [ACCOUNTS],
  },
  previous_employees: {
    topic: "last period's number of employees",
    plain: {
      meaning: [
        "The average number of people employed in the previous period, including directors, as shown in last period's accounts.",
      ],
      example: ["Last period's accounts say the company had an average of 3 employees. Enter 3."],
      excludes: ["This period's average, which you enter above."],
      effect: [
        "We show it beside this period's number in the notes to the accounts. You can leave it blank.",
      ],
    },
    hmrc: [ACCOUNTS],
  },
};
