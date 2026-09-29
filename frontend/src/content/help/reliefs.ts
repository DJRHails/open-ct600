/**
 * Help for the reliefs questions that have no box of their own on the supplementary pages, and
 * for choosing the pages, written from HMRC's guidance:
 *
 * Research and development: https://www.gov.uk/guidance/corporation-tax-research-and-development-rd-relief,
 * https://www.gov.uk/guidance/check-what-research-and-development-rd-costs-you-can-claim,
 * https://www.gov.uk/guidance/work-out-your-research-and-development-tax-relief,
 * https://www.gov.uk/guidance/research-and-development-rd-tax-relief-the-merged-scheme-and-enhanced-rd-intensive-support,
 * https://www.gov.uk/guidance/corporation-tax-research-and-development-tax-relief-for-small-and-medium-sized-enterprises
 * (for SME scheme costs before 1 April 2023 the rates were a 130% extra deduction and a 14.5%
 * credit, as the backend's ``reliefs/research_and_development.py`` applies),
 * https://www.gov.uk/guidance/tell-hmrc-that-youre-planning-to-claim-research-and-development-rd-tax-relief,
 * https://www.gov.uk/guidance/submit-detailed-information-before-you-claim-research-and-development-rd-tax-relief,
 * https://www.gov.uk/guidance/make-a-claim-for-rd-tax-relief-on-your-company-tax-return and
 * https://www.gov.uk/guidance/supplementary-pages-ct600l-research-and-development.
 *
 * Creative industries: https://www.gov.uk/guidance/support-your-claim-for-creative-industry-tax-reliefs
 * and https://www.gov.uk/guidance/completing-the-ct600p-page-for-creative-industries-reliefs.
 *
 * Loans to participators: https://www.gov.uk/guidance/supplementary-pages-ct600a-2015-version-3-close-company-loans-and-arrangements-to-confer-benefits-on-participators,
 * https://www.gov.uk/directors-loans and
 * https://www.gov.uk/guidance/changes-and-issues-affecting-the-corporation-tax-online-service
 * (the 35.75% rate).
 *
 * Group and consortium relief: https://www.gov.uk/guidance/supplementary-pages-ct600c-group-and-consortium-relief
 * and the Company Taxation Manual (CTM80105 and CTM80255 for surrenderable amounts and
 * overlapping periods, CTM80151 for groups, CTM80530 for consortia).
 *
 * Supplementary pages: https://www.gov.uk/guidance/the-company-tax-return-guide.
 */
import type { HmrcRef, QuestionHelp } from "@/content/help/types";
import type { ResearchAnswers, SurrendererFigures } from "@/filing/reliefs";

const MERGED_SCHEME =
  "research-and-development-rd-tax-relief-the-merged-scheme-and-enhanced-rd-intensive-support";
const CLAIM_NOTIFICATION =
  "tell-hmrc-that-youre-planning-to-claim-research-and-development-rd-tax-relief";
const SME_SCHEME =
  "corporation-tax-research-and-development-tax-relief-for-small-and-medium-sized-enterprises";

const NOTIFICATION_PERIOD: HmrcRef = {
  quote: {
    guide: CLAIM_NOTIFICATION,
    heading: "Working out your claim notification period",
    paragraphs: [
      "Your claim notification period:",
      "starts on the first day of the ‘period of account’ — this is the first date of your notification period",
      "ends 6 months after the end of the ‘period of account’ — this is the last date of your claim notification period",
    ],
  },
};

