/**
 * Help for the boxes the company is asked on the supplementary pages CT600A (loans to
 * participators), CT600C (group and consortium relief) and CT600L (research and development),
 * written from HMRC's guidance:
 *
 * CT600A: https://www.gov.uk/guidance/supplementary-pages-ct600a-2015-version-3-close-company-loans-and-arrangements-to-confer-benefits-on-participators,
 * https://www.gov.uk/directors-loans,
 * https://www.gov.uk/guidance/changes-and-issues-affecting-the-corporation-tax-online-service
 * (the 35.75% rate) and the Company Taxation Manual (CTM61505 for the rates, CTM61540 for
 * loans to employees, CTM61610 for when relief is due, CTM61630 for the 30-day rule).
 *
 * CT600C: https://www.gov.uk/guidance/supplementary-pages-ct600c-group-and-consortium-relief
 * and the Company Taxation Manual (CTM80105, CTM80110, CTM80120, CTM80140, CTM80142 for what
 * can be surrendered; CTM80151 and CTM80530 for groups and consortia; CTM80310 for UK
 * permanent establishments; CTM97020, CTM97040 and CTM97660 for consent and simplified
 * arrangements; CTM82010 to CTM82030 and CTM82180 for carried-forward losses).
 *
 * CT600L: https://www.gov.uk/guidance/supplementary-pages-ct600l-research-and-development,
 * https://www.gov.uk/guidance/research-and-development-rd-tax-relief-the-merged-scheme-and-enhanced-rd-intensive-support
 * and the Corporate Intangibles Research and Development Manual (CIRD112100 and CIRD89780 for
 * the payment steps, CIRD140000 and CIRD90600 for the PAYE cap and its exceptions, CIRD89810
 * for surrenders, CIRD81130 and CIRD191000 for going concern, CIRD89740 and CIRD89750 for
 * RDEC claimed by SMEs).
 */
import type { PlainHelp } from "@/content/help/types";

const PERMANENT_ESTABLISHMENT: PlainHelp = {
  meaning: [
    "Tick this if any of the losses claimed come from a trade that a company based outside the UK carries on in the UK through a permanent establishment. A permanent establishment is a fixed place of business, such as a branch or office.",
  ],
  example: [
    "A parent company in the United States runs a UK branch that made a £40,000 trading loss. The branch surrenders the loss to your company, a UK subsidiary of the same parent. Tick this box.",
  ],
  excludes: [
    "Losses of companies resident in the UK, even if they are owned from abroad.",
    "Losses of a company outside the UK that do not come from a UK branch or office.",
  ],
  effect: [
    "It tells HMRC that extra rules apply. A UK branch can only surrender a loss if no part of it can be used against profits for tax in another country.",
  ],
};

const AUTHORISED_COMPANY: PlainHelp = {
  meaning: [
    "The name of the company in the group that HMRC has agreed can make group relief claims and surrenders for the other companies. This is the authorised company in the simplified arrangement.",
  ],
  example: [
    "The group's parent company, Oak Holdings Limited, is the authorised company. Enter Oak Holdings Limited.",
  ],
  excludes: ["The name of this company, unless it is itself the authorised company."],
  effect: [
    "It shows HMRC which company approved the claim, so no notices of consent need to be attached.",
  ],
};

const AUTHORISED_PERSON: PlainHelp = {
  meaning: [
    "The full name of the person at the authorised company who approved this company's claim.",
  ],
  example: [
    "The authorised company's finance director, Priya Shah, approved the claim. Enter Priya Shah.",
  ],
  excludes: ["Someone at this company who has not been authorised by the authorised company."],
  effect: ["It records who approved the claim for the group."],
};

const AUTHORISED_STATUS: PlainHelp = {
  meaning: [
    "The job title or role of the person who approved the claim for the authorised company.",
  ],
  example: ["Enter Finance director, Company secretary or Director."],
  excludes: ["The person's name, which goes in the box before."],
  effect: ["It shows HMRC the person had the authority to approve the claim."],
};

const NORTHERN_IRELAND: PlainHelp = {
  meaning: [
    "This box is for losses from trading in Northern Ireland, for use if a separate Corporation Tax rate for Northern Ireland is introduced. There is no separate rate yet.",
  ],
  example: [
    "The company trades from Belfast and surrenders a £20,000 loss. Leave this box blank and include the £20,000 in the total.",
  ],
  excludes: ["Any amount. HMRC asks all companies to leave this box blank."],
  effect: ["Nothing. Leave it blank."],
};

const SIGNATORY_NAME: PlainHelp = {
  meaning: [
    "If this company is using this part of the page as its notice of consent to the surrender, a person authorised to act for the company signs the declaration by entering their full name.",
    "Any person authorised to act for the company can sign, unless a liquidator or administrator has been appointed.",
  ],
  example: ["The company's director, Tom Evans, agrees to the surrender. Enter Tom Evans."],
  excludes: [
    "The name of someone at the claimant company. The surrendering company gives its own consent.",
  ],
  effect: [
    "With the declaration, it makes this part a valid notice of consent. Send a copy to the HMRC office dealing with each claimant company's return, before or at the same time as that company claims the relief.",
  ],
};

const SIGNATORY_STATUS: PlainHelp = {
  meaning: ["The job title or role of the person who signs the declaration for the company."],
  example: ["Enter Director or Company secretary."],
  excludes: ["The person's name, which goes in the box before."],
  effect: ["It shows HMRC the person had the authority to give consent for the company."],
};

