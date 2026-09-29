import type { PageCode } from "@/api";

/** When each supplementary page applies, in a line, for the page chooser. CT600G is dormant. */
export const PAGE_DESCRIPTIONS: Record<Exclude<PageCode, "G">, string> = {
  A: "The company is a close company that lent money to a participator, such as a director's loan account that is overdrawn.",
  B: "The company has an interest in a controlled foreign company, has elected for the foreign permanent establishment exemption, or has hybrid or other mismatches.",
  C: "The company is claiming or surrendering group or consortium relief.",
  D: "The company is an insurance company making an overseas life assurance business declaration.",
  E: "The company is a charity or Community Amateur Sports Club claiming exemption from tax.",
  F: "The company has elected into tonnage tax for its shipping activities.",
  H: "The company paid royalties abroad and deducted tax at a reduced rate under a tax treaty or directive.",
  I: "The company carries on a ring fence trade in oil or gas and is liable to the supplementary charge.",
  J: "The company is party to a tax avoidance scheme that has a scheme reference number.",
  K: "The company received restitution interest from HMRC and must pay restitution tax on it.",
  L: "The company is claiming research and development relief or expenditure credit.",
  M: "The company is claiming allowances for investment in freeport or investment zone tax sites.",
  N: "The company is liable to Residential Property Developer Tax.",
  P: "The company is claiming a creative industries relief or expenditure credit, such as for film, television, video games, theatre, orchestras or exhibitions.",
};

export function pageName(code: PageCode): string {
  return `CT600${code}`;
}