export const RESEARCH_HELP: Record<keyof ResearchAnswers, QuestionHelp> = {
  claiming: {
    topic: "research and development (R&D) relief",
    plain: {
      meaning: [
        "R&D relief reduces tax, or pays a credit, for companies that spend money on projects seeking an advance in science or technology.",
        "The project must try to resolve a scientific or technological uncertainty: something a competent professional in the field could not easily work out. The advance must be for the field as a whole, not just for your company.",
      ],
      example: [
        "A software company spent £55,000 developing a new way to compress video that experts did not know how to achieve. It can claim R&D relief on the qualifying costs of that project.",
      ],
      excludes: [
        "Projects in the arts, humanities or social sciences, including economics.",
        "Routine work, like building a website with existing tools or making minor upgrades to a product.",
      ],
      effect: [
        "If yes, we ask about the claim and work out the relief. You must have sent HMRC the additional information form, and a claim notification form if one is needed.",
        "For expenditure credit or a payable tax credit, you also choose supplementary page CT600L.",
      ],
    },
    hmrc: [
      {
        quote: {
          guide: "corporation-tax-research-and-development-rd-relief",
          heading: "What R&D tax relief is",
          paragraphs: [
            "Research and Development (R&D) tax relief supports companies that work on innovative projects in science and technology. To qualify for R&D relief, a project must seek an advance in a field of science or technology.",
          ],
        },
      },
      {
        quote: {
          guide: "corporation-tax-research-and-development-rd-relief",
          heading: "A scientific or technological uncertainty",
          paragraphs: [
            "A scientific or technological uncertainty exists when an expert on the subject cannot say if something is technologically possible, or how it can be done, even after referring to all the available evidence.",
          ],
        },
      },
    ],
  },
  scheme: {
    topic: "R&D relief schemes",
    plain: {
      meaning: [
        "The scheme depends on when the accounting period started.",
        "For periods starting on or after 1 April 2024, most companies claim under the merged scheme: a research and development expenditure credit (RDEC) of 20% of the qualifying costs. Loss-making small and medium-sized enterprises (SMEs) that spend at least 30% of their total costs on R&D can claim enhanced R&D intensive support (ERIS) instead.",
        "For periods starting before 1 April 2024, SMEs claim under the SME scheme and large companies claim RDEC.",
      ],
      example: [
        "A company's period runs from 1 January 2025 to 31 December 2025. It spent £100,000 on qualifying R&D. Under the merged scheme it gets an expenditure credit of £20,000.",
        "If it is a loss-making SME that meets the 30% condition, it can claim ERIS instead: it takes an extra £86,000 off its profits, and it can give up its loss for a payable tax credit.",
      ],
      excludes: [
        "Claiming under both the merged scheme and ERIS for the same costs. This service does not handle claims under both schemes in the same period.",
        "The SME scheme for periods starting on or after 1 April 2024, and ERIS for periods starting before then.",
      ],
      effect: [
        "For RDEC, we add the credit to the company's trading profits, because it is taxable, and follow the steps on CT600L to use it against the company's tax. Any credit left over is paid to the company or carried forward.",
        "For the SME scheme and ERIS, we take the extra deduction off the company's trading profits and show the costs in boxes 659 and 660.",
      ],
    },
    hmrc: [
      {
        quote: {
          guide: MERGED_SCHEME,
          heading:
            "The merged R&D expenditure credit scheme and enhanced R&D intensive support scheme",
          paragraphs: [
            "The merged scheme R&D expenditure credit (RDEC) and enhanced R&D intensive support (ERIS) replace the old RDEC and small and medium-sized enterprise (SME) schemes for accounting periods beginning on or after 1 April 2024. The qualifying expenditure rules for the two new schemes are identical but the calculation of the credit amount is different.",
            "Even if you are eligible for ERIS you can choose to claim under the merged RDEC scheme, but you cannot claim under both schemes for the same expenditure.",
          ],
        },
      },
      { box: "650" },
      { box: "655" },
      { box: "659" },
      { box: "660" },
    ],
  },
  company_is_sme: {
    topic: "small and medium-sized enterprises (SMEs) for R&D relief",
    plain: {
      meaning: [
        "For R&D relief, a company is an SME if it has fewer than 500 staff, and either turnover under 100 million euros or a balance sheet total under 86 million euros.",
        "Include the staff, turnover and balance sheet of any linked companies, such as a parent company or subsidiaries, and a share of those of partner companies, where one owns 25% or more of the other.",
      ],
      example: [
        "A company has 12 staff and turnover of £800,000, and is owned by its 2 directors. It is an SME.",
        "A company with 40 staff whose parent company owns all its shares and has a group of 2,000 staff is not an SME.",
      ],
      excludes: [
        "The size limits for micro-entity and small company accounts, which are different.",
      ],
      effect: [
        "It does not change the credit. We tick box 650 on the return for an SME and box 655 for a large company.",
      ],
    },
    hmrc: [
      { box: "650" },
      { box: "655" },
      {
        quote: {
          guide: SME_SCHEME,
          heading: "Who can claim",
          paragraphs: [
            "less than 500 staff",
            "a turnover of under 100 million euros or a balance sheet total under 86 million euros",
            "You must include the staff, turnover and balance sheets of any linked or partner companies in your total when you work out if you can claim R&D tax relief for SMEs.",
          ],
        },
      },
    ],
  },
  qualifying_expenditure: {
    topic: "qualifying R&D expenditure",
    plain: {
      meaning: [
        "The costs of the R&D project that the company can claim for. These include staff costs for the time spent on the project, agency staff, contractors, consumables such as materials and power, software, data licences, cloud computing, and payments to clinical trial volunteers.",
        "Only include the share of each cost spent on the R&D. For periods starting on or after 1 April 2024, only 65% of payments to contractors the company is not connected with counts.",
      ],
      example: [
        "A developer's salary, employer's National Insurance and pension contributions total £60,000, and they spent 75% of their time on the project: £45,000.",
        "The company also paid £4,000 for cloud computing used for the R&D and £10,000 to an unconnected contractor, of which 65% counts: £6,500. Enter £55,500.",
      ],
      excludes: [
        "Capital expenditure, land, patents and trademarks, and rent, rates or leasing costs.",
        "The costs of producing and distributing the company's goods and services.",
        "Costs the company has not paid by the time it makes the claim.",
        "For periods starting on or after 1 April 2024, most payments to contractors for R&D done outside the UK.",
      ],
      effect: [
        "For the SME scheme and ERIS, we show it in box 659 and take an extra 86% of it off the company's trading profits. The total of 186% is shown in box 660. For SME scheme costs before 1 April 2023, the extra deduction is 130%, so the total is 230%.",
        "For RDEC, we show it in box L10 of CT600L and work out the credit on it.",
      ],
    },
    hmrc: [
      { box: "659" },
      { box: "660" },
      { box: "L10" },
      {
        quote: {
          guide: "check-what-research-and-development-rd-costs-you-can-claim",
          heading: "Costs you cannot claim",
          paragraphs: [
            "You can only claim the costs listed on this page, you cannot claim for any other costs.",
            "For example, you cannot claim for:",
            "capital expenditure",
            "the cost of land",
            "the cost of patents and trademarks",
            "rent, rates or leasing costs",
          ],
        },
      },
    ],
  },
  rdec_expenditure: {
    topic: "expenditure an SME claims RDEC on",
    plain: {
      meaning: [
        "Under the SME scheme, for periods starting before 1 April 2024, some R&D costs cannot get SME relief. The company claims the research and development expenditure credit (RDEC) on them instead.",
        "This includes R&D a large company paid your company to do, and projects that received a notified state aid or were otherwise subsidised.",
      ],
      example: [
        "Your company did R&D worth £30,000 under a contract with a large company, in a period starting on 1 April 2023. Enter £30,000 here, and the RDEC of 20%, £6,000, in box L185 of CT600L.",
      ],
      excludes: ["Costs you claim SME relief on. Enter those as qualifying R&D expenditure."],
      effect: [
        "We show it in box L10 of CT600L and check it against the credit you enter in boxes L185 and L190. The credit is added to the company's taxable trading profits.",
      ],
    },
    hmrc: [{ box: "L10" }, { box: "L185" }, { box: "L190" }],
  },
  intensity: {
    topic: "R&D intensity",
    plain: {
      meaning: [
        "The company's relevant R&D expenditure as a percentage of its total relevant expenditure. Include the costs of any connected companies.",
        "Relevant R&D expenditure is the costs the company could claim R&D relief on, whether or not it does. Total relevant expenditure is broadly the costs in its profit and loss account, before tax.",
      ],
      example: [
        "A company's costs in its profit and loss account are £500,000, and £175,000 of them could get R&D relief. Its R&D intensity is £175,000 divided by £500,000, which is 35%. Enter 35.",
      ],
      excludes: [
        "Payments to connected companies, which are left out of total relevant expenditure.",
        "Amortisation that is added back in the tax computations.",
      ],
      effect: [
        "ERIS usually needs an intensity of at least 30% for the period. We only accept an ERIS claim with an intensity of 30% or more. Otherwise, claim under the merged scheme.",
        "Under the SME scheme, an intensity of at least 40% makes the company R&D intensive for periods ending on or after 1 April 2023. We then tick box 653, and its payable tax credit is 14.5% of the loss it gives up instead of 10%.",
      ],
    },
    hmrc: [
      { box: "653" },
      {
        quote: {
          guide: MERGED_SCHEME,
          heading: "Intensity condition",
          paragraphs: [
            "A company meets the intensity condition if its:",
            "claiming for an accounting period beginning on or after 1 April 2024",
            "relevant R&D expenditure is at least 30% of its total expenditure (including that of any connected companies — read the Corporate Intangibles Research and Development Manual for information)",
          ],
        },
      },
    ],
  },
  claim_payable_credit: {
    topic: "payable R&D tax credits",
    plain: {
      meaning: [
        "Under ERIS or the SME scheme, a company with a trading loss can give up some or all of the loss in return for a payment from HMRC, called a payable tax credit.",
        "It can give up the lower of its trading loss after the extra R&D deduction and its enhanced expenditure (186% of its qualifying costs, or 230% for SME scheme costs before 1 April 2023). The credit is 14.5% of the loss given up under ERIS. Under the SME scheme it is 10% for costs from 1 April 2023, or 14.5% for R&D intensive companies, and 14.5% for costs before 1 April 2023.",
        "The credit is capped at £20,000 plus 3 times the company's PAYE and National Insurance for the period, unless an exception applies.",
      ],
      example: [
        "A company claiming ERIS has qualifying costs of £100,000 and, before the extra deduction, a trading loss of £40,000. The extra 86% deduction of £86,000 makes the loss £126,000. That is less than its enhanced expenditure of £186,000, so it gives up £126,000 for a credit of 14.5%, which is £18,270.",
      ],
      excludes: [
        "RDEC claims. RDEC is paid through the steps on CT600L, not by giving up a loss.",
        "Companies without a trading loss.",
      ],
      effect: [
        "We work out the credit, fill in CT600L and show the amount payable in box 875. You also need to choose supplementary page CT600L.",
        "The loss given up can no longer be carried forward to later periods.",
      ],
    },
    hmrc: [{ box: "L170" }, { box: "875" }],
  },
  rd_workers_paye_and_nic: {
    topic: "PAYE and National Insurance on R&D workers",
    plain: {
      meaning: [
        "For large company RDEC claims for periods starting before 1 April 2024, the credit that can be paid out or used against other periods' tax is capped. The cap is the PAYE and National Insurance the company owed on the pay of the staff whose costs are in the claim.",
      ],
      example: [
        "After steps 1 and 2 on CT600L, the company has £12,000 of credit left. The PAYE and National Insurance on its R&D staff's pay for the period is £9,000. Enter £9,000. Only £9,000 goes on to the next steps, and £3,000 is carried forward.",
      ],
      excludes: [
        "PAYE and National Insurance for staff who did not work on the R&D.",
        "Claims under the merged scheme, which use a different PAYE cap that you enter on CT600L.",
      ],
      effect: [
        "We show it in box L75 of CT600L. We only need it if some credit is left after steps 1 and 2. If there is and you leave this blank, we ask you for it.",
      ],
    },
    hmrc: [{ box: "L75" }],
  },
  claimed_in_previous_three_years: {
    topic: "earlier R&D claims",
    plain: {
      meaning: [
        "Whether the company has made an R&D claim in the 3 years before the last date of this claim's notification period. The notification period ends 6 months after the end of the period covered by the company's accounts.",
        "It counts from when the earlier claim was made, on a return or an amended return, not from the period it was for. A claim HMRC removed from a return does not count.",
      ],
      example: [
        "The company's accounts cover 1 January 2025 to 31 December 2025, so the notification period ends on 30 June 2026. It claimed R&D relief on the return it filed on 15 September 2025. Answer yes.",
        "If its last claim was made before 30 June 2023, answer no.",
      ],
      excludes: [
        "Claims HMRC removed from the company's return.",
        "Claims for periods starting before 1 April 2023 made by amending a return, if HMRC received the amendment on or after 1 April 2023.",
      ],
      effect: [
        "If yes, the company does not need a claim notification form. If no, we ask whether it sent one, as HMRC will not accept the claim without it.",
      ],
    },
    hmrc: [
      {
        quote: {
          guide: CLAIM_NOTIFICATION,
          heading: "If you’ve claimed R&D tax relief previously",
          paragraphs: [
            "If you’ve claimed R&D tax relief within 3 years of the last date of your claim notification period you do not need to send a claim notification form, unless any of the following exceptions apply:",
            "HMRC rejected your R&D tax relief claim by removing it from your Company Tax Return",
            "you claimed R&D tax relief for an accounting period beginning before 1 April 2023 by amending your tax return and the amendment was received on or after 1 April 2023",
          ],
        },
      },
      NOTIFICATION_PERIOD,
    ],
  },
  claim_notification_submitted: {
    topic: "R&D claim notification",
    plain: {
      meaning: [
        "A claim notification form tells HMRC in advance that the company plans to claim R&D relief. It is needed for periods starting on or after 1 April 2023 if the company has not claimed in the last 3 years.",
        "It must reach HMRC between the first day of the period covered by the company's accounts and 6 months after that period ends.",
      ],
      example: [
        "The company's accounts cover 1 April 2025 to 31 March 2026. It must send the claim notification form between 1 April 2025 and 30 September 2026.",
      ],
      excludes: ["The R&D additional information form, which every claim needs as well."],
      effect: [
        "If yes, we tick box 656 on the return. If the company did not send the form in time, its claim is invalid, and this service cannot file it.",
      ],
    },
    hmrc: [
      { box: "656" },
      {
        quote: {
          guide: CLAIM_NOTIFICATION,
          heading: "When to submit the form — claim notification period",
          paragraphs: [
            "You must submit the form within certain dates known as the ‘claim notification period’. If you do not, your R&D tax relief claim will be invalid.",
          ],
        },
      },
      NOTIFICATION_PERIOD,
    ],
  },
  additional_information_submitted: {
    topic: "the R&D additional information form",
    plain: {
      meaning: [
        "Every R&D claim needs an additional information form. It gives HMRC details of the company, its R&D projects and the costs it is claiming for.",
        "The company must send it online before the return, or on the same day. On the same day, send the form first.",
      ],
      example: [
        "You plan to file the return on 10 December 2026. Send the additional information form on or before 10 December 2026, and if on the same day, before you file the return.",
      ],
      excludes: [
        "The claim notification form, which is a separate form sent earlier.",
        "The creative industries additional information form.",
      ],
      effect: [
        "If yes, we tick box 657 on the return. If the form is not sent first, HMRC removes the claim, so you cannot continue with it until you have sent the form.",
      ],
    },
    hmrc: [
      { box: "657" },
      {
        quote: {
          guide:
            "submit-detailed-information-before-you-claim-research-and-development-rd-tax-relief",
          heading: "When to submit",
          paragraphs: [
            "The additional information form must be submitted before or on the same day you submit the Company Tax Return (CT600). If you do not submit this form, any R&D or expenditure credit claim will not be accepted.",
            "If you send the additional information form and the Company Tax Return (CT600) on the same day, you must make sure you send the form first, followed by the tax return. If the tax return is submitted before the additional information form, the claim will be rejected.",
          ],
        },
      },
    ],
  },
};