/** Plain-English help for supplementary page boxes, by box id. */
export const PAGE_BOX_HELP: Record<string, PlainHelp> = {
  A5: {
    meaning: [
      "This page is for close companies. A close company is controlled by 5 or fewer shareholders, or by shareholders who are also directors. Most family and owner-managed companies are close companies.",
      "Answer yes if the company lent money during this accounting period to a participator, and some or all of it was repaid, released or written off before the period ended. A participator is someone with a share or interest in the company, usually a shareholder. The rules also cover their associates, such as relatives and business partners.",
    ],
    example: [
      "A director who owns half the company's shares borrowed £12,000 in June 2025. They paid back £4,000 in December 2025, before the company's year ended on 31 March 2026. Answer yes.",
    ],
    excludes: [
      "Loans made in earlier accounting periods and repaid in this one.",
      "Repayments made after the period ended. Enter those in the tables for relief.",
      "Payments back to the company under tax avoidance arrangements made on or after 30 October 2024. These no longer count.",
    ],
    effect: [
      "It tells HMRC that the company lent more than the amount still owed at the end of the period. It does not change the tax, which is worked out on what was still owed.",
    ],
  },
  A10: {
    meaning: [
      "List each participator or associate who still owed the company money at the end of the period for loans made during the period. This includes an overdrawn director's loan account.",
      "For each person, enter the net amount lent during the period: everything the company paid to them or for them, minus what they paid back, minus anything the company owed them at the start of the period. Do not take off repayments of loans from earlier periods. Dividends, salary or bonuses credited to their account count as repayments.",
    ],
    example: [
      "At the start of the year, the company owed a director £2,000 on their loan account. During the year the company paid £30,000 of the director's personal bills and the director paid in £8,000. Enter £30,000 minus £8,000 minus £2,000, which is £20,000.",
    ],
    excludes: [
      "Loans made in earlier periods. Tax was charged on those in the period they were made.",
      "Loans of £15,000 or less in total to a director or employee who works full time for the company and owns 5% or less of it.",
      "Money owed for goods or services the company sold in its normal business, unless it gave more than 6 months' credit or longer than it normally gives customers.",
    ],
    effect: [
      "We charge tax on the total at 33.75% for loans made from 6 April 2022 to 5 April 2026, and 35.75% for loans made on or after 6 April 2026. The company pays this on top of its Corporation Tax, and it is due on the same date. If the loan is repaid within 9 months and 1 day of the end of the period, the tax does not have to be paid.",
      "HMRC's online service will not accept the 35.75% rate until 6 April 2027. Until then we file at 33.75% and show how much more the company will owe when it amends the return.",
    ],
  },
  A25: {
    meaning: [
      "Use this table if a loan in the outstanding loans table was repaid, released or written off after the period ended, but within 9 months of the end. The company then gets relief straight away, so it does not pay the tax on that amount.",
      "A loan is released or written off when the company formally lets the person off, or accepts that it will not get the money back. Enter one row for each person, with the total they repaid and the date of their last repayment. Enter a separate row for each loan, or part of a loan, that was released or written off.",
    ],
    example: [
      "The company's period ended on 31 March 2026 and a director owed £20,000 from loans made during it. They repaid £12,000 on 31 July 2026. Enter £12,000 as repaid, with the date 31 July 2026. The relief is £12,000 at 33.75%, which is £4,050, so the tax falls from £6,750 to £2,700.",
    ],
    excludes: [
      "Repayments made before the period ended, which are already taken off in the outstanding loans table.",
      "Repayments more than 9 months after the period ended. Use the table for relief due now instead.",
      "A repayment of £5,000 or more matched by new borrowing of £5,000 or more within 30 days. HMRC treats it as repaying the new loan, not the old one.",
    ],
    effect: [
      "We work out the relief at the same rate the loan was charged at and take it off the tax, in box A45. The total repaid cannot be more than the loans in the outstanding loans table.",
      "If a loan to a director is released or written off, the company must also deduct Class 1 National Insurance through its payroll, and the director pays Income Tax on it through Self Assessment.",
    ],
  },
  A50: {
    meaning: [
      "Use this table only if a loan made during this period was repaid, released or written off more than 9 months after the period ended, and the relief is already due when you file this return.",
      "Relief for a late repayment is due 9 months and 1 day after the end of the accounting period in which the repayment was made. Most companies will not need this table. It is usually only for returns filed very late.",
    ],
    example: [
      "The company's period ended on 31 December 2024 and a participator owed £10,000 from a loan made during it. They repaid it on 30 November 2025, in the company's next period, which ended on 31 December 2025. Relief is due from 1 October 2026. If the company files this return after that date, enter £10,000 and the date 30 November 2025.",
    ],
    excludes: [
      "Repayments within 9 months of the end of the period. Use the table for relief within 9 months.",
      "Repayments where the relief is not due yet. The company must claim that relief separately once it is due.",
    ],
    effect: [
      "We work out the relief at the same rate the loan was charged at and take it off the tax, in box A70. We also tick box 485 on the main return to tell HMRC.",
    ],
  },
  A75: {
    meaning: [
      "The total that all participators and their associates owed the company at the end of the period, for loans from this period and all earlier ones. This includes overdrawn directors' loan accounts.",
    ],
    example: [
      "A director owed £15,000 from loans made 2 years ago and borrowed a further £20,000 this year. None of it has been repaid. Enter £35,000.",
    ],
    excludes: [
      "Loans that were repaid, released or written off by the end of the period.",
      "Money the company owes to participators, such as a director's loan account in credit.",
    ],
    effect: [
      "It is for HMRC's information and does not change the tax on this page. Tax is only charged on loans made in this period.",
    ],
  },

  C5: {
    meaning: [
      "Group relief lets a company use another company's losses to reduce its own taxable profits. Both companies must be in the same group: one owns at least 75% of the other, or a third company owns at least 75% of both. Relief can also be claimed through a consortium, where several companies each own at least 5% of a company and together own at least 75%.",
      "List each company that is giving up, or surrendering, losses to this company. Enter its name, its tax reference (its 10-digit Unique Taxpayer Reference, or its company registration number), its accounting period if it is different from this company's, and the amount claimed.",
    ],
    example: [
      "Your company made profits of £80,000. Its sister company, owned by the same parent company, made a trading loss of £30,000 in the same year and agrees to surrender all of it. Enter the sister company's details and £30,000. Your company then pays tax on £50,000.",
    ],
    excludes: [
      "Losses the other company carried forward from earlier periods. Claim those in the table for carried-forward losses.",
      "Losses from any time when the companies were not in the same group or consortium.",
      "Losses of a company outside the UK, other than from a UK branch, for accounting periods starting on or after 27 October 2021.",
    ],
    effect: [
      "We add up the amounts and take the total off the company's profits, in box 310. The total cannot be more than the company's profits after qualifying charitable donations. If the 2 companies' accounting periods only partly overlap, only the overlapping part counts.",
      "Each surrendering company must give written consent, called a notice of consent, and a copy goes with this return, unless the group has a simplified arrangement with HMRC.",
    ],
  },
  C15: PERMANENT_ESTABLISHMENT,
  C20: {
    meaning: [
      "Tick this if the claim involves a company not resident in the UK in any way other than through a UK branch or office. This includes when the company claiming, the company surrendering, or a company that links them in the group, is not resident in the UK.",
    ],
    example: [
      "Your company and its sister company are both owned by a parent company in France. Your company claims the sister company's £25,000 loss. Tick this box, because the group relationship depends on a company outside the UK.",
    ],
    excludes: [
      "Losses of a UK branch of a company outside the UK. Tick the box for permanent establishments instead.",
      "Losses of a company outside the UK, other than from a UK branch, for accounting periods starting on or after 27 October 2021. These cannot be claimed at all.",
    ],
    effect: [
      "It tells HMRC the claim involves a company outside the UK, so it can check the claim meets the extra conditions for that. It does not change the amount we take off the profits.",
    ],
  },
  C25: {
    meaning: [
      "Some groups agree a simplified arrangement with HMRC. One company in the group, the authorised company, makes group relief claims and surrenders for all of them, so claimants do not need to send copies of each notice of consent.",
      "Tick this to confirm the authorised company has approved this company's claim.",
    ],
    example: [
      "Your group has a simplified arrangement and the parent company is the authorised company. Its finance director approves your company's £30,000 claim. Tick this box and enter the parent company's name and the finance director's name and job title.",
    ],
    excludes: [
      "Groups without a simplified arrangement. They send a copy of each notice of consent with the return instead.",
    ],
    effect: [
      "It means no notices of consent need to be attached to this return. Enter the authorised company's details in the next boxes.",
    ],
  },
  C30: AUTHORISED_COMPANY,
  C35: AUTHORISED_PERSON,
  C40: AUTHORISED_STATUS,
  C45: {
    meaning: [
      "Enter how much of this period's trading loss the company is giving up, or surrendering, to other companies in its group or consortium. A trading loss is when the costs of running the business that are allowed for tax are more than its income from it.",
      "The company can surrender all of its trading loss, even if it has other profits it could have used it against.",
    ],
    example: [
      "The company made a trading loss of £45,000. It surrenders £30,000 to its parent company and keeps £15,000 to carry forward. Enter £30,000.",
    ],
    excludes: [
      "Trading losses carried forward from earlier periods. Enter those in the part for carried-forward losses.",
      "Capital losses from selling assets, which cannot be surrendered.",
    ],
    effect: [
      "We add it to the total surrendered. The company cannot use the amount it surrenders itself, so it is not carried forward. It cannot be more than this period's trading loss.",
    ],
  },
  C46: NORTHERN_IRELAND,
  C50: {
    meaning: [
      "This is for capital allowances on equipment the company leases out, but not as part of its trade. This is called special leasing. When the allowances are more than the income from that leasing, the company can surrender the excess.",
    ],
    example: [
      "The company leases a machine to another business, outside its own trade. It gets £8,000 in rent and claims £20,000 of capital allowances on the machine. Enter the £12,000 excess, or the part of it the company surrenders.",
    ],
    excludes: [
      "Capital allowances on assets used in the company's trade, which are part of its trading loss.",
      "Allowances brought forward from earlier periods.",
    ],
    effect: [
      "We add it to the total surrendered. The company can surrender it even if it has other profits it could use it against.",
    ],
  },
  C55: {
    meaning: [
      "Loan relationships are the company's borrowing and lending, such as bank loans and loans to or from other companies. A non-trading deficit is when the costs of borrowing that is not for the trade, such as interest, are more than the income from non-trading lending, such as bank interest.",
    ],
    example: [
      "The company borrowed money to buy an investment and paid £9,000 interest. It earned £1,000 of bank interest. Its non-trading deficit is £8,000, and it surrenders all of it. Enter £8,000.",
    ],
    excludes: [
      "Interest on borrowing used for the trade, which is a trading cost.",
      "Deficits carried forward from earlier periods.",
    ],
    effect: [
      "We add it to the total surrendered. The company can surrender it even if it has other profits it could use it against.",
    ],
  },
  C60: {
    meaning: [
      "If the company gave more to charities, community amateur sports clubs or grassroots sport than its profits, it can surrender the excess to another company in its group.",
    ],
    example: [
      "The company's profits were £3,000 and it gave £10,000 to a registered charity. Enter the £7,000 excess, or the part of it the company surrenders.",
    ],
    excludes: [
      "Donations the company can use against its own profits for the period.",
      "Sponsorship or donations that are not qualifying charitable donations.",
    ],
    effect: [
      "We add it to the total surrendered. Excess donations cannot be carried forward, so surrendering them is the only way to use them.",
    ],
  },
  C65: {
    meaning: [
      "A UK property business loss is when the costs of letting land or buildings in the UK are more than the rents. The company can surrender the part of the loss that is more than its other profits for the period, whether or not it uses the loss itself.",
    ],
    example: [
      "The company made a £15,000 loss letting a building and had £5,000 of other profits. Enter the £10,000 excess, or the part of it the company surrenders.",
    ],
    excludes: [
      "Losses from letting property outside the UK.",
      "Property losses carried forward from earlier periods.",
    ],
    effect: ["We add it to the total surrendered."],
  },
  C70: {
    meaning: [
      "Management expenses are the costs of running an investment business, such as a company that holds shares or investments. The company can surrender the part of this period's management expenses that is more than its profits, whether or not it uses them itself.",
    ],
    example: [
      "A holding company spent £25,000 on management costs and had £5,000 of income. Enter the £20,000 excess, or the part of it the company surrenders.",
    ],
    excludes: [
      "Management expenses carried forward from earlier periods.",
      "Costs of a trade, which are part of the trading profit or loss.",
    ],
    effect: ["We add it to the total surrendered."],
  },
  C75: {
    meaning: [
      "Intangible fixed assets are things like patents, trademarks, copyright and goodwill. A non-trading loss on them is when the costs of intangible assets not used in the trade, such as writing down their value, are more than the income from them.",
      "The company can surrender the part of this period's loss that is more than its profits.",
    ],
    example: [
      "The company owns a patent that it licenses out, but not as part of its trade. It wrote down the patent's value by £12,000 and received £4,000 in royalties. Enter the £8,000 loss, or the part of it the company surrenders.",
    ],
    excludes: [
      "Intangible assets used in the trade, which are part of the trading profit or loss.",
      "Losses carried forward from earlier periods.",
    ],
    effect: ["We add it to the total surrendered."],
  },
  C85: {
    meaning: [
      "List each company in the group or consortium that the company is surrendering amounts to. Enter its name, its tax reference (its 10-digit Unique Taxpayer Reference, or its company registration number), its accounting period if it is different from this company's, and the amount surrendered to it.",
    ],
    example: [
      "The company surrenders £30,000 to its parent company and £15,000 to its sister company. Enter 2 rows, one for £30,000 and one for £15,000.",
    ],
    excludes: [
      "Carried-forward losses surrendered. Enter those in the part for carried-forward losses.",
    ],
    effect: [
      "The amounts must add up to the total surrendered. Each company listed claims its amount on its own CT600C.",
    ],
  },
  C115: SIGNATORY_NAME,
  C120: SIGNATORY_STATUS,
  C125: {
    meaning: [
      "Since 1 April 2017, a company can also surrender losses it has carried forward from earlier periods to other companies in its group. Only losses made on or after 1 April 2017 count.",
      "List each company surrendering carried-forward losses to this company. Enter its name, its tax reference (its 10-digit Unique Taxpayer Reference, or its company registration number), its accounting period if it is different from this company's, and the amount claimed.",
    ],
    example: [
      "Your company has profits of £60,000 and no losses of its own. Its sister company has £40,000 of trading losses from 2023 that it carried forward, and it made no profits this year to use them against. It surrenders the £40,000 to your company. Enter the sister company's details and £40,000.",
    ],
    excludes: [
      "Losses made before 1 April 2017.",
      "Losses of the surrendering company's current period. Claim those in the group relief table.",
      "Losses the surrendering company could use against its own profits this period.",
    ],
    effect: [
      "We take the total off the company's profits, in box 312, after group relief for current-period losses. The company must use its own carried-forward losses from 1 April 2017 or later first, so the claim cannot be more than the profits left after those.",
      "Only the first £5 million of profits can be fully covered by carried-forward losses, including these. Each surrendering company must give a notice of consent, unless a simplified arrangement applies.",
    ],
  },
  C135: PERMANENT_ESTABLISHMENT,
  C140: {
    meaning: [
      "Some groups agree a simplified arrangement with HMRC, where one authorised company makes claims and surrenders for the whole group. A group needs a separate application to use a simplified arrangement for carried-forward losses, even if it already has one for current-period losses.",
      "Tick this to confirm the authorised company has approved this company's claim for carried-forward losses.",
    ],
    example: [
      "Your group has a simplified arrangement for carried-forward losses and the parent company is the authorised company. It approves your company's £40,000 claim. Tick this box and enter the parent company's name and the details of the person who approved it.",
    ],
    excludes: [
      "Groups without a simplified arrangement for carried-forward losses. They send a copy of each notice of consent with the return instead.",
    ],
    effect: [
      "It means no notices of consent need to be attached to this return. Enter the authorised company's details in the next boxes.",
    ],
  },
  C145: AUTHORISED_COMPANY,
  C150: AUTHORISED_PERSON,
  C155: AUTHORISED_STATUS,
  C160: {
    meaning: [
      "Enter how much of the company's carried-forward trading losses it is surrendering to other companies in its group. Only trading losses made on or after 1 April 2017 can be surrendered this way.",
    ],
    example: [
      "The company has £50,000 of trading losses from 2022 carried forward, and no profits this year to use them against. It surrenders £35,000 to its parent company. Enter £35,000.",
    ],
    excludes: [
      "Trading losses made before 1 April 2017.",
      "This period's trading loss. Enter that in the part for amounts surrendered as group relief.",
      "Losses the company could use against its own profits this period.",
    ],
    effect: [
      "We add it to the total carried-forward losses surrendered. It cannot be more than the company's unused losses brought forward, and the company can no longer use the amount surrendered itself.",
    ],
  },
  C161: NORTHERN_IRELAND,
  C165: {
    meaning: [
      "A non-trading deficit on loan relationships is when interest and other costs of borrowing not used for the trade are more than the income from non-trading lending. Enter how much of such a deficit, carried forward from earlier periods, the company is surrendering.",
    ],
    example: [
      "The company has a £12,000 non-trading deficit from 2023 carried forward. It surrenders £12,000 to its sister company. Enter £12,000.",
    ],
    excludes: [
      "Deficits from before 1 April 2017.",
      "This period's deficit. Enter that in the part for amounts surrendered as group relief.",
    ],
    effect: ["We add it to the total carried-forward losses surrendered."],
  },
  C170: {
    meaning: [
      "Enter how much of the company's UK property business losses, carried forward from earlier periods, it is surrendering. A UK property business loss is when the costs of letting land or buildings in the UK are more than the rents.",
    ],
    example: [
      "The company has £18,000 of losses from letting a building in 2024 carried forward. It surrenders £18,000 to its parent company. Enter £18,000.",
    ],
    excludes: [
      "Losses from before 1 April 2017.",
      "Losses from letting property outside the UK.",
      "This period's property loss. Enter that in the part for amounts surrendered as group relief.",
    ],
    effect: ["We add it to the total carried-forward losses surrendered."],
  },
  C175: {
    meaning: [
      "Management expenses are the costs of running an investment business, such as a company that holds shares or investments. Enter how much of the company's unused management expenses, carried forward from earlier periods, it is surrendering.",
    ],
    example: [
      "A holding company has £22,000 of management expenses from 2023 carried forward. It surrenders £22,000 to a trading company in its group. Enter £22,000.",
    ],
    excludes: [
      "Management expenses from before 1 April 2017.",
      "Charitable donations carried forward as management expenses, which cannot be surrendered.",
    ],
    effect: ["We add it to the total carried-forward losses surrendered."],
  },
  C180: {
    meaning: [
      "Intangible fixed assets are things like patents, trademarks, copyright and goodwill. Enter how much of the company's non-trading losses on them, carried forward from earlier periods, it is surrendering.",
    ],
    example: [
      "The company has a £9,000 non-trading loss on a patent it licenses out, carried forward from 2024. It surrenders £9,000 to its sister company. Enter £9,000.",
    ],
    excludes: [
      "Losses from before 1 April 2017.",
      "Losses on intangible assets used in the trade, which are part of the trading loss.",
    ],
    effect: ["We add it to the total carried-forward losses surrendered."],
  },
  C190: {
    meaning: [
      "List each company in the group that the company is surrendering carried-forward losses to. Enter its name, its tax reference (its 10-digit Unique Taxpayer Reference, or its company registration number), its accounting period if it is different from this company's, and the amount surrendered to it.",
    ],
    example: [
      "The company surrenders £35,000 of carried-forward trading losses to its parent company. Enter one row for the parent company with £35,000.",
    ],
    excludes: [
      "This period's losses surrendered. Enter those in the part for amounts surrendered as group relief.",
    ],
    effect: [
      "The amounts must add up to the total carried-forward losses surrendered. The notice of consent must say which loss is being surrendered.",
    ],
  },
  C220: SIGNATORY_NAME,
  C225: SIGNATORY_STATUS,

  L5: {
    meaning: [
      "Research and development expenditure credit (RDEC) is a taxable credit for R&D spending. For accounting periods starting on or after 1 April 2024 it is worth 20% of qualifying spending. If the credit is more than the company's Corporation Tax, part of it is held back at step 2 of this page as notional tax, and carried forward to pay Corporation Tax in later periods.",
      "Enter the total held back in earlier periods and not used yet. It is in box L140 of the company's last CT600L. You can also include RDEC that another company in the group surrendered to this company at step 2 or step 5.",
    ],
    example: [
      "Last year the company had £6,000 held back at step 2. This year its Corporation Tax is £4,000. Enter £6,000. It pays the £4,000 of tax, and £2,000 carries forward to next year.",
    ],
    excludes: [
      "Amounts carried forward at step 3 because of the PAYE cap. Enter those in box L20.",
      "This period's RDEC, which we work out from the R&D details.",
    ],
    effect: [
      "We use it to pay this period's Corporation Tax first, before any new RDEC, and carry forward whatever is left.",
    ],
  },
  L20: {
    meaning: [
      "The PAYE cap limits how much RDEC can be paid to a company: £20,000 plus 3 times its PAYE and National Insurance bills. If the company's credit was more than the cap in an earlier period, the excess was carried forward at step 3.",
      "That excess counts as RDEC for this period, even if the company makes no new R&D claim. Enter the total carried forward. It is in box L145 of the company's last CT600L.",
    ],
    example: [
      "Last year the company's credit after step 2 was £50,000 but its PAYE cap was £35,000, so £15,000 was carried forward. Enter £15,000.",
    ],
    excludes: ["Amounts held back at step 2 as notional tax. Enter those in box L5."],
    effect: [
      "We add it to this period's RDEC at step 1, where it pays Corporation Tax first. It is not reduced again for notional tax at step 2, because it has already been taxed.",
    ],
  },
  L35: {
    meaning: [
      "Some income reaches the company with Income Tax already taken off. The company can set that tax against its Corporation Tax, in box 515 of the main return. This box is for the part of that Income Tax that is set against the Corporation Tax in box 475.",
    ],
    example: [
      "The company was paid £1,000 of interest with £200 of Income Tax taken off, so it received £800. It has no other tax on the return apart from Corporation Tax. This box would be £200.",
    ],
    excludes: ["Deductions from payments under the Construction Industry Scheme."],
    effect: [
      "This service does not handle Income Tax deducted from the company's income, so leave this box blank. If the company has had Income Tax deducted, get help from an accountant.",
    ],
  },
  L71: {
    meaning: [
      "The PAYE cap limits how much RDEC can be paid to a company: £20,000 plus 3 times its PAYE and National Insurance bills. The cap does not apply if the company meets 2 conditions.",
      "First, its own employees are creating, or preparing to create, intellectual property such as patents, designs or copyright, or are managing intellectual property the company owns. Directors only count if they are also employees. Second, what it spends on workers supplied by connected companies, and on R&D subcontracted to them, is no more than 15% of its qualifying R&D spending. Connected companies are ones under the same control, such as others in the same group.",
    ],
    example: [
      "The company's 6 employees develop software it owns. It spends £200,000 on qualifying R&D, including £10,000 on work subcontracted to a sister company. £10,000 is 5% of £200,000, so the exception applies. Tick the box.",
    ],
    excludes: [
      "Companies whose R&D is done wholly or mainly by subcontractors, not their own employees.",
      "Claims under both merged-scheme RDEC and enhanced R&D intensive support. Use box L167 instead.",
    ],
    effect: [
      "The PAYE cap no longer limits the credit, so do not enter the company's PAYE and National Insurance. You must enter the spending with connected companies in box L71A.",
    ],
  },
  L71A: {
    meaning: [
      "Enter what the company spent in this period on externally provided workers from connected companies, and on R&D subcontracted to connected companies. Externally provided workers are staff supplied by another business. Only count spending that qualifies for R&D relief.",
      "It must be no more than 15% of the R&D spending the RDEC is claimed on.",
    ],
    example: [
      "The company claims RDEC on £200,000 of R&D spending. It paid a sister company £10,000 for R&D subcontracted to it. Enter £10,000. The most it could be is £30,000, which is 15% of £200,000.",
    ],
    excludes: [
      "Spending with businesses that are not connected to the company.",
      "Spending that does not qualify for R&D relief.",
    ],
    effect: [
      "We check it is no more than 15% of the R&D spending. If it is more, the exception does not apply and the PAYE cap limits the credit.",
    ],
  },
  L72: {
    meaning: [
      "Enter the Income Tax the company deducted under PAYE and the Class 1 National Insurance it must pay to HMRC for payroll periods in this accounting period. Include all staff, not just those working on R&D, and both employer's and employees' National Insurance.",
      "Do not reduce it for statutory pay the company recovers, such as statutory maternity, paternity or adoption pay.",
    ],
    example: [
      "The company's payroll reports for the year show £48,000 of PAYE Income Tax and £36,000 of Class 1 National Insurance. Enter £84,000. Its PAYE cap is £20,000 plus 3 times £84,000, which is £272,000.",
    ],
    excludes: [
      "PAYE and National Insurance of connected companies. Enter those in box L73.",
      "Class 1A National Insurance on benefits in kind.",
    ],
    effect: [
      "We use it to work out the PAYE cap, which limits how much RDEC can be paid out at step 3. Any credit above the cap carries forward to the next period. If the period is shorter than 12 months, the £20,000 is reduced proportionately.",
    ],
  },
  L72A: {
    meaning: [
      "The reference HMRC gave the company when it registered as an employer. It is a 3-digit HMRC office number and a reference, such as 123/AB45678. You can find it on the company's P60 forms and letters from HMRC about PAYE. You can give up to 2 references.",
    ],
    example: [
      "The company's employer PAYE reference is 123/AB45678. Enter 123 as the office number and AB45678 as the reference.",
    ],
    excludes: [
      "The company's Unique Taxpayer Reference or its Accounts Office reference, which are different numbers.",
    ],
    effect: ["It lets HMRC match the PAYE and National Insurance figure to the company's payroll."],
  },
  L73: {
    meaning: [
      "If a connected company supplies workers for this company's R&D, or carries out R&D subcontracted to it, this company can add the part of that company's PAYE and National Insurance that relates to the work. Connected companies are ones under the same control, such as others in the same group.",
    ],
    example: [
      "A sister company supplies 2 engineers for the company's R&D project. The PAYE and National Insurance on their pay for the work is £18,000. Enter £18,000.",
    ],
    excludes: [
      "The connected company's PAYE and National Insurance for other work.",
      "Businesses that are not connected to the company.",
    ],
    effect: [
      "We add it to the company's own PAYE and National Insurance when working out the PAYE cap, so the cap is higher. Give each connected company's employer PAYE reference in the next box.",
    ],
  },
  L73A: {
    meaning: [
      "The employer PAYE reference of each connected company whose PAYE and National Insurance you included. It is a 3-digit HMRC office number and a reference, such as 456/CD12345.",
    ],
    example: [
      "The sister company's employer PAYE reference is 456/CD12345. Enter 456 as the office number and CD12345 as the reference.",
    ],
    excludes: ["This company's own employer PAYE reference, which goes in box L72A."],
    effect: ["It lets HMRC check the connected companies' figures against their payroll."],
  },
  L90: {
    meaning: [
      "RDEC left after steps 1 to 3 is used to pay any Corporation Tax the company owes for other accounting periods that is due and not yet paid.",
    ],
    example: [
      "The company has £25,000 of credit left after step 3. It still owes £8,000 of Corporation Tax for last year. Enter £8,000.",
    ],
    excludes: [
      "This period's Corporation Tax, which the credit pays at step 1.",
      "Other taxes, such as VAT or PAYE. Those come at step 6.",
    ],
    effect: [
      "It reduces the credit left for the later steps. It cannot be more than the credit left after step 3.",
    ],
  },
  L100: {
    meaning: [
      "If the company is in a group, it can give, or surrender, some or all of the credit left after step 4 to another group member, to pay that company's Corporation Tax. A group means one company owns at least 75% of the other, or a third company owns at least 75% of both.",
    ],
    example: [
      "The company has £17,000 of credit left after step 4. Its sister company owes £10,000 of Corporation Tax. The company surrenders £10,000 to it. Enter £10,000.",
    ],
    excludes: [
      "Amounts held back as notional tax at step 2. Enter surrenders of those in box L135.",
    ],
    effect: [
      "It reduces the credit left for steps 6 and 7. The company's tax computations must name the group member it surrendered the credit to.",
    ],
  },
  L110: {
    meaning: [
      "RDEC left after step 5 is used to pay other amounts the company owes on this return, apart from Corporation Tax. These include tax on loans to participators and the other amounts in boxes 480 to 505 of the main return.",
    ],
    example: [
      "The company has £7,000 of credit left after step 5. This return shows £2,700 of tax on a loan to a director. Enter £2,700.",
    ],
    excludes: [
      "Corporation Tax for this period, which the credit pays at step 1.",
      "Taxes outside this return, such as VAT. Enter those in box L115.",
    ],
    effect: [
      "We take it off the amount the company must pay on this return, through box 530. It cannot be more than the credit left after step 5.",
    ],
  },
  L115: {
    meaning: [
      "RDEC left after using it on this return is used to pay other amounts the company owes HMRC, such as VAT or PAYE.",
    ],
    example: [
      "The company has £4,300 of credit left and owes £3,000 of VAT that is due. Enter £3,000.",
    ],
    excludes: ["Amounts on this return. Enter those in box L110."],
    effect: [
      "It reduces the credit paid to the company. It cannot be more than the credit left after box L110.",
    ],
  },
  L123: {
    meaning: [
      "RDEC left after step 6 is only paid to the company if it was a going concern when it made the claim. A company is a going concern if its latest published accounts were prepared on the basis that it will keep trading, and that did not depend on getting R&D relief. A company in liquidation or administration is not a going concern.",
      "Enter the credit that cannot be paid because the company was not a going concern.",
    ],
    example: [
      "The company's latest published accounts were not prepared on a going concern basis. It has £9,000 of credit left after step 6. Enter £9,000.",
    ],
    excludes: ["Credit used at steps 1 to 6."],
    effect: ["We take it off the RDEC paid to the company, in box 880."],
  },
  L135: {
    meaning: [
      "Instead of carrying forward the RDEC held back as notional tax at step 2, the company can surrender some or all of it to another company in its group, to pay that company's Corporation Tax.",
    ],
    example: [
      "The company has £12,000 held back at step 2. Its sister company owes £5,000 of Corporation Tax. The company surrenders £5,000 to it and carries £7,000 forward. Enter £5,000.",
    ],
    excludes: [
      "Credit surrendered at step 5. Enter that in box L100.",
      "Amounts carried forward at step 3 because of the PAYE cap.",
    ],
    effect: [
      "It reduces the amount carried forward to the next period. The company's tax computations must name the group company it surrendered the credit to.",
    ],
  },
  L167: {
    meaning: [
      "A small or medium-sized company's R&D payable tax credit is capped at £20,000 plus 3 times its PAYE and National Insurance bills. This is the PAYE cap. It applies to SME scheme claims for periods starting from 1 April 2021 to 31 March 2024. For periods starting on or after 1 April 2024, it applies to enhanced R&D intensive support (ERIS), which is for loss-making companies whose R&D is at least 30% of their spending.",
      "The cap does not apply if 2 conditions are met. First, the company's own employees are creating, or preparing to create, intellectual property such as patents, designs or copyright, or are managing intellectual property it owns. Second, what it spends on workers supplied by connected companies, and on R&D subcontracted to them, is no more than 15% of its qualifying R&D spending.",
    ],
    example: [
      "The company's 4 employees are developing a medical device it plans to patent. It spends £150,000 on qualifying R&D and nothing with connected companies. Tick the box.",
    ],
    excludes: [
      "Companies whose R&D is done wholly or mainly by subcontractors, not their own employees.",
    ],
    effect: [
      "The PAYE cap no longer limits the credit, so do not enter the company's PAYE and National Insurance. You must enter the spending with connected companies in box L167A.",
    ],
  },
  L167A: {
    meaning: [
      "Enter what the company spent in this period on externally provided workers from connected companies, and on R&D subcontracted to connected companies. Externally provided workers are staff supplied by another business. Connected companies are ones under the same control, such as others in the same group.",
      "It must be no more than 15% of the company's qualifying R&D spending.",
    ],
    example: [
      "The company spends £150,000 on qualifying R&D, including £12,000 on engineers supplied by its sister company. Enter £12,000. The most it could be is £22,500, which is 15% of £150,000.",
    ],
    excludes: [
      "Spending with businesses that are not connected to the company.",
      "Spending that does not qualify for R&D relief.",
    ],
    effect: [
      "We check it is no more than 15% of the R&D spending. If it is more, the exception does not apply and the PAYE cap limits the credit.",
    ],
  },
  L168: {
    meaning: [
      "Enter the Income Tax the company deducted under PAYE and the Class 1 National Insurance it must pay to HMRC for payroll periods in this accounting period. Include all staff, not just those working on R&D, and both employer's and employees' National Insurance.",
      "Do not reduce it for statutory pay the company recovers, such as statutory maternity, paternity or adoption pay.",
    ],
    example: [
      "The company's payroll reports show £9,000 of PAYE Income Tax and £6,000 of Class 1 National Insurance. Enter £15,000. Its PAYE cap is £20,000 plus 3 times £15,000, which is £65,000.",
    ],
    excludes: [
      "PAYE and National Insurance of connected companies. Enter those in box L169.",
      "Class 1A National Insurance on benefits in kind.",
    ],
    effect: [
      "We use it to work out the PAYE cap. If the credit is more than the cap, we limit it to the cap and only surrender as much of the loss as the capped credit needs, so the rest of the loss carries forward. If the period is shorter than 12 months, the £20,000 is reduced proportionately.",
    ],
  },
  L168A: {
    meaning: [
      "The reference HMRC gave the company when it registered as an employer. It is a 3-digit HMRC office number and a reference, such as 123/AB45678. You can find it on the company's P60 forms and letters from HMRC about PAYE. You can give up to 2 references.",
    ],
    example: [
      "The company's employer PAYE reference is 123/AB45678. Enter 123 as the office number and AB45678 as the reference.",
    ],
    excludes: [
      "The company's Unique Taxpayer Reference or its Accounts Office reference, which are different numbers.",
    ],
    effect: ["It lets HMRC match the PAYE and National Insurance figure to the company's payroll."],
  },
  L169: {
    meaning: [
      "If a connected company supplies workers for this company's R&D, or carries out R&D subcontracted to it, this company can add the part of that company's PAYE and National Insurance that relates to the work. Connected companies are ones under the same control, such as others in the same group.",
    ],
    example: [
      "A sister company supplies an engineer for the company's R&D. The PAYE and National Insurance on their pay for the work is £7,000. Enter £7,000.",
    ],
    excludes: [
      "The connected company's PAYE and National Insurance for other work.",
      "Businesses that are not connected to the company.",
    ],
    effect: [
      "We add it to the company's own PAYE and National Insurance when working out the PAYE cap, so the cap is higher. Give each connected company's employer PAYE reference in the next box.",
    ],
  },
  L169A: {
    meaning: [
      "The employer PAYE reference of each connected company whose PAYE and National Insurance you included. It is a 3-digit HMRC office number and a reference, such as 456/CD12345.",
    ],
    example: [
      "The sister company's employer PAYE reference is 456/CD12345. Enter 456 as the office number and CD12345 as the reference.",
    ],
    excludes: ["This company's own employer PAYE reference, which goes in box L168A."],
    effect: ["It lets HMRC check the connected companies' figures against their payroll."],
  },
  L175: {
    meaning: [
      "Enter how much of the company's R&D payable tax credit should pay other amounts the company owes on this return, such as tax on loans to participators. These are the amounts in boxes 480 to 505 of the main return.",
    ],
    example: [
      "The company's payable credit is £29,000 and this return shows £2,700 of tax on a loan to a director. Enter £2,700. The other £26,300 is paid to the company.",
    ],
    excludes: ["Taxes outside this return, such as VAT or PAYE."],
    effect: [
      "We take it off the amount the company must pay on this return, through box 530, and pay the rest of the credit to the company, in box 875. It cannot be more than the credit.",
    ],
  },
  L185: {
    meaning: [
      "For accounting periods starting before 1 April 2024, a small or medium-sized company cannot claim SME relief on R&D it does under contract for a large company. It can claim RDEC on that spending instead.",
      "Enter the RDEC claimed on that work. The rate is 20% for spending on or after 1 April 2023, and 13% from 1 April 2020 to 31 March 2023.",
    ],
    example: [
      "In its accounting period from 1 January 2024 to 31 December 2024, the company spent £50,000 on R&D it did for a large company under contract. Enter £10,000, which is 20% of £50,000.",
    ],
    excludes: [
      "Accounting periods starting on or after 1 April 2024, when the merged RDEC scheme applies.",
      "R&D the company does for itself, which qualifies for SME relief.",
    ],
    effect: [
      "We use it as the company's RDEC at step 1, and add it to its taxable trading income. You also need to give the spending the RDEC is claimed on.",
    ],
  },
  L190: {
    meaning: [
      "For accounting periods starting before 1 April 2024, a small or medium-sized company cannot claim SME relief on R&D spending that is subsidised, such as by a grant, or on a project where its state aid goes over €7.5 million. It can claim RDEC on that spending instead.",
      "Enter the RDEC claimed on that spending. The rate is 20% for spending on or after 1 April 2023, and 13% from 1 April 2020 to 31 March 2023.",
    ],
    example: [
      "In its accounting period from 1 January 2024 to 31 December 2024, £40,000 of the company's R&D spending was paid for by a government grant, so it counts as subsidised. Enter £8,000, which is 20% of £40,000.",
    ],
    excludes: [
      "Accounting periods starting on or after 1 April 2024, when the merged RDEC scheme applies.",
      "R&D spending that is not subsidised or capped, which qualifies for SME relief.",
    ],
    effect: [
      "We use it as the company's RDEC at step 1, and add it to its taxable trading income. You also need to give the spending the RDEC is claimed on.",
    ],
  },
};
