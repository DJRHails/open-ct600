/**
 * Help for the tax adjustments questions, written from HMRC's guidance:
 * https://www.gov.uk/corporation-tax-rates (the expenses, rates and associated companies),
 * https://www.gov.uk/capital-allowances, https://www.gov.uk/work-out-capital-allowances (pools
 * and writing down allowances: main pool 14% from 1 April 2026 for Corporation Tax, 18% before),
 * https://www.gov.uk/tax-limited-company-gives-to-charity,
 * https://www.gov.uk/government/collections/corporation-tax-on-chargeable-gains-indexation-allowance-rates
 * and the Capital Gains Manual (CG17231: indexation frozen at December 2017 for companies'
 * disposals of assets held before 2018; CG46100: indexation cannot create or increase a loss),
 * https://www.gov.uk/guidance/corporation-tax-calculating-and-claiming-a-loss,
 * https://www.gov.uk/guidance/corporation-tax-marginal-relief and the Company Taxation Manual
 * (CTM03940 and CTM03945 for associated companies).
 */
import type { QuestionHelp } from "@/content/help/types";
import type { TAX_ADJUSTMENTS } from "@/filing/model";

type Key = (typeof TAX_ADJUSTMENTS)["fields"][number]["key"];

export const TAX_ADJUSTMENTS_HELP: Record<Key, QuestionHelp> = {
  disallowable_expenses: {
    topic: "disallowable expenses",
    plain: {
      meaning: [
        "Your accounts show everything the company spent. For tax, some of those costs cannot be taken off profits. These are called disallowable expenses.",
        "The most common are entertaining clients or suppliers, fines and penalties, political donations, and costs that are not only for the business, such as a director's personal bills paid by the company.",
      ],
      example: [
        "The company's profit and loss account includes £1,200 for taking clients to dinner and a £100 parking fine. Enter £1,300.",
      ],
      excludes: [
        "Depreciation. We add it back for you from your profit and loss account, so do not include it here.",
        "Staff entertaining, like a Christmas party for employees. That is allowed.",
        "Costs of buying equipment or vehicles. Claim capital allowances for those instead.",
      ],
      effect: [
        "We add the amount back to the company's profits, so it pays tax on it. It cannot be more than the total expenses in your profit and loss account.",
      ],
    },
    hmrc: [{ box: "155" }],
  },
  capital_allowances: {
    topic: "capital allowances",
    plain: {
      meaning: [
        "When a company buys equipment, tools, machinery, computers or vehicles to use in the business, it cannot take their cost off its profits as an expense. It claims capital allowances instead.",
        "Most items qualify for the Annual Investment Allowance (AIA), which lets the company deduct their full cost in the year it bought them, up to £1 million a year. Companies can also claim full expensing on most new equipment.",
        "Cars do not qualify for the AIA. For cars, and for anything else whose full cost the company has not claimed, it claims a percentage of the value left each year, called a writing down allowance. It carries on claiming this in later years, even in a year it buys nothing new.",
      ],
      example: [
        "The company bought 2 laptops for £2,400 and a van for £18,000. It claims the AIA on both, so enter £20,400.",
        "Another company bought nothing this period, but its main pool, the value left from equipment it bought in earlier years, is £40,000. For a period from 1 April 2026 to 31 March 2027 the main pool rate is 14%, so it claims a writing down allowance of £5,600. Answer yes and enter £5,600.",
      ],
      excludes: [
        "Depreciation in your accounts, which is not the same thing and is added back for you.",
        "Things the company leases or rents, which are normal expenses.",
        "Buildings and land, except for some fixtures and the structures and buildings allowance.",
        "Items used only for personal purposes.",
      ],
      effect: [
        "We take the amount off the company's trading profits before working out the tax. If the allowances are more than the profits, the company makes a trading loss, which it can carry forward to later periods.",
        "If you answer no, the company claims no capital allowances this period, not even writing down allowances on things bought before.",
      ],
    },
    hmrc: [{ box: "690" }, { box: "688" }, { box: "705" }],
  },
  losses_brought_forward: {
    topic: "trading losses brought forward",
    plain: {
      meaning: [
        "If the company made a trading loss in an earlier accounting period and has not used it yet, it can use it to reduce this period's trading profits.",
        "You can find the amount on the company's last Company Tax Return or tax computation, as losses carried forward.",
      ],
      example: [
        "The company made a loss of £8,000 last year and has trading profits of £5,000 this year. Enter £8,000. We use £5,000 of it this year, and the other £3,000 is carried forward to next year.",
      ],
      excludes: [
        "A loss made in this accounting period. We work that out from your figures.",
        "Capital losses from selling assets, property business losses and other losses that are not from the trade.",
        "Losses the company has already used or given to another company in its group.",
      ],
      effect: [
        "We use as much of the loss as the company's trading profits allow, and show the amount used in box 160, against trading profits. Very large amounts may be limited: only the first £5 million of profits can be fully covered by losses brought forward.",
        "HMRC's guide puts losses from periods ending on or after 1 April 2017 in box 285 when they are set against total profits. This service only sets losses against trading profits, so it shows every loss it uses in box 160. The tax is the same. If the company wants to set later losses against its other profits, such as interest or gains, ask an accountant.",
      ],
    },
    hmrc: [{ box: "160" }, { box: "285" }],
  },
  losses_brought_forward_before_april_2017: {
    topic: "losses from before 1 April 2017",
    plain: {
      meaning: [
        "The rules for using trading losses changed on 1 April 2017. Losses from before then can only be used against later profits of the same trade. Losses from after then can also be used against the company's other profits.",
        "We need to know how much of your losses brought forward are older, because the company must use its own later losses before it can claim group relief for another company's carried-forward losses.",
      ],
      example: [
        "The company has £20,000 of losses brought forward. £6,000 came from its accounting period ending 31 December 2016 and £14,000 from later periods. Enter £6,000.",
      ],
      excludes: [
        "Losses from accounting periods that began on or after 1 April 2017.",
        "Losses that have already been used.",
      ],
      effect: [
        "It limits how much group relief for carried-forward losses the company can claim on CT600C. It does not change the total losses brought forward.",
      ],
    },
    hmrc: [{ box: "160" }, { box: "312" }],
  },
  chargeable_gains: {
    topic: "chargeable gains",
    plain: {
      meaning: [
        "If the company sold or gave away an asset for more than it cost, the profit on it may be a chargeable gain. Companies pay Corporation Tax on these gains, not Capital Gains Tax.",
        "Assets include land and buildings, shares in other companies, and some other investments.",
        "The gain is what the company got for the asset, minus what it cost and the costs of buying and selling it. If the company owned the asset before 1 January 2018, it also takes off indexation allowance, which allows for inflation up to December 2017 only. Indexation allowance can reduce a gain to nothing, but cannot create or increase a loss.",
      ],
      example: [
        "The company bought a small office in 2019 for £150,000 and sold it this year for £190,000, paying £5,000 in legal and estate agent fees. It bought the office after 2017, so there is no indexation allowance. The gain is £190,000 minus £150,000 minus £5,000, which is £35,000. Enter £35,000.",
        "If it had bought the office in 2010 instead, it would also take off indexation allowance: £150,000 times the factor in HMRC's December 2017 table for the month it bought it. If that factor were 0.250, the allowance would be £37,500. That is more than the £35,000 gain, so the gain is reduced to nothing, not turned into a loss. Enter 0.",
      ],
      excludes: [
        "Equipment and vehicles the company claimed capital allowances on. Selling those is dealt with through capital allowances.",
        "Stock the company sells as part of its trade.",
        "Most gains on selling shares in a trading company the company owned at least 10% of for a year or more, which are exempt under the substantial shareholding exemption.",
        "Most intangible assets, like goodwill, created or bought after 1 April 2002.",
      ],
      effect: [
        "We add the gain to the company's taxable profits, in boxes 210 and 220. Enter the gain after indexation allowance and after taking off any capital losses the company can use against it.",
      ],
    },
    hmrc: [
      { box: "210" },
      { box: "215" },
      { box: "220" },
      {
        quote: {
          guide: "corporation-tax-on-chargeable-gains-indexation-allowance-rates",
          heading: "Indexation Allowance rates for Corporation Tax on chargeable gains",
          paragraphs: [
            "From 1 January 2018 the capital gains Indexation Allowance has been frozen. When a company or organisation makes a capital gain on or after 1 January 2018, the Indexation Allowance that is applied in order to determine the amount of the chargeable gain will be calculated up to December 2017.",
          ],
        },
      },
    ],
  },
  qualifying_donations: {
    topic: "qualifying charitable donations",
    plain: {
      meaning: [
        "Gifts of money to charities and community amateur sports clubs (CASCs) reduce the company's taxable profits. So do gifts of shares, land or property.",
      ],
      example: [
        "The company gave £500 to a local hospice, which is a registered charity. Enter £500.",
        "If the £500 is included in the expenses in your profit and loss account, also include it in disallowable expenses, so it is not taken off twice.",
      ],
      excludes: [
        "Sponsorship, where the company gets advertising or another business benefit. That is a normal business expense.",
        "Donations to political parties.",
        "Loans the charity will repay, and payments made on condition that the charity buys something from the company.",
        "Donations where the company got something back worth more than HMRC allows, like event tickets.",
      ],
      effect: [
        "We take the donations off the company's profits, in box 305, but only as far as there are profits to cover them. Relief for donations cannot be carried forward to later years.",
      ],
    },
    hmrc: [{ box: "305" }],
  },
  exempt_distributions: {
    topic: "dividends received",
    plain: {
      meaning: [
        "Dividends the company receives from shares it holds in other companies are usually not taxed.",
        "They still count when working out which rate of Corporation Tax the company pays. The small profits rate of 19% only applies when profits plus these dividends are £50,000 or less.",
      ],
      example: [
        "The company has profits of £45,000 and received £10,000 in dividends from shares in a listed company. Its profits for deciding the rate are £55,000, so it gets marginal relief instead of paying 19% on all of its profits. It still only pays tax on the £45,000.",
      ],
      excludes: [
        "Dividends from companies in the same group, where one owns more than half of the other.",
        "Interest from banks or loans. Enter bank interest in the profit and loss account.",
      ],
      effect: [
        "No tax is charged on the dividends themselves. They may mean the company pays a higher rate on its profits. They are shown in box 620.",
      ],
    },
    hmrc: [{ box: "620" }],
  },
  associated_companies: {
    topic: "associated companies",
    plain: {
      meaning: [
        "Two companies are associated if one controls the other, or the same person or people control both. Control usually means owning more than half of the shares or votes.",
        "The profit limits for the small profits rate (£50,000) and marginal relief (£250,000) are shared between associated companies. This stops owners splitting a business into several companies to pay less tax.",
      ],
      example: [
        "Sam owns all the shares in your company and in 2 other companies that trade. Your company has 2 associated companies. The limits are divided by 3, so the small profits rate only applies to profits up to £16,667.",
      ],
      excludes: [
        "Your own company. Only count the others.",
        "Companies that did not carry on any business during the period, such as dormant companies.",
        "Some holding companies that only hold shares in their subsidiaries and pass on the dividends they receive.",
      ],
      effect: [
        "We divide the £50,000 and £250,000 limits by the number of associated companies plus 1. This may mean the company pays more tax. The number is shown in box 326.",
      ],
    },
    hmrc: [{ box: "326" }],
  },
};