export const CREATIVE_HELP: Record<"additional_information_submitted", QuestionHelp> = {
  additional_information_submitted: {
    topic: "the creative industries additional information form",
    plain: {
      meaning: [
        "Every claim to a creative industries relief or expenditure credit needs an additional information form. These include Theatre Tax Relief, Video Games Tax Relief and the Audio-Visual Expenditure Credit.",
        "The form gives HMRC details of each production and its costs. The company must send it before the return, or on the same day, and the dates of the accounting period on it must match the return.",
      ],
      example: [
        "The company produced a touring play and is claiming Theatre Tax Relief for 1 January 2025 to 31 December 2025. Before it files the return, it sends the form with the play's name, the date production began, the first performance and the production's core costs.",
      ],
      excludes: ["The R&D additional information form, which is a different form."],
      effect: [
        "If yes, we tick box 658 on the return. HMRC does not accept claims without the form, so you cannot continue with the claim until you have sent it.",
      ],
    },
    hmrc: [
      { box: "658" },
      {
        quote: {
          guide: "support-your-claim-for-creative-industry-tax-reliefs",
          heading: "When you should submit your claim",
          paragraphs: [
            "You must submit this form and all supporting evidence either before or on the same day you submit your Company Tax Return.",
          ],
        },
      },
      {
        quote: {
          guide: "support-your-claim-for-creative-industry-tax-reliefs",
          heading: "Accounting period start and end date",
          paragraphs: [
            "If the start and end dates on both submissions do not match, the additional information form will be rejected and the creative industry tax relief claim in the Company Tax Return will be removed.",
          ],
        },
      },
    ],
  },
};

