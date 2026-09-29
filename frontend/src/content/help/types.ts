/**
 * Help for the questions in the return. Each question has help in plain English, written for
 * this service from HMRC's guidance, and HMRC's own guidance, quoted word for word.
 */

/** A question's help in plain English, always in this order. Each is a list of paragraphs. */
export type PlainHelp = {
  /** What the question means. */
  meaning: string[];
  /** An example with numbers. */
  example: string[];
  /** What the answer does not include. */
  excludes: string[];
  /** What happens if the company answers yes or enters an amount. */
  effect: string[];
};

/**
 * Words quoted from one of the gov.uk guides saved in ``specs/hmrc/guidance``, for a question
 * with no box of its own. A test checks each paragraph appears word for word in the guide.
 */
export type HmrcQuote = {
  /** The guide's file name there without ".md", its gov.uk slug, like "company-tax-returns". */
  guide: string;
  /** The heading in the guide the words are under, as it is written there. */
  heading: string;
  paragraphs: string[];
};

/** Where HMRC's guidance for a question is: a box on the return or a page, or a quote. */
export type HmrcRef = { box: string } | { quote: HmrcQuote };

export type QuestionHelp = {
  /** The precise term, for "Help with capital allowances". */
  topic: string;
  plain: PlainHelp;
  hmrc: HmrcRef[];
};
