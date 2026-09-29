/**
 * Help for the profit and loss account questions, written from HMRC's guidance:
 * https://www.gov.uk/guidance/the-company-tax-return-guide (boxes 145, 155 and 170),
 * https://www.gov.uk/corporation-tax-rates (the expenses), https://www.gov.uk/capital-allowances
 * and Companies House's guidance on annual accounts, https://www.gov.uk/annual-accounts.
 */
import type { QuestionHelp } from "@/content/help/types";
import type { PROFIT_AND_LOSS } from "@/filing/model";

type Key = (typeof PROFIT_AND_LOSS)["fields"][number]["key"];

export const PROFIT_AND_LOSS_HELP: Record<Key, QuestionHelp> = {
  turnover: {
    topic: "turnover",
    plain: {
      meaning: [
        "The total the company earned from its trade in the accounting period: sales of goods and fees for services, before taking off any costs.",
        "If the company is registered for VAT, enter turnover without the VAT it charged.",
      ],
      example: [
        "The company invoiced clients £96,000 plus £19,200 VAT for work done in the period. Enter £96,000.",
      ],
      excludes: [
        "Interest from bank or building society accounts. Enter that separately.",
        "Dividends from shares the company owns, and money from selling equipment, property or shares.",
        "Money the owners paid into the company, and loans it received.",
      ],
      effect: [
        "We show it in box 145 and in the company's profit and loss account. We use it to work out the company's trading profits, in box 155.",
      ],
    },
    hmrc: [{ box: "145" }, { box: "155" }],
  },
  interest_income: {
    topic: "bank and building society interest",
    plain: {
      meaning: [
        "Interest the company earned on money in bank or building society accounts during the accounting period.",
      ],
      example: [
        "The company's savings account paid £240 of interest and its business current account paid £60. Enter £300.",
      ],
      excludes: [
        "Interest the company paid on loans or overdrafts. That is an expense.",
        "Dividends from shares the company owns.",
      ],
      effect: [
        "Interest is not part of the company's trading profits. We show it separately in box 170, as profits from non-trading loan relationships, and it is taxed with the company's other profits.",
        "We also include it in the profit and loss account in the company's accounts.",
      ],
    },
    hmrc: [{ box: "170" }],
  },
  cost_of_sales: {
    topic: "cost of sales",
    plain: {
      meaning: [
        "The direct costs of the goods or services the company sold in the period, such as stock, materials and work bought in for particular jobs.",
        "For stock, it is the stock at the start of the period plus what the company bought, less the stock left at the end.",
      ],
      example: [
        "The company had £5,000 of stock at the start of the period, bought £30,000 more and had £8,000 left at the end. Its cost of sales is £5,000 plus £30,000 minus £8,000, which is £27,000.",
      ],
      excludes: [
        "Running costs such as rent, insurance and accountancy fees. Enter them in other expenses.",
        "Staff costs, if you enter them in staff costs, so they are not counted twice.",
        "Equipment, tools and vehicles the company will use for more than a year. Claim capital allowances for those.",
      ],
      effect: [
        "We take it off turnover when we work out the company's trading profits, in box 155. It is shown in the company's profit and loss account.",
      ],
    },
    hmrc: [{ box: "155" }],
  },
  staff_costs: {
    topic: "staff costs",
    plain: {
      meaning: [
        "What the company paid its employees, including directors, for the period: gross salaries, wages and bonuses, employer's National Insurance, and pension contributions the company paid for them.",
      ],
      example: [
        "The company paid gross salaries of £60,000, employer's National Insurance of £7,500 and pension contributions of £1,800. Enter £69,300.",
      ],
      excludes: [
        "Dividends paid to shareholders. They are paid out of profits and are not an expense.",
        "Payments to freelancers and contractors who are not employees. Enter them in cost of sales or other expenses.",
        "Income Tax and employees' National Insurance taken from pay. These are already part of gross salaries, so do not add them again.",
      ],
      effect: [
        "We take it off turnover when we work out the company's trading profits, in box 155. It is shown in the company's profit and loss account.",
      ],
    },
    hmrc: [{ box: "155" }],
  },
  depreciation: {
    topic: "depreciation",
    plain: {
      meaning: [
        "In its accounts, a company spreads the cost of equipment, vehicles and other long-term assets over the years it uses them. The amount charged for this period is called depreciation.",
      ],
      example: [
        "The company bought a laptop for £1,500 and expects to use it for 3 years. Its accounts charge £500 of depreciation each year, so enter £500.",
      ],
      excludes: [
        "The cost of buying the assets. Claim capital allowances for that in tax adjustments.",
        "Assets that are used up within the year, like stationery. Those are other expenses.",
      ],
      effect: [
        "Depreciation is taken off profits in the accounts, but it cannot be deducted for tax. We add it back for you when we work out the company's trading profits, in box 155. The company claims capital allowances instead.",
      ],
    },
    hmrc: [{ box: "155" }],
  },
  other_expenses: {
    topic: "other expenses",
    plain: {
      meaning: [
        "All the company's other running costs in the period that are in its profit and loss account, such as rent, business rates, utilities, insurance, travel, phone and internet, software, advertising, accountancy fees, bank charges and interest paid.",
        "Include costs that cannot be deducted for tax, such as client entertaining, if they are in your accounts. You list those again in disallowable expenses in tax adjustments.",
      ],
      example: [
        "The company paid rent of £9,600, insurance of £800, accountancy fees of £1,200 and software subscriptions of £600. Enter £12,200.",
      ],
      excludes: [
        "Cost of sales, staff costs and depreciation, which you enter separately.",
        "Corporation Tax and dividends.",
        "Equipment, tools and vehicles the company will use for more than a year. Claim capital allowances for those.",
      ],
      effect: [
        "We take it off turnover when we work out the company's trading profits, in box 155. It is shown in the company's profit and loss account.",
      ],
    },
    hmrc: [{ box: "155" }],
  },
};