export const LOAN_DATE_HELP: QuestionHelp = {
  topic: "when a loan to a participator was made",
  plain: {
    meaning: [
      "A close company is one controlled by 5 or fewer people, or by its directors. When it lends money to a participator, usually a shareholder, and the loan is not repaid within 9 months of the end of the period, the company pays tax on it.",
      "The rate depends on when the loan was made. It is 33.75% for loans made from 6 April 2022 to 5 April 2026, and 35.75% for loans made on or after 6 April 2026. The rate changed during this accounting period, so we need the date of each loan.",
    ],
    example: [
      "The company's period is 1 January 2026 to 31 December 2026. It lent a director £10,000 on 1 March 2026 and £10,000 on 1 June 2026. The tax is £3,375 on the first loan and £3,575 on the second.",
    ],
    excludes: [
      "The date the loan was repaid, released or written off.",
      "Loans made before or after this accounting period.",
    ],
    effect: [
      "We charge tax on each loan at the rate for the date it was made, and give any relief for repayments at the same rate.",
      "HMRC's systems will only accept the 35.75% rate from 6 April 2027. Until then we file the return at 33.75%, and you will need to amend it after 6 April 2027 for loans made on or after 6 April 2026.",
    ],
  },
  hmrc: [
    { box: "A10" },
    { box: "A20" },
    {
      quote: {
        guide: "changes-and-issues-affecting-the-corporation-tax-online-service",
        heading: "Loans to participators",
        paragraphs: [
          "At Budget 2025, the rate of tax payable under the loans to participators regime was increased from 33.75% to 35.75%. The new rate will apply to loans made or benefits conferred on or after 6 April 2026.",
          "The Corporation Tax online service will be updated to reflect this change on 6 April 2027.",
          "If the new rate applies to your company and you need to file before 6 April 2027, you’ll need to amend your return after 6 April 2027 to reflect the new rate.",
        ],
      },
    },
  ],
};

export const SURRENDERER_HELP: Record<keyof SurrendererFigures, QuestionHelp> = {
  surrenderable_amount: {
    topic: "the amount a company can surrender",
    plain: {
      meaning: [
        "The most the surrendering company can give up as group relief for its own accounting period. Its own Company Tax Return shows this as the maximum available for surrender, such as trading losses in box 785.",
      ],
      example: [
        "Your company's period is 1 January 2025 to 31 December 2025. A company in your group made a trading loss of £120,000 in its year to 30 June 2025, shown in box 785 of its return. Enter £120,000.",
        "The 2 periods overlap for 6 months, so your company can claim at most the part of the loss for those months, about £60,000.",
      ],
      excludes: ["The amount your company is claiming, which you enter on CT600C."],
      effect: [
        "This is optional. If you enter it, we check your claim is no more than the share of this amount for the time the 2 periods overlap, less what the company has already surrendered to others for that time.",
      ],
    },
    hmrc: [{ box: "C5" }, { box: "785" }],
  },
  surrendered_to_others: {
    topic: "amounts already surrendered to other companies",
    plain: {
      meaning: [
        "How much the surrendering company has already given up as group or consortium relief to other companies, for the part of its period that overlaps your company's accounting period.",
      ],
      example: [
        "£60,000 of the surrendering company's loss is for the 6 months that overlap your company's period. It has already surrendered £25,000 for those months to another company in the group. Enter £25,000. Your company can claim up to £35,000.",
      ],
      excludes: [
        "Amounts surrendered for months that do not overlap your company's period.",
        "The amount it is surrendering to your company.",
      ],
      effect: [
        "This is optional. We take it off the amount available for the overlapping period when we check your claim.",
      ],
    },
    hmrc: [{ box: "C5" }, { box: "C85" }],
  },
  consortium_share: {
    topic: "a consortium member's share",
    plain: {
      meaning: [
        "A consortium is a group of companies that together own at least 75% of the shares of another company, each owning at least 5%. Consortium relief lets losses pass between the company they own and its members.",
        "The share is the lowest of your company's percentages of the surrendering company's shares, profits, assets and votes.",
      ],
      example: [
        "Your company owns 30% of a joint venture company's shares, is entitled to 30% of its profits and assets, and has 25% of its votes. Enter 25. If the joint venture's loss is £80,000, your company can claim at most £20,000 of it.",
      ],
      excludes: [
        "Claims between companies in the same group, where one owns at least 75% of the other or a third company owns at least 75% of both. Leave this blank for those.",
      ],
      effect: [
        "This is optional. If you enter it, we limit the claim to this percentage of the amount the surrendering company can surrender.",
      ],
    },
    hmrc: [
      { box: "C5" },
      {
        quote: {
          guide: "supplementary-pages-ct600c-group-and-consortium-relief",
          heading: "Part 1: claims to group relief",
          paragraphs: [
            "Unless a simplified arrangement is in force, you must also attach a copy of each surrendering company’s notice of consent to the claim. Include claims made under the consortium provisions and attach a copy of the notice of consent of each member of the consortium.",
          ],
        },
      },
    ],
  },
};

export const CHOOSE_PAGES_HELP: QuestionHelp = {
  topic: "supplementary pages",
  plain: {
    meaning: [
      "Supplementary pages are extra pages of the Company Tax Return for particular claims and situations, named CT600A to CT600P. Most small companies do not need any.",
    ],
    example: [
      "A director borrowed £8,000 from the company and had not paid it back by the end of the period. Choose CT600A.",
      "The company is claiming the research and development expenditure credit. Choose CT600L.",
    ],
    excludes: [
      "Pages for situations that do not apply to the company in this period.",
      "CT600G for Northern Ireland, which is not in use yet.",
    ],
    effect: [
      "We ask you the questions on each page you choose, and tell HMRC which pages are included in the return.",
      "The pages are part of the return and are covered by the declaration you make when you file it.",
    ],
  },
  hmrc: [
    {
      quote: {
        guide: "the-company-tax-return-guide",
        heading: "Supplementary pages",
        paragraphs: [
          "Enter X in the appropriate box or boxes to show which supplementary pages you’re including in your Company Tax Return.",
          "Supplementary pages provide a standard format to help you submit the information HMRC needs. It’s important to get this right because your completed supplementary pages form part of your company’s return and are covered by the declaration.",
        ],
      },
    },
  ],
};
