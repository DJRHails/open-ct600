# CT600 main return, supplementary pages A–P, and group relief / R&D / s455 rules

Research dossier for implementing the UK Company Tax Return (CT600 v3, the 2024, 2025 and 2026 editions) and every supplementary page. Compiled 2026-09-28 from gov.uk, legislation.gov.uk, HMRC internal manuals and HMRC's CT XML schema spec v1.995.

**How to read this.** Box numbers and labels come from the PDFs, checked against the schema.
- Types and cardinality come from the schema (`schema-box-map.tsv`, `schema/CT?-boxes.txt`).
- Arithmetic and cross-form rules come from the schema validation rules (`schema-rules.tsv`, `schema/CT?-rules.txt`), cited by HMRC error code.
- Everything else is cited inline to gov.uk, legislation.gov.uk or an HMRC manual URL.

## Key takeaways

1. **The main form changed twice in the target window** (details in "CT600 — Version differences"):
   - CT600 (2024) → (2025) added box 96 (CT600P tick), 541, 614, 653, 658, 663, 886 and 943, and relabelled 650/657/659/665/670.
   - (2025) → (2026) is wording only.
   - The online schema (v1.995) is already ahead of the 2026 PDF: it has boxes **696/739** (40% first-year allowance, for periods ending after 31 Dec 2025) and the 35.75% s455 rate.
2. **15 supplementary pages are live**: A, B, C, D, E, F, H, I, J, K, L, M, N and P, plus **CT600G (Northern Ireland)**, which is dormant.
   - CT600G has no PDF and no NI rate. It exists only in the schema, where the NI boxes are accepted only for periods ending on or after 1 Apr 2050.
   - **Pillar 2 (Multinational top-up tax / DMTT) is not a CT600 page.** It is filed through HMRC's separate Pillar 2 service (https://www.gov.uk/guidance/how-to-report-pillar-2-top-up-taxes). No CT600-series box relates to it, and the schema has no Pillar 2 element.
   - The **Energy Profits Levy** and **Electricity Generator Levy** are main-return boxes (986/987, 501/502), not pages.
3. **Pages that changed in the window**:
   - **CT600A**: 2026 wording limits s464A return-payment relief to payments made before 30 Oct 2024.
   - **CT600E (2026)**: adds E88 legacy income and a legacy table, E195/E200.
   - **CT600F (2025)**: adds F15C, managed-only ships.
   - **CT600L**: 2025 adds ERIS labels; 2026 adds L71–L73A (PAYE cap data for merged-RDEC-only claims).
   - **CT600P (2026)**: a new page. It is mandatory for returns filed from 6 Apr 2026. Before that, creative reliefs went directly into CT600 boxes 540/541/663/665/885/886.
   - The rest (B 2022, C 2018, D/H/J 2015, I 2019, K 2017, M 2024, N 2023) are unchanged through 2024–2026.
4. **s455 rate is now 35.75%** for loans made or benefits conferred **on or after 6 Apr 2026** (Budget 2025; HMRC online-service notice; schema v1.995). It was 33.75% from 6 Apr 2022 and 32.5% before that. HMRC's CT600A guidance still shows 33.75% as the latest rate.
5. **R&D**:
   - **Periods beginning before 1 Apr 2024**: old RDEC 20% (from 1 Apr 2023, notional tax at the main rate); SME 86%/10%, or 14.5% if R&D-intensive at ≥ 40%.
   - **Periods beginning on or after 1 Apr 2024**: **merged RDEC 20%**, with step 2 notional tax at 25% for main-rate companies and **19% otherwise**; or **ERIS** (86% additional deduction, 14.5% payable credit, intensity ≥ 30%, loss-making).
   - Both new schemes share the PAYE cap of **£20,000 + 300% of PAYE/NIC**.
   - Every claim needs the **additional information form** (box 657). A **claim notification** (box 656) is needed for first-time claimants or those with no claim in the last 3 years.
   - Flows: L210 → 530, L180 → 875, L125 → 880.
6. **Group relief**:
   - 75% group, meaning shares **and** the profit and asset entitlement; or a consortium of ≥ 75% owned by members holding ≥ 5% each, with relief limited to each member's lowest ownership proportion.
   - C10 → box 310; C130 → box 312.
   - It is deducted after donations: 300 → 305 → 310 → 312 → 315.
   - For non-coterminous periods, relief is the lower of the time-apportioned surrenderable amount and the claimant's available profits for the overlapping period.
7. **The HMRC guide contradicts the form and schema in three formulas**: 295 (the guide omits 285), 315 (omits 312) and 470 (says 480 instead of 450). Implement the form and schema version; they agree with each other.

## Supplementary page index

| Page | Current version | Version for 2024/2025 filings | CT600 tick box | CT600 boxes fed by the page |
|---|---|---|---|---|
| CT600A Close company loans / arrangements | CT600A (2026) v3 | CT600A (2015) v3 | 95 | A80 → 480; A70 completed → tick 485 |
| CT600B CFCs, foreign PE exemption, hybrids | CT600B (2022) v3 | same | 100 | B30 → 490 |
| CT600C Group and consortium relief | CT600C (2018) v3 | same | 105 | C10 → 310; C130 → 312 |
| CT600D Insurance | CT600D (2015) v3 | same | 110 | information only (see section) |
| CT600E Charities and CASCs | CT600E (2026) v3 | CT600E (2015) v3 | 115 | exemption claim; box 4 type 8 |
| CT600F Tonnage tax | CT600F (2025) v3 | 2025: same; 2024: CT600F (2023) v3 (no F15C, no code M) | 120 | F70 → 200; F45 → included in 450 |
| CT600G Northern Ireland | none published (schema only) | — | 125 | dormant; NI boxes 5–8, 325, 586, 856–858, C46, C161 |
| CT600H Cross-border royalties | CT600H (2015) v3 | same | 130 | links to tick 645 |
| CT600I Ring fence supplementary charge | CT600I (2019) v3 | same | 135 | I70 → 505; I80 → 585; I85 → 590; box 320 |
| CT600J DOTAS | CT600J (2015) v3 | same | 140 | required if box 65 ticked |
| CT600K Restitution tax | CT600K (2017) v3 | same | 141 | K35 → 527 |
| CT600L Research and development | CT600L (2026) v3 | (2022) v3 / (2025) v3 | 142 | L210 → 530; L180 → 875; L125 → 880; L166 = 659 |
| CT600M Freeports and Investment Zones | CT600M (2024) v3 | same | 143 | enhanced SBA/ECA detail; expenditure in 760/771 (see section) |
| CT600N Residential Property Developer Tax | CT600N (2023) v3 | same | 144 | N285 → 497 → 500 |
| CT600P Creative industries | CT600P (2026) v3 | none (boxes direct on CT600) | 96 | P325 → 540; P245 → 541; P310 → 663; P315 → 665; P330 → 885; P190 → 886 |

## Things not verified from an official source (consolidated; details in each section's caveats)

- **Main return** — guide vs form/schema formula conflicts: 295, 315, 470.
- **Main return** — boxes 696/739 (40% FYA) exist only in schema v1.995. HMRC says the online service adds them in April 2027; until then use 725/750 and 760.
- **Main return** — the 2024 and 2025 PDFs were recovered from Wayback copies of HMRC's own asset URLs, because gov.uk now redirects old asset IDs to the newest file. The same applies to CT600F (2023) v3, the edition used for 2024 filings.
- **R&D** — which size tick (650/655) a merged-scheme RDEC claimant uses from April 2024 is not stated. Whether box 780 is shown before or after losses surrendered for a payable credit is not stated.
- **R&D** — HMRC's online-service notice says to set **L75 = L70 for s1112E-exempt RDEC claims** until a validation fix in April 2027.
- **s455** — the online service applies 35.75% only from 6 Apr 2027. Returns filed earlier with post-6-Apr-2026 loans must be amended later (HMRC notice).
- **CT600B** — CFC charge rate for companies below the main-rate threshold: the statute says "the rate applicable", while the 2016 INTM manual says the main rate.
- **CT600E** — whether a CASC uses company type 0 or 6. How "additions in the period" applies to E170/E175. Rule 8026's English text swaps D and E. The E88/E200 cross-rules differ between live v1.994 and v1.995.
- **CT600F** — the managed-ship rates (£0.12/£0.09/£0.06/£0.03 per 100 nt) apply to elections from 1 Apr 2024 and are absent from the form and guidance.
- **CT600H** — the guidance still describes the Interest and Royalties Directive route, which was abolished for payments from 1 Jun 2021.
- **CT600I** — guidance typos (I50/I45 cap vs schema I35).
- **CT600J** — capped at 10 schemes per return; whether promoter reference numbers fit the 8-digit field is unconfirmed.
- **CT600K** — how to apportion across financial years.
- **CT600M** — no CT600 box takes the Freeport/Investment Zone allowance amount itself (only expenditure in 760); the location code list is in the guidance only.
- **CT600N** — the guidance's N285 = "4% of N285" should be N280. The pro-rata basis of the allowance for short periods (days vs months) is unconfirmed. HMRC's RPDT20100 example has an arithmetic typo.
- **CT600P** — the P195 vs P50 guidance conflict. The online-service bug for P260–P305 (enter £1 in column D). The MGETR end date. The old-relief section (P260–P285) is barred for periods starting on or after 1 Apr 2027 (rule 8061).
- **Parsed schema tables** — `schema-box-map.tsv` flattens `xsd:choice`. Elements shown 1..1 inside a choice (e.g. I10/I15, the plus/minus columns of I145/I150, CT600H column E(a)/E(b)) are **either/or**. Check the XSD (`../hmrc-submission/downloads/v1-995/HMRC-CT-2014-v1-995/CT-2014-v1-995.xsd`) before treating them as mandatory.

## Files

- `downloads/`: PDFs of every form and version; `downloads/MANIFEST.md` (+ `MANIFEST-extra-*.md`) lists the file, source URL, version string and md5.
- `text/`: text extracted from each PDF (PyMuPDF).
- `guidance/`: gov.uk guidance as markdown, including the CT600 guide (current and a 2025-09-18 snapshot), every CT600X guidance page, the R&D guidance, the rates page and the online-service change notices.
- `manuals/`: CTM (group relief, s455) and CIRD (R&D) pages used here.
- `schema/`, `schema-box-map.tsv`, `schema-rules.tsv`: box ↔ XML path ↔ type ↔ validation rule, parsed from HMRC's CT specDoc v1.995.
- `sections/`: the per-page sections concatenated below.
- `tools/`: two small helper scripts (gov.uk Content API fetcher, HTML→md).

---

# (a) Main return

## CT600 — Company Tax Return (main return)

- **Form versions** (all say "Version 3, for accounting periods starting on or after 1 April 2015"):
  - `downloads/CT600_2024_v3.pdf`: CT600 (2024) Version 3, footer HMRC 04/24. Recovered via the Wayback Machine, because gov.uk replaces its attachments.
  - `downloads/CT600_2025_v3.pdf`: CT600 (2025) Version 3, footer HMRC 04/25.
  - `downloads/CT600_2026_v3.pdf`: CT600 (2026) Version 3, footer HMRC 04/26. This is the current live attachment.
  - Publication: https://www.gov.uk/government/publications/corporation-tax-company-tax-return-ct600-2015-version-3
  - Box-by-box guide (HTML only; there is no PDF "CT600 Guide" any more): https://www.gov.uk/guidance/the-company-tax-return-guide (saved as `guidance/the-company-tax-return-guide.md`, updated 2026-06-02). The 2025 wording is in `guidance/the-company-tax-return-guide_wayback-20250918.md`.
- **Machine-readable source.** The HMRC XML schema spec CT-2014 v1.995 (modified 2026-09-03) was parsed into:
  - `schema-box-map.tsv` (1,396 elements: xpath, box id, type, cardinality)
  - `schema-rules.tsv` (1,035 validation rules)
  - per-form files under `schema/`
  
  Types below come from the schema:
  - "tick" = `CT_YesType`
  - "£" = `CTwholePoundStructure` (whole pounds)
  - "£p" = `CTpoundPenceStructure` (pounds and pence)
  - "count" = `nonNegativeInteger`

### Version differences for the main form (text diff of the three PDFs)

| Change | 2024 → 2025 | 2025 → 2026 |
|---|---|---|
| Box 96 "Creative industries – form CT600P" tick | **added** | — |
| Box 541 AVEC/VGEC; 545 label now "total box 530 to 541" | **added** | — |
| Box 614 AVEC/VGEC surrendered to this company | **added** | — |
| Box 653 R&D intensive SME tick | **added** | — |
| Box 657 relabelled "R&D additional information form"; **658** Creatives additional information form | **added** | — |
| Box 659 relabelled "…qualifying for SME/R&D intensive SME relief" | changed | — |
| Box 663 Creatives core expenditure (new); 665 relabelled "Creatives additional deduction" (was "Creative qualifying expenditure and/or additional deduction"); 670 relabelled | changed | — |
| Box 886 Payable AVEC/VGEC | **added** | — |
| Box 943 R&D payable-credit nominee tick | **added** | — |
| Box 650 label drops "and/or for all creatives claims" (creatives move to CT600P) | — | changed |
| Wording only (a/an, "Zero emissions"→"Zero-emission", "Electric"→"Electric vehicle") | cosmetic | cosmetic |

Two further boxes exist in the schema but not in the 2026 PDF: **696** (40% first-year allowance, in trading profits) and **739** (40% FYA, not in trading profits). Both are in schema v1.995, with rules 8081/8082 saying they must not be present if box 35 ≤ 2025-12-31. HMRC's online-service notice says to use boxes 725/750 and 760 for the 40% FYA until April 2027 (https://www.gov.uk/guidance/changes-and-issues-affecting-the-corporation-tax-online-service).

### Full box table (CT600 2025/2026 v3)

Only the calculations printed on the form are shown; a few differ from the guide, flagged ⚠.

**Company information**

| Box | Label | Type | Notes |
|---|---|---|---|
| 1 | Company name | text (1..1) | |
| 2 | Company registration number | text (0..1) | |
| 3 | Tax reference | UTR (10 digits) | |
| 4 | Type of company | integer 0–11 | 0 none; 1 unit trust/OEIC; 2 CIC; 3 company in liquidation (second or later year); 4 QAHC; 5 insurance (policyholders' share at basic rate, FA89 s88); 6 members' club/voluntary association; 7 property management company; 8 charity or owned by a charity; 9 REIT C residual; 10 REIT C tax-exempt; 11 non-resident |
| 5 | NI trading activity | tick | Leave blank: no NI rate is in force. Schema: boxes 5–8 only if box 35 ≥ 01-04-2050 |
| 6 | SME | tick | NI; leave blank |
| 7 | NI employer | tick | NI; leave blank |
| 8 | Special circumstances | tick | NI; leave blank |

**About this return**

| Box | Label | Type | Notes |
|---|---|---|---|
| 30 | from DD MM YYYY | date | Period ≤ 12 months; cannot start before 1 Apr 2015 |
| 35 | to DD MM YYYY | date | |
| 40 | A repayment is due for this return period | tick | |
| 45 | Claim or relief affecting an earlier period | tick | |
| 50 | Making more than one return for this company now | tick | |
| 55 | This return contains estimated figures | tick | |
| 60 | Company part of a group that is not small | tick | |
| 65 | Notice of disclosable avoidance schemes | tick | If ticked, box 140 is required (new return) |
| 70 | Transfer pricing: Compensating adjustment claimed | tick | 70 and 75 are mutually exclusive |
| 75 | Company qualifies for SME exemption | tick | |
| 80 | I attach accounts and computations for the period to which this return relates | tick | Schema splits this into 80A (accounts) and 80B (computations) |
| 85 | I attach accounts and computations for a different period | tick | 85A / 85B |
| 90 | If you're not attaching the accounts and computations, explain why | text | 90A / 90B |

**Supplementary pages enclosed** (ticks; each makes the page mandatory on a new return)

| Box | Page |
|---|---|
| 95 | Loans and arrangements to participators by close companies – CT600A |
| 100 | Controlled foreign companies, foreign permanent establishment exemptions, hybrid and other mismatches – CT600B |
| 105 | Group and consortium – CT600C |
| 110 | Insurance – CT600D |
| 115 | Charities and Community Amateur Sports Clubs (CASCs) – CT600E |
| 120 | Tonnage tax – CT600F |
| 125 | Northern Ireland – CT600G (no PDF published; dormant) |
| 130 | Cross-border royalties – CT600H |
| 135 | Supplementary charge in respect of ring fence trades – CT600I |
| 140 | Disclosure of Tax Avoidance Schemes – CT600J |
| 141 | Restitution tax – CT600K |
| 142 | Research and Development – CT600L |
| 143 | Freeports and Investment Zones – CT600M |
| 144 | Residential Property Developer Tax (RPDT) – CT600N |
| 96 | Creative industries – CT600P (from the 2025 form) |

**Tax calculation: turnover and income**

| Box | Label | Type | Calculation / notes |
|---|---|---|---|
| 145 | Total turnover from trade | £ (non-negative) | Not for investment companies or unit trusts |
| 150 | Banks, building societies, insurance companies and other financial concerns – no recognised turnover | tick | |
| 155 | Trading profits | £ | Includes Patent Box deduction and partnership shares. Losses go to 780/790 |
| 160 | Trading losses brought forward set against trading profits | £ | ≤ 155. Subject to the loss-restriction deductions allowance |
| 165 | Net trading profits – box 155 minus box 160 | £ | Rule 9151 |
| 170 | Bank, building society or other interest, and profits from non-trading loan relationships | £ | Excludes restitution interest (CT600K). Deficits go to 795 |
| 172 | Figure in 170 is net of carrying back a deficit from a later period | tick | |
| 175 | Annual payments not otherwise charged to CT and from which IT has not been deducted | £ | |
| 180 | Non-exempt dividends or distributions from non-UK resident companies | £ | |
| 185 | Income from which Income Tax has been deducted | £ | Gross; excludes amounts in 170 |
| 190 | Income from a property business | £ | NRL tax withheld goes in 515 |
| 195 | Non-trading gains on intangible fixed assets | £ | |
| 200 | Tonnage tax profits | £ | = F70 (rule 9155) |
| 205 | Income not falling under any other heading | £ | |
| 210 | Gross chargeable gains | £ | |
| 215 | Allowable losses including losses brought forward | £ | ≤ 210 |
| 220 | Net chargeable gains – box 210 minus box 215 | £ (1..1) | |

**Profits before deductions and reliefs**

| Box | Label | Type | Calculation / notes |
|---|---|---|---|
| 225 | Losses brought forward against certain investment income | £ | ≤ sum(170…205, 220) |
| 230 | Non-trade deficits on loan relationships and derivative contracts brought forward set against non-trading profits | £ | ≤ sum(170…205, 220) − 225 |
| 235 | Profits before other deductions and reliefs | £ | = 165+170+175+180+185+190+195+200+205+220 − (225+230) (rule 9332) |

**Deductions and reliefs.** Each box is capped at 235 minus the boxes before it (rules 9166–9178).

| Box | Label | Type | Notes |
|---|---|---|---|
| 240 | Losses on unquoted shares | £ | CTA10 s68 |
| 245 | Management expenses | £ | |
| 250 | UK property business losses for this or previous accounting period | £ | |
| 255 | Capital allowances for the purposes of management of the business | £ | Investment companies |
| 260 | Non-trade deficits for this accounting period from loan relationships and derivative contracts | £ | |
| 263 | Carried forward non-trade deficits from loan relationships and derivative contracts | £ | Post-1-Apr-2017 deficits against total profits |
| 265 | Non-trading losses on intangible fixed assets | £ | CTA09 s753 |
| 275 | Total trading losses of this or a later accounting period | £ | CTA10 s37. If 280 is not ticked, 275 ≤ 780 (rule 9175) |
| 280 | Amounts carried back from later accounting periods are included in box 275 | tick | |
| 285 | Trading losses carried forward and claimed against total profits | £ | CTA10 s45A (post-2017 losses) |
| 290 | Non-trade capital allowances | £ | CAA01 s260(3) |
| 295 | Total of deductions and reliefs – total of boxes 240 to 275, 285 and 290 | £ | = 240+245+250+255+260+263+265+275+285+290 (rule 9180); ≤ 235. ⚠ The HTML guide omits 285 ("240 to 275 and 290"); the form and schema include it |
| 300 | Profits before qualifying donations and group relief – box 235 minus box 295 | £ | Rule 9333 |
| 305 | Qualifying donations | £ | ≤ 300 |
| 310 | Group relief | £ | = C10. ≤ 300 − 305. Only if box 105 ticked (or amended return) |
| 312 | Group relief for carried forward losses | £ | = C130. ≤ 300 − 305 − 310 |
| 315 | Profits chargeable to Corporation Tax – box 300 minus boxes 305, 310 and 312 | £ (1..1) | Rule 9335. Also 315 = sum of 335+350+365+385+400+415 (rule 9186). ⚠ The guide text omits 312 |
| 320 | Ring fence profits included | £ | ≤ 315; production ring fence only (not contractor ring fence) |
| 325 | Northern Ireland profits included | £ | Leave blank |

**Tax calculation**

| Box | Label | Type | Notes |
|---|---|---|---|
| 326 | Number of associated companies in this period | count | Excludes the company itself. Use either 326, or 327 + 328 |
| 327 | Number of associated companies in the first financial year | count | For periods straddling a financial year where the limits or counts differ; not for quarterly instalment payers |
| 328 | Number of associated companies in the second financial year | count | |
| 329 | Chargeable at the small profits rate or entitled to marginal relief | tick | Not allowed for company types 1, 2, 3, 9, 10, 11 (rules 9398–9874) |
| 330 | Financial year (yyyy) – FY1 | gYear | = financial year of the box 30 date |
| 335 / 340 / 345 | Amount of profit / Rate of tax % / Tax (FY1, row 1) | £ / decimal / £p | 345 = 335 × 340 (rule 9204). Schema: FY1 "Details" repeats 1..3 (rows 335/340/345, 350/355/360, 365/370/375) |
| 350 / 355 / 360 | FY1, row 2 | £ / % / £p | |
| 365 / 370 / 375 | FY1, row 3 | £ / % / £p | |
| 380 | Financial year – FY2 | gYear | = 330 + 1 |
| 385 / 390 / 395 | FY2, row 1 | £ / % / £p | |
| 400 / 405 / 410 | FY2, row 2 | £ / % / £p | |
| 415 / 420 / 425 | FY2, row 3 | £ / % / £p | |
| 430 | Corporation Tax – total of boxes 345, 360, 375, 395, 410 and 425 | £p | |
| 435 | Marginal relief | £p (non-zero) | < 430. Requires 329 (for periods ending ≥ 1 Apr 2023) |
| 440 | Corporation Tax chargeable – box 430 minus box 435 | £p (1..1) | |

**Reliefs and deductions in terms of tax**

| Box | Label | Type | Notes |
|---|---|---|---|
| 445 | Community Investment Tax Relief | £p | ≤ 440 |
| 450 | Double Taxation Relief | £p | ≤ 440 − 445. Includes F45 |
| 455 | Box 450 includes an underlying rate relief claim | tick | |
| 460 | Box 450 includes an amount carried back from a later period | tick | |
| 465 | Advance Corporation Tax | £p | ≤ 440 − 445 − 450 |
| 470 | Total reliefs and deduction in terms of tax – total of boxes 445, 450 and 465 | £p | Rule 9247. ⚠ The guide says "445, 465 and 480", which is a typo |

**Coronavirus support schemes and energy levies**

| Box | Label | Type | Notes |
|---|---|---|---|
| 471 | Coronavirus Job Retention Scheme (CJRS) received | £p | Only for periods ending ≤ 30 Sep 2021 |
| 472 | CJRS entitlement | £p | ≤ 471 |
| 473 | CJRS overpayment already assessed or voluntarily disclosed | £p | |
| 474 | Other coronavirus overpayments | £p | |
| 986 | Energy (Oil and Gas) Profits Levy (EOGPL) amounts liable | £ | |
| 987 | Electricity Generator Levy (EGL) exceptional generation receipts | £ | |

**Calculation of tax outstanding or overpaid**

| Box | Label | Type | Notes |
|---|---|---|---|
| 475 | Net Corporation Tax liability – box 440 minus box 470 | £p | Required if 440 > 0 |
| 480 | Tax payable on loans and arrangements to participators | £p | = A80. Requires box 95 (new return) |
| 485 | You completed box A70 in CT600A | tick | Requires 480 and A70 |
| 490 | Controlled Foreign Companies (CFC) tax payable | £p | = B30 |
| 495 | Bank levy payable | £p | |
| 496 | Bank surcharge payable | £p | |
| 497 | Residential Property Developer Tax (RPDT) payable | £p | = N285 (rule 9433) |
| 500 | CFC tax, bank levy, bank surcharge and RPDT payable – total of boxes 490, 495, 496 and 497 | £p | |
| 501 | EOGPL payable | £p | |
| 502 | EGL payable | £p | |
| 505 | Supplementary charge (ring fence trades) payable | £p | = I70 |
| 510 | Tax chargeable – total of boxes 475, 480, 500, 501, 502 and 505 | £p | Rule 9339 |
| 515 | Income Tax deducted from gross income included in profits | £p | Excludes CIS deductions |
| 520 | Income Tax repayable to the company | £p | = 515 − 510 if positive |
| 525 | Self-assessment of tax payable before restitution tax and coronavirus support scheme overpayments – box 510 minus box 515 | £p (1..1) | Floor 0 |
| 526 | Coronavirus support schemes overpayment now due – total of boxes 471 and 474 minus boxes 472 and 473 | £p | |
| 527 | Restitution tax | £p | = K35 |
| 528 | Self-assessment of tax payable – total of boxes 525, 526 and 527 | £p | |

**Tax reconciliation**

| Box | Label | Type | Notes |
|---|---|---|---|
| 530 | Research and Development credit | £p | = L210 (rule 9386). Only if 142 ticked |
| 535 | (Not currently used) | £p | Leave blank |
| 540 | Creatives tax credit | £p | 2026 guide: = P325. 2024/25 guide: total creative tax credits claimed before set-off |
| 541 | AVEC and VGEC | £p | 2026 guide: = P245 |
| 545 | Total of R&D credit, creatives tax credit and AVEC/VGEC – total box 530 to 541 | £p | = 530+535+540+541 |
| 550 | Land remediation tax credit | £p | |
| 555 | Life assurance company tax credit | £p | ≤ 525 |
| 560 | Total land remediation and life assurance company tax credit – total box 550 and 555 | £p | |
| 565 | Capital allowances first-year tax credit | £p | Repealed for expenditure from 1 Apr 2020 |
| 570 | Surplus R&D credits and creatives tax credit payable – box 545 minus box 525 | £p | Floor 0 |
| 575 | Land remediation or life assurance company tax credit payable – (545+560) − (525+570) | £p | Floor 0; ≤ 560 |
| 580 | Capital allowances first-year tax credit payable – (545+560+565) − (525+570+575) | £p | Floor 0; ≤ 565 |
| 585 | Ring fence Corporation Tax included | £p | = I80; ≤ 525 |
| 586 | NI Corporation Tax included | £p | Leave blank |
| 590 | Ring fence supplementary charge included | £p | = I85; ≤ 505 |
| 595 | Tax already paid (and not already repaid) | £p | |
| 600 | Tax outstanding – box 525 minus boxes 545, 560, 565 and 595 | £p | Omit if negative (rule 9276). Note: uses 525, not 528 |
| 605 | Tax overpaid including surplus or payable credits – (545+560+565+595) − 525 | £p | Omit if negative |
| 610 | Group tax refunds surrendered to this company | £p | CTA10 s963 / QIP regulation 9 |
| 614 | AVEC and VGEC surrendered to this company | £p | CTA09 Pt 14A Ch 3 |
| 615 | R&D expenditure credits surrendered to this company | £p | CTA09 Pt 3 Ch 6A |

**Exporter information** (optional; shared with the Department for Business and Trade)

| Box | Label | Type |
|---|---|---|
| 616 | Yes – goods | tick |
| 617 | Yes – services | tick |
| 618 | No – neither | tick |

**Indicators and information**

| Box | Label | Type | Notes |
|---|---|---|---|
| 620 | Franked investment income / Exempt ABGH distributions | £ | |
| 625 | Number of 51% group companies | count | Only for periods ending ≤ 31 Mar 2023. Includes the company itself |
| 630 | Should have made instalment payments as a large company | tick | For periods ending ≥ 1 Apr 2023, box 326 must be completed |
| 631 | Should have made instalment payments as a very large company | tick | Mutually exclusive with 630 |
| 635 | Within a group payments arrangement for the period | tick | |
| 640 | Has written down or sold intangible assets | tick | |
| 645 | Has made cross-border royalty payments | tick | See CT600H |
| 647 | Eat Out to Help Out Scheme: reimbursed discounts included as taxable income | £ | |

**R&D and creatives enhanced expenditure**

| Box | Label | Type | Notes |
|---|---|---|---|
| 650 | R&D claim made by an SME (incl. SME subcontractor to a large company) [2025 wording adds "and/or for all creatives claims"] | tick | Mutually exclusive with 655 |
| 653 | Claim made by an R&D intensive SME | tick | Requires 650; only for periods ending after 31 Mar 2023 |
| 655 | Claim made by a large company | tick | |
| 656 | R&D claim notification form has been submitted | tick | |
| 657 | R&D additional information form has been submitted | tick | Requires 650 or 655 |
| 658 | Creatives additional information form has been submitted | tick | |
| 659 | R&D expenditure qualifying for SME/R&D intensive SME relief | £ | Requires 650. For periods starting ≥ 1 Apr 2024 it also requires 653. = L166 |
| 660 | R&D enhanced expenditure | £ | Qualifying expenditure plus additional deduction. For periods starting ≥ 1 Apr 2024 it requires 653 (ERIS only) |
| 663 | Creatives core expenditure | £ | = P310 (2026); requires box 96 |
| 665 | Creatives additional deduction | £ | = P315 (2026); requires box 96 |
| 670 | R&D enhanced expenditure and creatives additional deduction – total box 660 and box 665 | £ | |
| 675 | R&D enhanced expenditure of an SME on work subcontracted to it by a large company | £ | Not for periods starting ≥ 1 Apr 2024 |
| 680 | Vaccine research expenditure | £ | Large-company 40% additional deduction (historic) |
| 685 | Land remediation: total enhanced expenditure | £ | 150% of qualifying expenditure |

**Capital allowances included in trading profits/losses.** Pairs are "allowance / balancing charge (or disposal value)"; the schema type is `ChargeAndAllowance`.

| Boxes | Label |
|---|---|
| 688 / 689 | Full expensing |
| 690 | Annual investment allowance |
| 691 / 692 | Machinery and plant – super-deduction |
| 693 / 694 | Machinery and plant – special rate allowance (50% FYA) |
| (696) | 40% first-year allowance — schema only |
| 695 / 700 | Machinery and plant – special rate pool |
| 705 / 710 | Machinery and plant – main pool |
| 711 | Structures and buildings |
| 715 / 720 | Business premises renovation |
| 725 / 730 | Other allowances and charges |
| 713 / 714 | Electric vehicle charge-points (disposal value). 714 unused for periods beginning ≥ 1 Apr 2025; 713 unused ≥ 1 Apr 2026 |
| 721 / 722 | Enterprise zones. Unused for periods beginning ≥ 1 Apr 2024 |
| 723 / 724 | Zero-emission goods vehicles. Unused ≥ 1 Apr 2025 |
| 726 / 727 | Zero-emission cars. 727 unused ≥ 1 Apr 2025; 726 unused ≥ 1 Apr 2026 |

**Capital allowances not included in trading profits/losses**

| Boxes | Label |
|---|---|
| 735 | Annual investment allowance |
| 736 | Structures and buildings |
| 733 / 734 | Full expensing |
| 740 / 745 | Business premises renovation |
| 741 / 742 | Machinery and plant – super-deduction |
| 743 / 744 | Machinery and plant – special rate allowance |
| (739) | 40% FYA — schema only |
| 750 / 755 | Other allowances and charges |
| 737 / 738 | Electric vehicle charge-points |
| 746 / 747 | Enterprise zones |
| 748 / 749 | Zero-emission goods vehicles |
| 751 / 752 | Zero-emission cars |

Rule 9288: 690 + 735 ≤ the apportioned AIA limit.

**Qualifying expenditure (all £)**

| Box | Label |
|---|---|
| 760 | Machinery and plant on which first year allowance is claimed. Includes 765, 772, 773 and full expensing |
| 765 | Designated environmentally friendly machinery and plant |
| 770 | Machinery and plant on long-life assets and integral features |
| 771 | Structures and buildings |
| 772 | Machinery and plant – super-deduction |
| 773 | Machinery and plant – special rate allowance |
| 775 | Other machinery and plant |

**Losses, deficits and excess amounts arising.** Pairs are "amount / maximum available for surrender as group relief"; the schema type is `ArisingAndMaximum`, all £.

| Boxes | Label |
|---|---|
| 780 / 785 | Losses of trades carried on wholly or partly in the UK (785 = CTA10 s100 amount) |
| 790 | Losses of trades carried on wholly outside the UK |
| 795 / 800 | Non-trade deficits on loan relationships and derivative contracts |
| 805 / 810 | UK property business losses |
| 815 | Overseas property business losses |
| 820 | Losses from miscellaneous transactions |
| 825 | Capital losses |
| 830 / 835 | Non-trading losses on intangible fixed assets |
| 840 | Excess non-trade capital allowances (max for surrender) |
| 845 | Qualifying donations (max for surrender) |
| 850 / 855 | Management expenses |

**Northern Ireland information** (leave blank)

| Box | Label |
|---|---|
| 856 | Group relief claimed which relates to NI trading losses used against rest of UK/mainstream profits |
| 857 | Group relief claimed which relates to NI trading losses used against NI trading profits |
| 858 | Group relief claimed which relates to rest of UK/mainstream losses used against NI trading profits |

**Overpayments and repayments**

| Box | Label | Type | Notes |
|---|---|---|---|
| 860 | Do not repay sums of £… or less | £ | |
| 865 | Repayment of Corporation Tax | £p | Guide: = 605 − (570+575+580) |
| 870 | Repayment of Income Tax | £p | = 520 |
| 875 | Payable R&D tax credit | £p | = L180 (rule 9394) |
| 880 | Payable R&D expenditure credit | £p | = L125 (rule 9396) |
| 885 | Payable creatives tax credit | £p | = P330 if > 0 |
| 886 | Payable AVEC and VGEC | £p | = P190 if > 0 |
| 890 | Payable land remediation or life assurance company tax credit | £p | = 575 |
| 895 | Payable capital allowances first-year tax credit | £p | = 580 |
| 900 | Surrender of tax refund within group: amount to be surrendered | £p | |
| 905 | The joint Notice is attached | tick | |
| 910 | The joint Notice will follow | tick | |
| 915 | Please stop repayment of the following amount until we send you the Notice | £p | ≤ 900 |

**Bank details**

| Box | Label | Type |
|---|---|---|
| 920 | Name of bank or building society | text |
| 925 | Branch sort code | text |
| 930 | Account number | text |
| 935 | Name of account | text |
| 940 | Building society reference | text |

**Payments to a person other than the company**

| Box | Label | Type | Notes |
|---|---|---|---|
| 943 | There is an R&D payable credit and one of the conditions listed in the CT600 Guide is applicable | tick | Only if 875 or 880 is completed (periods starting ≥ 1 Apr 2024). Conditions: nominee is connected; exceptional circumstances; claim first made before 1 Apr 2024; assignment before 22 Nov 2023 (CIRD81805) |
| 945 | I, as (status) | text | |
| 950 | of (company name) | text | |
| 955 | authorise (name) | text | |
| 960 | of address | address | |
| 965 | Nominee reference | text | |
| 970 | Name | text | |

**Declaration**

| Box | Label | Type |
|---|---|---|
| 975 | Name | text |
| 980 | Date | date |
| 985 | Status | text |

### Corporation Tax rate mechanics (boxes 326–440)

Source: https://www.gov.uk/government/publications/rates-and-allowances-corporation-tax

- **Rates for FY2023 to FY2026** (every year from 1 April 2023):
  - Main rate 25%.
  - Small profits rate 19%.
  - Lower limit £50,000 and upper limit £250,000. Both are divided by (1 + associated companies) and time-apportioned for periods under 12 months.
  - Marginal relief fraction 3/200.
  - Ring fence: small 19%, main 30%.
  - Unit trusts/OEICs: 20%.
- **Marginal relief (box 435)** = 3/200 × (U − A) × N/A, where:
  - U is the adjusted upper limit;
  - A is augmented profits (box 315 plus exempt ABGH distributions from non-group companies);
  - N is taxable total profits (box 315).
  
  Rows 330–425 carry the profit at 25% and the tax. For periods that straddle 1 April, profits are split by days between FY1 (330) and FY2 (380). Rules 9197/9198 require the FY1 rows to total box 315 apportioned to FY1.

### Unverified / caveats (main return)

- The HTML guide conflicts with the form and schema for 295 (omits 285), 315 (omits 312) and 470 (says 480 instead of 450). The form and schema rules are internally consistent, so implement those.
- The 2024 and 2025 PDFs were obtained from web.archive.org copies of the HMRC asset URLs, because gov.uk now serves the latest file for old asset links. Checksums are in `downloads/MANIFEST.md`.
- Boxes 696/739 (40% FYA) are in schema v1.995 only. HMRC says online support arrives in April 2027.

---

# (b) Supplementary pages

## CT600A — Close company loans and arrangements to confer benefits on participators

- **Form versions**:
  - `downloads/CT600A_2015_v3_pre2026.pdf`: "CT600A (2015) Version 3 for accounting periods starting on or after 1 April 2015", HMRC 04/15. This was in force for 2024/2025 filings; recovered from the Wayback copy of the asset.
  - `downloads/CT600A.pdf`: "CT600A (2026) Version 3", HMRC 04/26.
  - Publication: https://www.gov.uk/government/publications/corporation-tax-close-company-loans-and-arrangements-to-confer-benefits-on-participators-ct600a-2015-version-3
  - Guidance: https://www.gov.uk/guidance/supplementary-pages-ct600a-2015-version-3-close-company-loans-and-arrangements-to-confer-benefits-on-participators (updated 2026-04-08).
- **2015 → 2026 changes** (wording only; no box added or removed):
  - A5, the Part 2 heading and the Part 3 heading now say return payments on s464A arrangements only count if made **before 30 October 2024**.
  - Column B of the A25/A50 tables is renamed "Amount repaid" (was "Amount repaid/return repayments made").
- **Who files**: a close company (CTA10 s439) that, in the period, either:
  - made a loan or advance to a participator or associate (CTA10 s455) that is not repaid, released or written off by the period end; or
  - conferred a benefit under tax-avoidance arrangements (CTA10 s464A) with no return payment by the period end.
  
  Tick CT600 box **95**.

### Box table

| Box | Label (form) | Type (schema) | Notes / calculation |
|---|---|---|---|
| A1 | Company name | text | |
| A2 | Tax reference | UTR | |
| A3 | Period covered… from DD MM YYYY | date | ≤ 12 months |
| A4 | to DD MM YYYY | date | |
| A5 | Put an 'X' if any/all loans made during the period have been repaid, released, or written off before the end of the period, or in the case of arrangements, return payments have been made before the end of the period [and before 30 October 2024] | Yes/No (1..1, `YesNoType`) | |
| A10 | **Part 1 – Outstanding loans and arrangements made** | repeating table, 1..999 rows (form shows 6) | |
| A10A | Name of participator or associate | text | |
| A10B | Amount of loan/benefit | £ non-zero | Net debit on the account for the period: debits less credits less any credit balance brought forward, excluding credits that repay earlier-period loans |
| A15 | Total | £ | = Σ A10B (rule 9401). Loans in the period not repaid by the period end, plus s464A benefits with no return payment, plus amounts deemed outstanding by s464C |
| A20 | Tax chargeable – box A15 multiplied by rate applicable | £p | = A15 × s455 rate (rule 9466). Rounded to the nearest penny, with half a penny rounded up. If the rate changes within the period, the value must lie between A15 × lowest rate and A15 × highest rate (rules 9467/9468) |
| A25 | **Part 2 – Relief for amounts repaid, released or written off within 9 months** [or return payments within 9 months and before 30 Oct 2024] | repeating table, 1..999 | Only allowed if Part 1 is completed (rule 9405) |
| A25A | Name of participator or associate | text | |
| A25B | Amount repaid [/return payments made] | £ | At least one of B or C > 0 |
| A25C | Amount released or written off | £ | |
| A25D | Date of repayment, release or write-off | date | Must be **after** box 35 and **before** (box 35 + 9 months + 1 day); not in the future (rules 9429/9406/9884). Give the date of the last repayment |
| A30 | Totals (column B) | £ | = Σ A25B |
| A35 | Totals (column C) | £ | = Σ A25C |
| A40 | Totals – total amount of boxes A30 and A35 | £ | |
| A45 | Relief due – box A40 multiplied by rate applicable | £p | = A40 × rate; ≤ A20 |
| A50 | **Part 3 – Relief due now for amounts repaid, released or written off later** [and return payments made later and before 30 Oct 2024] | repeating table, 1..999 | "Most companies will not need to complete" |
| A50A | Name of participator or associate | text | |
| A50B | Amount repaid [/return payments made] | £ | |
| A50C | Amount released or written off | £ | |
| A50D | Date of repayment, release or write-off | date | ≥ 9 months after box 35; not in the future |
| A55 | Totals (column B) | £ | = Σ A50B |
| A60 | Totals (column C) | £ | = Σ A50C |
| A65 | Totals – total of boxes A55 and A60 | £ | |
| A70 | Relief due – box A65 multiplied by rate applicable | £p | ≤ A20. If completed, tick CT600 box **485** (rule 9426) |
| A75 | Total of all loans and arrangements, for all periods, outstanding at the end of the return period | £ | Information only; includes earlier-period loans and s464C deemed amounts |
| A80 | Tax payable – box A20 minus total of boxes A45 and A70 | £p (1..1) | Floor 0 (rule 9427). **Copy to CT600 box 480** (rule 9428) |

### Rules and calculations (s455 / s464A / s458 / s464B / s464C)

- **Rate** (CTA10 s455(3): the "dividend upper rate" for the tax year in which the loan is made):
  - 25% for loans before 6 Apr 2016.
  - 32.5% for 6 Apr 2016 – 5 Apr 2022.
  - **33.75% for 6 Apr 2022 – 5 Apr 2026**.
  - **35.75% for loans made or benefits conferred on or after 6 Apr 2026**, following the Budget 2025 rise in the dividend upper rate. Sources: https://www.gov.uk/government/publications/income-tax-changes-to-tax-rates-for-property-savings-and-dividend-income and https://www.gov.uk/guidance/changes-and-issues-affecting-the-corporation-tax-online-service
  
  Schema v1.995 already encodes 0.25 / 0.325 / 0.3375 / 0.3575, switching on 2016-04-06, 2022-04-06 and 2026-04-06. HMRC's online service only adopts 35.75% on 6 Apr 2027, so returns filed earlier must be amended later. ⚠ The CT600A guidance page (updated April 2026) still says 33.75% is the latest rate.
- **Relief rate**: relief (A45/A70) is given at the rate that applied **when the loan was made**, not when it was repaid.
- **Timing of relief (s458)**:
  - Repayment, release or write-off after the period end but within 9 months → relief is effectively immediate (Part 2), so no s455 tax becomes due.
  - Repayment more than 9 months after the period end → relief is due only from the normal due date (9 months and 1 day) of the accounting period in which the repayment is made (s458(5)).
  - Part 3 is used only when that date has already passed at filing, for example a very late return filed at least 21 months after the period end.
  
  Source: CTM61610 https://www.gov.uk/hmrc-internal-manuals/company-taxation-manual/ctm61610
- **s464A/s464B** (benefits under arrangements): there is **no relief for return payments made on or after 30 Oct 2024**.
- **Bed and breakfasting (s464ZA)** — repayments are matched to new loans instead of old ones:
  - **30-day rule**: repayments of ≥ £5,000 matched against new loans of ≥ £5,000 made in a later accounting period within 30 days.
  - **Arrangements rule**: applies where the balance is ≥ £15,000 and arrangements exist for ≥ £5,000 of new loans.
  - Repayments by way of dividend or remuneration taxable on the participator are excluded (s464ZA(6)).
  
  Sources: CTM61630 / CTM61635.
- **Exclusions (s456)**:
  - Ordinary-course trade credit of ≤ 6 months.
  - Loans of ≤ £15,000 to full-time working directors or employees without a material interest (> 5%).
  - Loans to charitable trustees from 25 Nov 2015.
- **Participators and associates**: participator is defined in s454; associate in s448. Loans to partnerships and trusts are included from 20 Mar 2013 (CTM61510).
- **Payment**: s455 tax is due with mainstream CT (9 months and 1 day after the period end). It is carried into the CT600 through box 480, then into 510 and on to 525/528.

### Worked example

Period 1 Jan 2025 – 31 Dec 2025. The director's loan account is overdrawn by £40,000 at 31 Dec 2025, from advances drawn during 2025. £15,000 is repaid on 30 Jun 2026 (within 9 months). £5,000 is written off on 1 Nov 2026 (more than 9 months). The return is filed on 15 Aug 2026.

| Box | Value |
|---|---|
| A10 row 1 | "J Smith", £40,000 |
| A15 | £40,000 |
| A20 | £40,000 × 33.75% = £13,500.00 |
| A25 row 1 | "J Smith", repaid £15,000, date 30/06/2026 |
| A30 / A40 | £15,000 |
| A45 | £15,000 × 33.75% = £5,062.50 |
| A70 | Blank: the write-off relief falls due on 1 Oct 2027 (the due date for the period ending 31 Dec 2026) and is claimed separately |
| A75 | £25,000 |
| A80 | £13,500 − £5,062.50 = **£8,437.50** → CT600 box **480**; box 95 ticked |

If the advances had been made after 5 Apr 2026, the rate would be 35.75%. A20 would then be £14,300.00 and A45 £5,362.50.

---

## CT600B — Controlled foreign companies and foreign permanent establishment exemptions, hybrid and other mismatches

- **Form version(s)**
  - Printed version string: `CT600B (2022) Version 3 for accounting periods starting on or after 1 April 2015`; footer `CT600B(2022) Version 3 … HMRC 04/22`. 3 pages (company information, CFC/FPE table, hybrids).
  - Local file: `downloads/CT600B_2022.pdf` (text: `text/CT600B_2022.txt`).
  - Publication: https://www.gov.uk/government/publications/corporation-tax-controlled-foreign-companies-and-foreign-permanent-establishment-exemptions-ct600b-2015-version-3 (asset https://assets.publishing.service.gov.uk/media/623de3b6e90e075f0e144710/CT600B_2022.pdf; page last changed 2025-04-01, form itself unchanged since the "updated the form and guidance for 2022" entry of 2022-04-01).
  - Guidance: https://www.gov.uk/guidance/supplementary-pages-ct600b-controlled-foreign-companies-and-foreign-permanent-establishment-exemptions-hybrid-and-other-mismatches (first published 2022-09-29, B40–B85 guidance added 2022-10-21, updated 2024-01-02).
  - Schema: HMRC CT-2014 v1.995 (`[CTB]`, element `ControlledForeignCompanies`, N096); identical in live v1.994 (no CTB changes in the 1.994→1.995 diff).
  - Applicability: any CT600 v3 return (APs starting on/after 1 April 2015). The 2022 edition added the hybrid section B40–B85; HMRC says B40–B85 "should be completed for any return submissions made for the first time from April 2022 … not required … if you are submitting an amended return" (guidance). Schema has no date gate on B40–B85.

- **Purpose / who must file**
  - A UK-resident company that held a **relevant interest of ≥25%** in a CFC at any time in the AP, where the CFC's AP ended within or at the same time as the company's AP (guidance; TIOPA 2010 s371BD "chargeable company" — ≥25% of chargeable profits apportioned to it plus connected/associated persons: https://www.legislation.gov.uk/ukpga/2010/8/section/371BD).
  - Do **not** list a CFC that meets the Tax Exemption (Ch 14), Excluded Territories Exemption (Ch 11) or Low Profit Margin Exemption (Ch 13) (guidance). CFCs relieved by gateway Ch 3–8, Ch 9 in full, Exempt Period (Ch 10) or Low Profits (Ch 12) are listed with an entry in column C only.
  - A company whose **first** period of a foreign permanent establishments exemption election (CTA 2009 Part 2 Ch 3A, s18A–18S) falls in this AP ticks B35 (INTM281010, INTM281020).
  - A company that is a hybrid entity, transacts with hybrid entities in its control group, has a Part 6A Ch 3/6/8 mismatch, has any Part 6A counteraction, a s259LA deduction, or made/consented to a DII surplus allocation claim under s259ZMB (TIOPA 2010 Part 6A; INTM550000).

- **Box table**

| Box | Label (verbatim from form) | Type | Notes / calculation |
|---|---|---|---|
| B1 | Company name | text | Paper only. Not in schema — XML takes CT600 box 1. |
| B2 | Tax reference | text | Paper only (10-digit UTR). Not in schema — CT600 box 3. |
| B3 | Period covered by this supplementary page (cannot exceed 12 months) — from | date | Paper only; = CT600 box 30. |
| B4 | … to | date | Paper only; = CT600 box 35. |
| B5 | Controlled foreign companies and foreign permanent establishment exemptions (table) | repeating table 0..∞ | Paper has 12 rows; schema `CompanyInformation` 0..∞ (unbounded). Each row = name + territory + **either** column C **or** columns D–J (XSD `xsd:choice`). |
| B5A | A — Name of CFC | text | 1..1 per row; `CTexcludedCharsStringType`, 2–56 chars. |
| B5B | B — Territory of Residence | text | 1..1; 2–56 chars. Schema desc "Territory of residence for S749 purposes" (stale ICTA ref); guidance: territory under TIOPA 2010 Part 9A Ch 20. |
| B5C | C — Type of exemption due (if any) | text | Choice branch 1; 2–56 chars. Enter "gateway chapter 3", chapter 4–8, "chapter 9", "Exempt Period Exemption" or "Low Profits Exemption" when **all** profits excluded. Mutually exclusive with D–J. |
| B5D | D — Percentage of apportionable profits and creditable tax | % | Choice branch 2, 1..1. Pattern `[0-9]{1,3}\.[0-9]{2}`, >0, ≤100.00 (always 2 dp). = P% of s371BC(3). Do not reduce for Ch 9 partial exemption. |
| B5E | E — Chargeable profits | amount £ (whole pounds) | 1..1; non-zero (`CT_CTnonZeroWholePoundStructure`). CFC's chargeable profits (s371BA) **before** any Ch 9 claim. |
| B5F | F — Tax on chargeable profits | amount £p | 1..1; ≥0. = appropriate rate × P% × E. |
| B5G | G — Creditable tax | amount £p | 0..1; >0 if present. = Q% × CFC creditable tax (Ch 16). |
| B5H | H — Reliefs in terms of tax | amount £p | 0..1; >0. Guidance heading adds "(exemption claimed under Chapter 9)": tax on profits excluded by a Ch 9 claim. |
| B5I | I — ACT as restricted | amount £p | 0..1; >0. Unrelieved surplus ACT (guidance cites s32 FA 1998). |
| B5J | J — CFC charge due | amount £p | 1..1; ≥0. = F − (G + H + I) (rule 9455). |
| B10 | Total (column F) | amount £p | 0..1; >0. Σ B5F. Schema desc "Total tax on chargeable profits". |
| B15 | Total (column G) | amount £p | 0..1; >0. Σ B5G. |
| B20 | Total (column H) | amount £p | 0..1; >0. Σ B5H. |
| B25 | Total (column I) | amount £p | 0..1; >0. Σ B5I. |
| B30 | Total (column J) — "Enter this amount in box 490 on form CT600" | amount £p | 0..1; ≥0. Σ B5J → CT600 box 490. Schema element `TotalCFCtaxChargeble` (sic). |
| B35 | Put an 'X' in this box if this is the first period where an election for foreign permanent establishment exemption applies | tick (X) | 0..1 `CT_YesType`. |
| — | Hybrid and other mismatches — "Put an 'X' in the relevant boxes, if:" | group | Schema `HybridAndOtherMismatches` 0..1; if present must be non-empty (9622). |
| B40 | the company is a hybrid entity | tick (X) | s259BE TIOPA 2010; INTM550580. |
| B45 | there were any transactions with hybrid entities in the same control group as this company | tick (X) | Payments/quasi-payments to or from a hybrid entity in the same control group; INTM550610. |
| B50 | there were any hybrid or otherwise impermissible deduction/non-inclusion mismatches in connection with a financial instrument | tick (X) | Part 6A Ch 3 (s259CA/259CB); INTM551000. |
| B55 | there was an excessive permanent establishment (PE) deduction | tick (X) | Part 6A Ch 6 (s259FA); INTM554000. |
| B60 | there has been a multinational payee deduction/non-inclusion mismatch | tick (X) | Part 6A Ch 8 (s259HA/259HB); INTM556000. |
| B65 | there has been a counteraction under Part 6A Taxation (International and Other Provisions) Act 2010 (TIOPA 2010) | tick (X) | Any chapter of Part 6A affecting tax payable in the period. |
| B70 | Total counteraction | amount £ (whole pounds) | 0..1; required if B65 (9621). Exclude amounts deducted only because matched by dual inclusion income. |
| B75 | Total section 259LA TIOPA 2010 deduction | amount £ (whole pounds) | Deduction for ordinary income arising outside the permitted period (INTM561130). |
| B80 | Total claim for allocation of dual inclusion income (DII) surplus that the company has made | amount £ (whole pounds) | s259ZMB allocation made by this company to another group company (INTM561200). |
| B85 | Total claim of DII surplus that the company has consented to | amount £ (whole pounds) | s259ZMB allocation from another group company, consented to. |

Form/schema disagreements: B1–B4 absent from schema (inherited from CT600 boxes 1/3/30/35); paper table fixed at 12 rows vs unbounded XML; B5 C vs D–J exclusivity is only in the XSD (`xsd:choice`), not printed; B10–B25 must be >0 when present but B30/B5F/B5J may be 0.00.

- **Calculations and rules**
  - Per CFC row (schema 9455): `J = F − (G + H + I)`. Because J is non-negative, G + H + I ≤ F.
  - Totals: `B10 = ΣF` (9456), `B15 = ΣG` (9457), `B20 = ΣH` (9458), `B25 = ΣI` (9459), `B30 = ΣJ` (9463). Equivalently `B30 = B10 − B15 − B20 − B25`.
  - **CFC charge (TIOPA 2010 Part 9A, s371BC step 5)**: charge on each chargeable company = CT at the *appropriate rate* on P% of the CFC's chargeable profits, **less** Q% of the CFC's creditable tax, charged "as if it were an amount of corporation tax" for the chargeable company's AP in which the CFC's AP ends (https://www.legislation.gov.uk/ukpga/2010/8/section/371BC; INTM194400).
    - Appropriate rate (s371BC(3)–(4)): rate applicable to the chargeable company's profits of that AP (average if >1 rate), assuming main rate not the NI rate. INTM194400 states "the main corporation tax rate … or an average". For FY2023+ this is 25% main rate; for APs straddling 1 April 2023 use the time-weighted average (see caveats re small profits rate).
    - Model: `F = round2(rate × P% × E)`; `G = Q% × creditable_tax` (Q% normally = P%, the same apportionment).
  - Steps (s371BC(1)): (1) relevant persons with relevant interests (Ch 15); (2) creditable tax (Ch 16); (3) apportion chargeable profits and creditable tax (Ch 17: by ordinary shareholdings, else just and reasonable — INTM233200/233300); (4) chargeable companies = UK-resident with ≥25% including connected/associated (s371BD; INTM194500), excluding offshore fund managers where charge ≤ £500,000 (s371BE); (5) charge.
  - Gateway (s371BB): Ch 3 decides whether any of Ch 4–8 apply; profits pass only through applicable chapters — Ch 4 UK activities, Ch 5 non-trading finance profits, Ch 6 trading finance profits, Ch 7 captive insurance, Ch 8 solo consolidation (s371AA(5)).
  - Ch 9 qualifying loan relationship exemption (claim): 75% exemption (s371ID; INTM218600) or full exemption for qualifying resources (s371IB; INTM218700). Tax on the exempted amount goes in column H, not deducted from E.
  - Entity exemptions (Ch 10–14; INTM224000): exempt period (s371JB, 12-month grace), excluded territories (Ch 11), low profits (s371LB: accounting profits or assumed TTP ≤ £50,000; or ≤ £500,000 with non-trading income ≤ £50,000; pro-rata for short APs), low profit margin (s371MB: accounting profits ≤ 10% of relevant operating expenditure), tax exemption (s371NB: local tax ≥ 75% of corresponding UK tax).
  - No reliefs (losses, surplus management expenses, etc.) may be set against the CFC charge for CFC APs beginning on/after 8 July 2015 (s371UD(2) repealed by F(No 2)A 2015 s36; INTM245400).
  - **Foreign PE exemption (CTA 2009 s18A)**: irrevocable election, must be received before the start of the first AP it covers, applies to all PEs; profits and losses attributable to foreign PEs are left out of the CT computation via "exemption adjustments" (INTM281010, INTM281020). No CT600B amount; effect flows into the underlying CT600 income boxes (e.g. 155). No DTR on exempt PE profits (INTM281060). Transitional streaming of prior PE losses, s18J–18N (INTM284040).
  - **Hybrids (TIOPA 2010 Part 6A)**: counteractions deny deductions (primary) or deem income (secondary) for deduction/non-inclusion and double-deduction mismatches in Ch 3–11 (INTM550000). Counteracted amounts are adjustments inside the tax computation (increase profits in the relevant CT600 income/deduction boxes); B70–B85 are disclosure totals only and feed no CT600 box.

- **Main-return linkage**
  - CT600 **box 100** tick (`ReturnInfoSummary/SupplementaryPages/CT600B`). N096 present ⇒ box 100 = yes (9306); box 100 + new return ⇒ N096 present (9121).
  - **B30 → CT600 box 490** "CFC tax payable" (guide; rule 9465). Box 490 must not be present on a new return unless box 100 ticked (9353).
  - Box 490 flows into **box 500** = 490 + 495 + 496 + 497 (rule 9434) → **box 510** = 475 + 480 + 500 + 501 + 502 + 505 (guide). Box 500 required if 490 > 0 (9351).
  - The CFC charge is **not** in box 440/475 and is not reduced by box 450 DTR ("Exclude any amount entered in box 500", guide box 450).
  - FPE exemption and hybrid counteractions change computation figures (e.g. boxes 155/170/235) but no box is directly fed.

- **Key schema validation rules**
  - 9460: CT600B present ⇒ at least one of B5 row, B35, or hybrid group.
  - 9450: B10 required if ΣB5F > 0; 9451/9452/9453: B15/B20/B25 required if any B5G/B5H/B5I present; 9454: B30 required if any D–J row exists.
  - 9455 row identity; 9456–9459, 9463 column totals; 9465: B30 present ⇒ box 490 present and = B30.
  - 9621: B65 ⇒ B70; 9622: hybrid group not empty.
  - XSD: B5D pattern `[0-9]{1,3}\.[0-9]{2}`, 0 < D ≤ 100.00; B5E non-zero whole pounds; B5G/H/I and B10–B25 > 0; name/territory/exemption 2–56 chars; C xor D–J.

- **Worked example** (AP 1 Jan–31 Dec 2025, appropriate rate 25%)

| Row | A | C | D | E | F | G | H | I | J |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Alpha Ltd (territory X) | — | 60.00 | 1,000,000 | 150,000.00 | 48,000.00 | — | — | 102,000.00 |
| 2 | Beta SA (territory Y) | Low Profits Exemption | — | — | — | — | — | — | — |

  - Row 1: F = 25% × 60% × £1,000,000 = £150,000.00; CFC paid £80,000 local tax, Q% = 60% ⇒ G = £48,000.00; J = 150,000.00 − 48,000.00 = £102,000.00.
  - B10 = 150,000.00; B15 = 48,000.00; B20/B25 omitted; B30 = 102,000.00 ⇒ box 490 = 102,000.00; box 500 = 102,000.00 (+495/496/497 if any); box 510 = 475 + 480 + 500 + …; box 100 ticked.
  - If a 75% Ch 9 claim covered £400,000 of E: E unchanged (1,000,000), H = 25% × 60% × 300,000 = £45,000.00, J = 150,000 − 48,000 − 45,000 = £57,000.00.

- **Unverified / caveats**
  - "Appropriate rate" after FY2023: statute says the rate "applicable to CC's profits" (s371BC(3)); INTM194400 (last updated 2016) says the main rate. Whether a company entitled to the 19% small profits rate uses 19% or 25% is not confirmed here — treat as a configurable rate defaulting to the main rate and flag to the user.
  - Column C content is free text (2–56 chars); HMRC publishes no code list. Suggested literal strings follow the guidance wording.
  - Column I (ACT as restricted) reference "section 32 of the Finance Act 1998" is quoted from guidance, not verified against legislation.
  - INTM pages cited: INTM190000, INTM194400, INTM194500, INTM218600, INTM224000, INTM233000, INTM245400, INTM281010, INTM281020, INTM550000 (URLs: https://www.gov.uk/hmrc-internal-manuals/international-manual/<id>).

---

## CT600C — Group and consortium relief

- **Form version**: `downloads/CT600C_2018.pdf`, "CT600C (2018) Version 3 for accounting periods starting on or after 1 April 2015", HMRC 04/18. This is still the current attachment and is used for the 2024, 2025 and 2026 filings.
  - Publication: https://www.gov.uk/government/publications/corporation-tax-group-and-consortium-relief-ct600c-2015-version-3
  - Guidance: https://www.gov.uk/guidance/supplementary-pages-ct600c-group-and-consortium-relief
- **Who files**: any company that claims or surrenders any of the following, and ticks CT600 box **105**:
  - group or consortium relief (CTA10 Part 5);
  - surplus contractor ring-fence lease payments (CTA10 s356NA(3)(b));
  - group relief for carried-forward losses (CTA10 Part 5A).
- **Consent**: unless a simplified arrangement is in force, each surrender needs a notice of consent. Part 2 or Part 4 can act as that notice. Copies of consent notices are attached as PDF attachments of type "Other" (rules 9510/9522).

### Box table

**Company information**

| Box | Label (form) | Type (schema) | Notes |
|---|---|---|---|
| C1 | Company name | text | |
| C2 | Tax reference | UTR | |
| C3 | Period covered… from | date | ≤ 12 months |
| C4 | to | date | |

**Part 1: Claims to group relief** (current-period losses; the group is *claimant*)

| Box | Label (form) | Type (schema) | Notes |
|---|---|---|---|
| C5 | Surrendering companies | repeating table, 1..∞ (form shows 7) | |
| C5A | Name of surrendering company | text (1..1) | |
| C5B | Accounting period of surrendering company* | period from–to (0..1) | Only if it differs from this return. ≤ 12 months; must overlap boxes 30–35 (rules 9502–9505) |
| C5C | Tax reference** | text (1..1) | 10-digit UTR, or CRN / other identifier |
| C5D | Amount claimed | £ non-zero | |
| C10 | Total | £ | = Σ C5D (rule 9507). **Enter in CT600 box 310** (rule 9506) |
| C15 | Claim involves losses of a trade carried on in the UK through a Permanent Establishment by a non-resident company | tick | |
| C20 | Claim involves losses of a non-resident company other than C15, or involves a non-resident link company | tick | Non-UK-PE losses are not allowable for APs from 27 Oct 2021 |
| (SC161) | Copies of notices of consent attached | tick (schema only) | Needs a PDF attachment |
| C25 | Claim authorisation – claim authorised (simplified arrangements) | tick | Claim authorisation section is required on a new return with a claim (rule 9518) |
| C30 | Name of authorised company | text | |
| C35 | Full name of person authorising | text | |
| C40 | Status | text | |

**Part 2: Amounts surrendered as group relief** (current-period amounts)

| Box | Label (form) | Type (schema) | Notes |
|---|---|---|---|
| C45 | Trading losses – total | £ | |
| C46 | Trading losses – Northern Ireland | £ | Leave blank. Only with box 5; ≤ C45 |
| C50 | Excess non-trade capital allowances over income from which they are primarily deductible | £ | |
| C55 | Non-trading deficit on loan relationships | £ | |
| C60 | Excess qualifying charitable donations over profits | £ | |
| C65 | Excess UK property business losses over profits | £ | |
| C70 | Excess of management expenses over profits | £ | |
| C75 | Non-trading deficits (losses) on intangible fixed assets | £ | |
| C80 | Total | £ | = C45+C50+C55+C60+C65+C70+C75 (rule 9511). Note C46 is a subset of C45 and is not added |
| C85 | Details of surrender | repeating table, 1..∞ (form shows 5) | |
| C85A | Name of claimant company | text | |
| C85B | Accounting period of claimant company* | period | |
| C85C | Tax reference** | text | |
| C85D | Amount surrendered | £ | |
| C90 | Total | £ | = Σ C85D |
| (SC150/151/152) | Consent options: simplified arrangement in force / CT600C notice of consent completed / copies attached | ticks (schema only) | |
| C95 | Company name | text | Must equal box 1 |
| C100 | Tax reference | UTR | Must equal box 3 |
| C105 | Accounting period start date | date | Must equal box 30 |
| C110 | Accounting period end date | date | Must equal box 35 |
| (SC156) | Certification ("I certify…") | tick | |
| C115 | Full name of person authorising | text | |
| C120 | Status | text | |

**Part 3: Claims to group relief for carried-forward losses**

| Box | Label (form) | Type (schema) | Notes |
|---|---|---|---|
| C125 | Surrendering companies | repeating table, 1..∞ (form shows 7) | |
| C125A | Name of surrendering company | text | |
| C125B | Accounting period of surrendering company | period | |
| C125C | Tax reference | text | |
| C125D | Amount claimed | £ | |
| C130 | Total | £ | = Σ C125D. **Enter in CT600 box 312** (rule 9550) |
| C135 | Claim involves losses of a trade carried on in the UK through a PE by a non-resident company | tick | |
| (SC172) | Copies of notices of consent attached | tick (schema only) | |
| C140 | Claim authorised (simplified arrangements) | tick | |
| C145 | Name of authorised company | text | |
| C150 | Full name of person authorising | text | |
| C155 | Status | text | |

**Part 4: Amounts surrendered as group relief for carried-forward losses**

| Box | Label (form) | Type (schema) | Notes |
|---|---|---|---|
| C160 | Trading losses carried forward – total | £ | |
| C161 | Trading losses carried forward – Northern Ireland | £ | Leave blank |
| C165 | Non-trading deficit on loan relationships carried forward | £ | |
| C170 | UK property business losses carried forward | £ | |
| C175 | Management expenses carried forward | £ | |
| C180 | Non-trading deficits on intangible fixed assets carried forward | £ | |
| C185 | Total | £ | = C160+C165+C170+C175+C180 |
| C190 | Details of surrender | repeating table, 1..∞ | |
| C190A | Name of claimant company | text | |
| C190B | Accounting period of claimant company | period | |
| C190C | Tax reference | text | |
| C190D | Amount surrendered | £ | |
| C195 | Total | £ | = Σ C190D |
| (SC188/189/190) | Consent options | ticks (schema only) | |
| C200 | Company name | text | = box 1 |
| C205 | Tax reference | UTR | = box 3 |
| C210 | Accounting period start date | date | = box 30 |
| C215 | Accounting period end date | date | = box 35 |
| (SC194) | Certification | tick | |
| C220 | Full name of person authorising | text | |
| C225 | Status | text | |

Cross-form rule 9544: at least one of Parts 1–4 must be completed.

### Main-return linkage

| CT600C | CT600 |
|---|---|
| C10 (claims, current period) | box 310 |
| C130 (claims, carried-forward losses) | box 312 |
| box 105 tick | required before 310/312 can be entered on a new return (rules 9971/10017) |

- **Surrenderer's own return**: the "maximum available for surrender" boxes (785, 800, 810, 835, 840, 845, 855) are the ceilings for C45–C75. For Part 4 the ceilings come from the loss computations.
- **Surrendered amounts do not reduce the surrenderer's CT600 profit boxes**. The surrendered losses leave its carry-forward in the computations.

The group relief rules are in the "Relief rules" section of SUMMARY.md.

---

## CT600D — Company Tax Return – supplementary page: Insurance

- **Form version(s)**: `CT600D (2015) Version 3 for accounting periods starting on or after 1 April 2015`; footer `CT600D(2015) Version 3 Page 1 HMRC 04/15`. Single page.
  - Local file: `downloads/CT600D_2015.pdf` (text: `text/CT600D_2015.txt`). MD5 matches the live gov.uk asset (checked 2026-09-28).
  - Publication: https://www.gov.uk/government/publications/corporation-tax-insurance-ct600d-2015-version-3 (asset https://assets.publishing.service.gov.uk/media/5a7f32dde5274a2e8ab4ab96/CT600D_2015.pdf; page last updated 2025-04-01, and that update only changed links).
  - Guidance: https://www.gov.uk/guidance/supplementary-pages-ct600d-insurance (updated 2024-01-02).
  - XML: `CompanyTaxReturn/Insurance` (type `CTD`), HMRC CT schema v1.995.
  - Applicability: all CT600 (2015+) returns, i.e. accounting periods starting on or after 1 April 2015. It is still the current version as of 2026-09.
- **Purpose / who must file**
  - Complete it if an insurance company (including a friendly society) has entered into policies or contracts during the accounting period that are treated as **Overseas Life Assurance Business (OLAB)**. Source: CT600D guidance.
  - OLAB is defined in FA 2012 s61 (https://www.legislation.gov.uk/ukpga/2012/14/section/61): life assurance business with non-UK-resident policyholders or annuitants that is not excluded business (pension, CTF or ISA business). OLAB is a category of non-BLAGAB business (FA 2012 s57(2)(f)), so it is taxed on the trading basis and not under I − E. See LAM12040: https://www.gov.uk/hmrc-internal-manuals/life-assurance/lam12040
  - The only substantive content is a **compliance declaration** (D5). It confirms the company has obtained or completed the certificates, documents, undertakings and declarations required by regs 4–11 of the Insurance Companies (Overseas Life Assurance Business) (Compliance) Regulations 1995 (SI 1995/3237, amended by SI 2004/3273, 2007/2088 and 2008/2627). Those regulations continue to apply under FA 2012 Sch 17 para 36 (per LAM12040).
  - If the documents were not created or obtained within the regulatory time limits, **leave D5 blank and make the return as if the business is not OLAB**, i.e. treat it as BLAGAB. Source: guidance.
  - CT600D carries **no figures**. The BLAGAB I − E computation, the policyholders' share and life-company trade profits all sit in the main CT600 and computations (LAM: https://www.gov.uk/hmrc-internal-manuals/life-assurance).

### Box table

| Box | Label (verbatim from form) | Type | Notes / calculation |
|---|---|---|---|
| D1 | Company name | text | Paper only. Not a CTD XML element; the value comes from CT600 box 1. |
| D2 | Tax reference | text (10-digit UTR) | Paper only. Comes from CT600 box 3 (the IRheader UTR key). |
| D3 | from DD MM YYYY | date | Period covered by this supplementary page (cannot exceed 12 months). Comes from CT600 box 30. |
| D4 | to DD MM YYYY | date | Comes from CT600 box 35. |
| D5 | The company has obtained or completed all the certificates, documents, undertakings and declarations required by regulations 4 to 11 of the Insurance Companies (Overseas Life Assurance Business) (Compliance) Regulations 1995. These relate to the policies and contracts that have been entered into in the accounting period which is being treated as Overseas Life Assurance Business in this return. Put 'X' in D5 if this applies | tick (X) | Schema `[SD001]` `CTD/Declaration`, `CT_YesType` (only the value `yes`), 0..1. The schema calls the box SD001 while the form calls it D5, a naming difference only. |

- Schema oddity: `CTD` has a single optional child, so a schema-valid `<Insurance/>` can be **empty**, meaning CT600D is present but D5 is not ticked. That is the case where the page is filed but no OLAB compliance is claimed. The form and guidance give no instruction for this case (see caveats).

### Calculations and rules

- The page has no arithmetic.
- The tax rules needed to model insurance companies all live **outside** CT600D:
  - **Box 4 = 5 (Insurance)**: the main guide (https://www.gov.uk/guidance/the-company-tax-return-guide) says to enter 5 "if the policyholders' share of profits is charged at a rate equivalent to the basic rate of Income Tax under Section 88 of the Finance Act 1989". FA 1989 s88 was superseded by **FA 2012 s102** (https://www.legislation.gov.uk/ukpga/2012/14/section/102): the policyholders' share of the I − E profit is charged at the *policyholders' rate of tax*, which equals the savings basic rate of income tax (20%).
  - **Schema rate check**: rules 9199 (box 340) and 9208 (box 390) allow FULL, SMALL CO, EQUIV. LOW (= 20 in the v1.995 schematron for FY2015 onwards), FULL RF or RF SMALL CO rates when box 4 = 5. A company type 5 return can therefore include a 20% line for the policyholders' share alongside the main-rate (25%/19% marginal) lines for the shareholders' share.
  - **I − E / BLAGAB**: BLAGAB profits are computed as I (income and gains) minus E (adjusted BLAGAB management expenses, FA 2012 ss 73–101). LAM04000 onward covers this: https://www.gov.uk/hmrc-internal-manuals/life-assurance/lam04000. The shareholders' share is taxed at the main rate and the policyholders' share at 20% (FA 2012 ss 102–103). Adjusted BLAGAB management expenses (FA 2012 s76) go in CT600 **box 245** "Management expenses" (the guide cites LAM04000 there), and BLAGAB trade losses in box 780 (FA 2012 s78(5)).
  - **Box 555 Life assurance company tax credit**: guide text is "Enter the amount of life assurance company tax credit claimed. The figure in box 555 must not exceed the figure in box 525." It also says to include tax treated as paid on a non-trading loan-relationship credit from an investment life insurance contract (IPTM3900: https://www.gov.uk/hmrc-internal-manuals/insurance-policyholder-taxation-manual/iptm3900). The guide cites LAM04030 for this box, but LAM04030 is actually "Step 1: Amounts treated as ordinary BLAGAB management expenses" (https://www.gov.uk/hmrc-internal-manuals/life-assurance/lam04030). **Box 555 is not fed from CT600D.**
  - Box 555 feeds 560 (560 = 550 + 555, rule 9361), then 575 and 890.
- **OLAB consequence**: if D5 is ticked, the policies written in the period are treated as OLAB. The profits are non-BLAGAB, taxed in the life company's trade profits (CT600 box 155 and so on), and do not enter I − E. If D5 is not ticked, the business stays BLAGAB and enters I − E.

### Main-return linkage

| CT600 box | Label (CT600 (2026) v3) | Link |
|---|---|---|
| 110 | Insurance – form CT600D | Tick (`SupplementaryPages/CT600D`, `CT_YesType`). |
| 4 | Type of company | 5 = Insurance. There is **no** schema cross-check between box 4 = 5 and CT600D. |
| 555 | Life assurance company tax credit | Not fed by CT600D. It is a separate entry, limited to box 525 per the guide. Contextually relevant only. |
| 1 / 3 / 30 / 35 | Company name / Tax reference / period from / to | Source of D1–D4. |

No CT600 amount box is populated from CT600D.

### Key schema validation rules (v1.995)

- **9124**: `[110]='yes'` and the return is New → CTD (`[N098]`) must be present.
- **9308**: CTD present → `[110]` must be `yes`.
- `[SD001]` / `D5` accepts only `yes`; omit the element to mean "not ticked".
- `CTD-rules.txt` contains **no form-specific rules**.

### Worked example

No numeric content. Minimal XML shape:

```xml
<Insurance><Declaration>yes</Declaration></Insurance>
```

It is valid only with `<CT600D>yes</CT600D>` under `ReturnInfoSummary/SupplementaryPages` (box 110).

### Unverified / caveats

- The form and guidance give no instruction on whether to file CT600D (box 110) when the company has OLAB but D5 cannot be ticked. The guidance says to return on a non-OLAB basis. It is unclear whether box 110 should then be ticked with an empty CTD, or CT600D omitted. The schema allows either.
- The guide's box 4 wording cites the repealed FA 1989 s88. The current law is FA 2012 s102 (policyholders' rate = savings basic rate, 20%). The mapping of `[EQUIV. LOW CT RATE]` = 20 to the policyholders' rate is an **inference** from the schematron constants, not a documented HMRC statement.
- The legal basis for the "life assurance company tax credit" (box 555) was not traced to a statute section. The guide's LAM04030 citation looks mis-titled.
- Consolidated in-force status of SI 1995/3237 (as amended) was not re-verified clause by clause.

---

## CT600E — Charities and Community Amateur Sports Clubs (CASCs)

- **Form version(s)**
  - Current: `CT600E (2026) Version 3 for accounting periods starting on or after 1 April 2015`; footer `CT600E(2026) Version 3 … HMRC 04/26`; 4 pages. Local `downloads/CT600E.pdf` (text `text/CT600E.txt`); asset https://assets.publishing.service.gov.uk/media/69ccf8bd5cf899414a0bc5dc/CT600E.pdf (publication updated 2026-04-05).
  - Previous (in force for 2024/2025 filings): `CT600E (2015) Version 3 for accounting periods starting on or after 1 April 2015`; footer `HMRC 04/15`; 3 pages. Local `downloads/CT600E_2015_v3_pre2026.pdf` (text `text/CT600E_2015_v3_pre2026.txt`); asset https://assets.publishing.service.gov.uk/media/5a757055e5274a1622e21c9e/CT600E_2015.pdf (found on the Wayback snapshot of the publication page, 2025-09-15).
  - Publication: https://www.gov.uk/government/publications/corporation-tax-charity-and-community-amateur-sports-clubs-ct600e-2015-version-3
  - Guidance: https://www.gov.uk/guidance/supplementary-pages-ct600e-charities-and-community-amateur-sports-clubs (2026-04-05: "Information for box E88 added. Information for box E85 and E130 to E190 updated. Section added for Legacy details").
  - Schema: `[CTE]` element `Charity` (N099). E88 and the legacy table E195/E200 were added in **v1.994** (live since Oct 2025); v1.995 (awaiting implementation) only changes the E88/E200 cross-rules (see validation).
  - Applicability: HMRC states the "held at the end of the period" → "added during the period" change for E135–E165 "applies to accounting periods starting on or after 1 April 2026". Legacy income becomes attributable income from **6 April 2026** (CTA 2010 s474A, inserted by FA 2026 s54: https://www.legislation.gov.uk/ukpga/2010/4/section/474A). Use the 2015 layout (E90 = E50..E85, E135–E165 = held at end) for APs starting before 1 April 2026.

- **Changes 2015 v3 → 2026 v3** (text diff of the two PDFs)

| Area | CT600E (2015) v3 | CT600E (2026) v3 |
|---|---|---|
| Guidance paragraph (p1) | refers to "What supplementary pages do I need to complete…" and "Important points about all supplementary pages" | refers to "Company Tax return obligations", "Completing your company Tax return" and "Supplementary pages CT600E" |
| E88 | absent | **new** "Legacy income" |
| E90 label | "Total of boxes E50 to E85" | "Total of boxes E50 to E88" |
| Assets column 1 | "Disposals in period" | "Disposals in the period" |
| Assets column 2 (E135/E145/E155/E165, and E170/E175 positioned in same column) | "Held at the end of the period (use accounts figures)" | "Additions in the period (use accounts figures)" |
| Page 4 | absent | **new** "Legacy details" table E195 (A–G, 12 rows) and E200 "Total of column G — Copy this figure to box E88" |
| All other boxes E1–E85, E95–E125, E130, E140, E150, E160, E180–E190 | unchanged labels | unchanged |

- **Purpose / who must file**
  - A charitable company or registered CASC claiming exemption from tax on all or part of its income and gains; the page **is** the claim (guidance; publication page). Also tick E15 if a charity/CASC had no income or gains.
  - Charitable company exemptions: CTA 2010 Part 11 — trading s478–s480 (primary purpose, small-scale trades), fund-raising events s483, lotteries s484, property s485, investment income/NTLR s486, public revenue dividends s487, miscellaneous s488, estate income s489, legacies s474A (from 6 Apr 2026); gains TCGA 1992 s256; restriction for non-charitable expenditure s492–s497; approved investments/loans s511–s514.
  - CASC exemptions: CTA 2010 Part 13 Ch 9 (s658 registration; s662 UK trading income; s663 UK property income; s664 interest/Gift Aid/company gift income; s665 gains; s666 restriction for non-qualifying expenditure).
  - HMRC references: CTM40050 (https://www.gov.uk/hmrc-internal-manuals/company-taxation-manual/ctm40050), Charities detailed guidance notes Annex i–iii (https://www.gov.uk/government/publications/charities-detailed-guidance-notes), CASC detailed guidance notes (https://www.gov.uk/government/publications/community-amateur-sports-clubs-detailed-guidance-notes).

- **Box table** (2026 v3 layout)

| Box | Label (verbatim from form) | Type | Notes / calculation |
|---|---|---|---|
| E1 | Company name (name of charity or CASC) | text | Paper only; XML uses CT600 box 1. |
| E2 | Tax reference | text | Paper only; CT600 box 3. |
| E3 | Period covered by this supplementary page (cannot exceed 12 months) — from | date | Paper only; CT600 box 30. |
| E4 | … to | date | Paper only; CT600 box 35. |
| E5 | Charity/CASC repayment reference | text | 0..1; pattern `(X[NRT]?\|C[RH]\|Z[BCDEFGHJKN]\|EW\|ST\|NI)[0-9]{1,9}`, 2–11 chars. |
| E10 | Charity Commission registration number, or OSCR number (if applicable) | text | 0..1; alphanumeric 6–8 chars. Schema desc says "Scottish Charity number". |
| E15 | The company was a charity/CASC and is claiming exemption from all tax on all or part of its income and gains (Also put an 'X' in box E15 if the company was a charity/CASC but had no income or gains in the period.) | tick (X) | **1..1 mandatory**. |
| E20 | All income and gains are exempt from tax and have been, or will be, applied for charitable or qualifying purposes only | tick (X) | XSD `choice`: exactly one of E20/E25 (1..1 group `AllCharitable`). |
| E25 | Some of the income and gains may not be exempt or have not been applied for charitable or qualifying purposes only, and I have completed form CT600 | tick (X) | Other branch of the E20/E25 choice; non-exempt amounts go on CT600. |
| E30 | I claim exemption from tax — Name | text | Paper only; not in schema (online: CT600 declaration box 975). |
| E35 | Status | text | Paper only (CT600 box 985). CASCs: treasurer signs (guidance). |
| E40 | Date | date | Paper only (CT600 box 980). |
| E45 | Put an 'X' in the box if during the period covered by these supplementary pages you have over claimed tax. | tick (X) | 0..1. Schema desc garbled ("E3 e3c included amounts"). Repayment claims go via Charities Online, not this page. |
| E50 | Enter total turnover from exempt charitable trading activities | amount £ (whole pounds) | 0..1. Exempt trade turnover (CTA 2010 s478/s480; CASC s662). |
| E55 | Investment income – exclude any amounts included on form CT600 | amount £ (whole pounds) | 0..1. |
| E60 | UK land and buildings – exclude any amounts included on form CT600 | amount £ (whole pounds) | 0..1. |
| E65 | Gift Aid – exclude any amounts included on form CT600 | amount £ (whole pounds) | 0..1. |
| E70 | From other charities – exclude any amounts included on form CT600 | amount £ (whole pounds) | 0..1. |
| E75 | Gifts of shares or securities received | amount £ (whole pounds) | 0..1 (ITA 2007 s431 gifts). |
| E80 | Gifts of real property received | amount £ (whole pounds) | 0..1 (ITA 2007 s431 gifts). |
| E85 | Other sources (not included above) | amount £ (whole pounds) | 0..1. Includes donations from wholly-owned trading subsidiary; "case VI income". |
| E88 | Legacy income | amount £ (whole pounds) | 0..1. **New 2026.** = E200. |
| E90 | Total of boxes E50 to E88 | amount £ (whole pounds) | **1..1 if Income group present.** = E50+E55+E60+E65+E70+E75+E80+E85+E88 (9614). |
| E95 | Trading costs in relation to exempt charitable activities (in box E50) | amount £ (whole pounds) | 0..1; requires E50 > 0 (9611). |
| E100 | UK land and buildings costs in relation to exempt charitable activities (in box E60) | amount £ (whole pounds) | 0..1; requires E60 > 0 (9612). |
| E105 | All general administration/governance costs | amount £ (whole pounds) | 0..1. |
| E110 | All grants and donations made within the UK | amount £ (whole pounds) | 0..1. |
| E115 | All grants and donations made outside the UK | amount £ (whole pounds) | 0..1. |
| E120 | Other expenditure not included above, or not used in calculating figures entered on the form CT600 | amount £ (whole pounds) | 0..1. |
| E125 | Total of boxes E95 to E120 | amount £ (whole pounds) | **1..1 if Expenditure group present.** = E95+E100+E105+E110+E115+E120 (9615). |
| E130 | Tangible fixed assets — Disposals in the period (total consideration received) | amount £ (whole pounds) | 0..1. |
| E135 | Tangible fixed assets — Additions in the period (use accounts figures) | amount £ (whole pounds) | 0..1. XML element still named `Held`. Pre-2026 meaning: held at end of period. |
| E140 | UK investments (excluding controlled companies) — Disposals in the period | amount £ (whole pounds) | 0..1. |
| E145 | UK investments (excluding controlled companies) — Additions in the period | amount £ (whole pounds) | 0..1 (`Held`). |
| E150 | Shares in, and loans to, controlled companies — Disposals in the period | amount £ (whole pounds) | 0..1. |
| E155 | Shares in, and loans to, controlled companies — Additions in the period | amount £ (whole pounds) | 0..1 (`Held`). |
| E160 | Overseas investments — Disposals in the period | amount £ (whole pounds) | 0..1. |
| E165 | Overseas investments — Additions in the period | amount £ (whole pounds) | 0..1 (`Held`). |
| E170 | Loans and non-trade debtors | amount £ (whole pounds) | 1..1 inside optional group. Printed in the "Additions" column; schema desc "Additions in the period". |
| E175 | Other current assets | amount £ (whole pounds) | As E170. |
| E180 | Qualifying investments and loans — Applies to charities only. See CT600 Guide | tick (X) | 0..1. Tick only if **all** investments/loans are approved (s511–s514). Not with E185 (9613). |
| E185 | Value of any non-qualifying investments and loans — Applies to charities only. See CT600 Guide | amount £ (whole pounds) | 0..1. Non-qualifying investments/loans where no claim made with the return. |
| E190 | Number of subsidiary or associated companies the charity controls at the end of the period. Exclude companies that were dormant throughout the period | count | 0..1; integer ≤ 999. |
| E195 | Legacy details — Please list the legacy donors. | repeating table 1..∞ | Group `LegacyPayments` 0..1; ≥1 row when present. Paper: 12 rows. |
| E195A | A — Forenames | text | 1..1 (`CTexcludedCharsStringType`). Guidance/schema: "Forename". Aggregated row: "X". |
| E195B | B — Surname | text | 1..1. Aggregated row: "X". |
| E195C | C — Address | text | 1..2 address lines. Aggregated row: "X". |
| E195D | D — Postcode | text | 0..1 `CT_PostCodeType`; UK address only. |
| E195E | E — Overseas | tick (X) | 0..1. Exactly one of D/E per row. Aggregated row: "X". |
| E195F | F — Date | date | 1..1; ≤ CT600 box 35 (8028). |
| E195G | G — Amount | amount £ (whole pounds) | 1..1. |
| E200 | Total of column G — Copy this figure to box E88 | amount £ (whole pounds) | 1..1 within group. = ΣE195G (8029); = E88 (8083). |

- **Calculations and rules**
  - Form totals: `E90 = E50+E55+E60+E65+E70+E75+E80+E85+E88`; `E125 = E95+…+E120`; `E200 = ΣE195G`; `E88 = E200`.
  - The page records **exempt** income only; non-exempt income and gains go in the normal CT600 boxes (E25 case). The page does not compute tax.
  - **Charity non-charitable expenditure restriction** (CTA 2010 s492–s496; Annex ii): non-exempt amount = min(A, B), A = non-charitable expenditure (incl. non-qualifying investments/loans, non-primary-purpose trading losses, payments to overseas bodies without reasonable steps), B = attributable income and gains (exempt income + s256 TCGA gains; from 6 Apr 2026 includes legacies). Exemption is withdrawn on income attributed to the non-exempt amount; charity may choose which sources (s494–s495; within 30 days of HMRC notice). Excess non-charitable expenditure over total income/gains is carried back to earlier periods, ending ≤ 6 years before (Annex ii §6).
  - **Approved investments** (s511–s514; Annex iii): investments acquired from 6 April 2026 must be of types 1–11 **and** made for an allowable purpose (sole purpose of benefiting the charity, not tax avoidance), or otherwise made for an allowable purpose.
  - **Small trading exemption** (s480, s482): non-exempt trading + miscellaneous incoming resources ≤ requisite limit = 25% of total incoming resources, floor £8,000, cap £80,000 (pro-rata for APs < 12 months).
  - **CASC limits**: UK trading receipts ≤ £50,000 (s662(5)); UK property receipts ≤ £30,000 (s663(5)); both for a 12-month AP, proportionately reduced for shorter APs; income must be applied for qualifying purposes. Interest, Gift Aid and company gift income exempt if applied for qualifying purposes (s664); gains exempt (s665).
  - **CASC non-qualifying expenditure** (s666): if NQE < IRCG, exempt income/gains reduced by `RIRG × NQE / IRCG`; if NQE ≥ IRCG no exemption for the period (s666(6)); excess reduces reliefs of earlier periods (s666(7)–(9)).

- **Main-return linkage**
  - CT600 **box 115** tick. N099 present ⇒ 115 = yes (9309); 115 + new return ⇒ N099 present (9125).
  - CT600 **box 4**: `8` = "Charity or owned by a charity" (guide; CTM40050). Schema message 9147 lists type `0` as "UK trading or Professional Services or CASC" — CASCs use 0 (unless 6 "Members' club" is more apt; not confirmed in guide).
  - No CT600 box is fed by CT600E amounts. If E20 (all exempt), CT600 still needs company information, "About this return" and the declaration (guidance E50); XML-mandatory calculation boxes (e.g. 315, 440) are submitted as 0. If E25, the non-exempt income and gains go in the normal CT600 income boxes (155–220) and are taxed at the normal rates (schema allows full/small rate for type 8).
  - Declaration E30/E35/E40 is paper-only; online the CT600 declaration (975/980/985) covers supplementary pages.

- **Key schema validation rules** (v1.995 unless stated)
  - 9614 E90 sum; 9615 E125 sum; 9611 E95 ⇒ E50 > 0; 9612 E100 ⇒ E60 > 0; 9613 not both E180 and E185.
  - 8026 (`LEGACYPAYMENT.0`): each E195 row must have Postcode or Overseas; 8027: Overseas not allowed with Postcode; 8028: E195F ≤ box 35.
  - 8029: E200 = ΣE195G; 8030: E200 ⇒ E88 present; 8083 (new in v1.995): E200 = E88.
  - v1.994 (live) instead had 8023 "Box E88 can only be completed if Box E200 is completed" and 8024 "Box E88 must equal Box E200"; v1.995 drops these, so under v1.995 E88 without a legacy table passes. HMRC guidance still expects at least an aggregated first row.
  - XSD: E15 mandatory; exactly one of E20/E25; E90 and E125 mandatory when their groups exist; E190 ≤ 999.

- **Worked example** (charity, AP 1 Apr 2026–31 Mar 2027)
  - Accounts: bank interest 12,000; Gift Aid 28,000; one legacy 5,000 (E195 aggregated row: X / X / X / — / X / 15 06 2026 / 5,000; E200 = 5,000; E88 = 5,000).
  - Expenditure: E105 4,000; E110 30,000 ⇒ E125 = 34,000. Non-qualifying loan £7,000 ⇒ E185 = 7,000 (E180 blank).
  - Restriction: attributable income 45,000; non-charitable expenditure 7,000 ⇒ non-exempt amount = min(7,000, 45,000) = £7,000; charity attributes it to interest.
  - Result: tick E15 and E25 (not E20); E55 = 12,000 − 7,000 = 5,000 ("exclude any amounts included on form CT600"); E65 = 28,000; E90 = 5,000 + 28,000 + 5,000 = 38,000; CT600 box 170 = 7,000; box 4 = 8; box 115 ticked.

- **Unverified / caveats**
  - E170/E175 sit in the "Additions in the period" column and the schema says "Additions", but "additions" to loans/debtors/current assets is odd; pre-2026 these were balances held at the end. Confirm with HMRC before relying on either meaning.
  - Rule 8026 English message swaps letters ("postcode in Box E195E … overseas indicator in Box E195D"); the XSD and form have D = Postcode, E = Overseas. Implement from the XSD.
  - Guidance cites ITA 2007 s525–s529 for charity trading exemptions; for charitable **companies** the provisions are CTA 2010 s478–s480. CASC trading exemption is s662 (guidance says "Chapter 9 CTA 2010").
  - CASC box 4 code (0 vs 6) not stated in the CT600 guide.
  - Which version of the schema HMRC will enforce on a given filing date (v1.994 live vs v1.995 awaiting) changes the E88/E200 rules.

---

## CT600F — Tonnage Tax

- **Form version(s)**
  - Printed version string: `CT600F (2025) Version 3 for accounting periods starting on or after 1 April 2015`; footer `CT600F(2025) Version 3 … HMRC 04/25`; 3 pages.
  - Local file: `downloads/CT600F.pdf` (text `text/CT600F.txt`).
  - Previous edition, used for filings Apr 2023 – Mar 2025 including 2024: `downloads/CT600F_2023_v3.pdf`, "CT600F (2023) Version 3", HMRC 04/23, recovered from the Wayback Machine. The only differences from the 2025 edition are:
    - no box F15C (group does not operate, only manages, qualifying ships);
    - F30C wording lacks "or relates to periods on or after 1 April 2022";
    - the F70 interest-in-ship column has codes O/F/T/G only, with no "M – managed only", and the columns read "Days operated" / "Operated for first time".
  - Publication: https://www.gov.uk/government/publications/corporation-tax-tonnage-tax-ct600f-2015-version-3 (asset https://assets.publishing.service.gov.uk/media/67c0159c72e83aab48866b5c/CT600F.pdf; "forms and guidance have been updated for 2025", 2025-04-01).
  - Guidance: https://www.gov.uk/guidance/supplementary-pages-ct600f-tonnage-tax (2025-04-01: "updated to include Box F15C, legislation links to Tonnage Tax activities and information regarding qualifying ship managed by a company"; 2023-03-31: headings for F30 and F65 updated).
  - Schema: `[CTF]` element `TonnageTax` (N100), v1.995 = v1.994 for CTF.
  - Applicability: all CT600 v3 APs. Period-dependent rules: flagging boxes F30A/F30B/F35 not allowed for APs starting on/after 1 April 2022 (FA 2022 s25); managed-only ships (interest code M, lower daily rates) only for tonnage tax elections made on/after 1 April 2024 (FA 2024 Sch 8 para 8).

- **Purpose / who must file**
  - A company that operates (or, for elections on/after 1 April 2024, manages) qualifying ships and is party to a tonnage tax election (guidance; FA 2000 Sch 22 paras 7–8, 16, 18A: https://www.legislation.gov.uk/ukpga/2000/17/schedule/22).
  - Tonnage tax profits replace relevant shipping profits, which (and losses) are left out of account for CT (FA 2000 Sch 22 para 3; Part VI; TTM06000).
  - Qualifying ship: seagoing, ≥100 gross tons, carrying passengers/cargo, towage, salvage etc.; excludes fishing vessels, factory ships, pleasure craft, harbour/river ferries, offshore installations, dedicated oil-field tankers, dredgers (guidance; TTM03000).
  - Election lasts 8 years from start of the AP in which it is made (FA 2022 s25, was 10 years; TTM01040).

- **Box table**

| Box | Label (verbatim from form) | Type | Notes / calculation |
|---|---|---|---|
| F1 | Company name | text | Paper only; CT600 box 1. |
| F2 | Tax reference | text | Paper only; CT600 box 3. |
| F3 | Period covered by this supplementary page (cannot exceed 12 months) — from | date | Paper only; CT600 box 30. |
| F4 | … to | date | Paper only; CT600 box 35. |
| F5A / F5B | The company was a party to a Tonnage Tax group election — Yes / No ("If 'Yes' complete F10. If 'No' complete F15A or F15B") | tick (X) | XML: one element `GroupElection` = yes/no (`YesNoType`), inside optional `TonnageGroup` (0..1). |
| F10 | Name of Tonnage Tax group of which the company was a member at the AP end ("Complete only if the company answered 'Yes' to F5A") | text | 0..1; 2–56 chars. Required if F5A (9651); forbidden if F5B (9653). |
| F15A / F15B / F15C | The company or group was covered by a training certificate — Yes / No / Not applicable ("Complete box F15C if the company or group does not operate (in contrast to manage) any qualifying ships") | tick (X) | 1..1, `CTYesNoNAType` yes/no/na. |
| F20A / F20B / F20C | The company met the prescribed limit on chartered-in tonnage ("If the company answered 'Yes' in F5A complete F20C") | tick (X) | 1..1 yes/no/na; must be `na` if F5A (9656). |
| F25A / F25B / F25C | The group met the prescribed limit on chartered-in tonnage ("Complete only if the company answered 'Yes' in F5A. Complete box F25C if the company is party to a group arrangement but is NOT the representative company") | tick (X) | 0..1 yes/no/na; required if F5A (9652); forbidden if F5B (9659). |
| F30A / F30B / F30C | The company or group operated ships that were NOT registered in the UK for the first time ("If the period covered by the return relates entirely to 'excepted years' or relates to periods on or after 1 April 2022 complete box F30C") | tick (X) | 1..1 yes/no/na; must be `na` if box 30 ≥ 2022-04-01 (9464). |
| F35A / F35B | The company or group satisfied the flagging conditions — Yes / No ("Complete only if the company answered 'Yes' in F30A") | tick (X) | 0..1 yes/no; required iff F30A (9664, 9665). |
| F40A / F40B | The company is subject to the special rules for offshore activities — Yes / No | tick (X) | 1..1 yes/no. FA 2000 Sch 22 Part XI. |
| F45 | The amount of training allowance to be offset against the Corporation Tax liability ("Include the amount in box F45 in box 450 on form CT600") | amount £p | 0..1; >0. Part 2 only if F40A (9660/9666). |
| F50 | The amount of training allowance to be carried forward | amount £p | 0..1; >0. Only record of the carry-forward (TTM01400). |
| F55A | The profit or loss in the company's accounts (other than non-tonnage-tax amounts and F60/F65 amounts) — Profit | amount £ (whole pounds) | XML `choice`: Profit (≥0) xor Loss. Group `Other` (schema id [F11]) 0..1. |
| F55B | … — Loss | amount £ (whole pounds) | Loss must be > 0 (entered as a positive number). |
| F60A | The profit or loss in the company's accounts in respect of the disposal of Tonnage Tax assets, which would otherwise be computed under chargeable gains rules — Profit | amount £ (whole pounds) | `choice` Profit xor Loss; group `DisposalOfAssets` (schema id [F12]) 0..1 (FA 2000 Sch 22 Part VIII). |
| F60B | … — Loss | amount £ (whole pounds) | >0. |
| F65 | Dividends and other distributions qualifying as relevant shipping income | amount £ (whole pounds) | 0..1 (FA 2000 Sch 22 para 49). |
| F70 (table) | Part 4: Computation of Tonnage Tax profits | repeating table 1..200 | Group `QualifyingShips` 0..1; 1–200 `Ship` rows (paper: 10 rows). |
| F70A | A — Name of ship | text | 1..1; 2–56 chars. |
| F70B | B — IMO number | count | 1..1 integer, pattern `[1-9][0-9]{6,7}`, 1,000,000–99,999,999. |
| F70C | C — Interest in ship, or if managed only (O/F/T/G/M)* | text (code) | 1..1 enum: O owned or bareboat chartered in (not finance leased); F finance leased; T chartered in otherwise than bareboat (time/voyage); G chartered from another member of the same tonnage tax group; M managed only (crew, vessel or safety management). |
| F70D | D — Gross tonnage | count | 1..1 integer (no bounds; schema description blank). Used for ≥100 GT qualifying test only. |
| F70E | E — Net tonnage | count | 1..1 integer 0–9,999,999. Drives the calculation. |
| F70F | F — Days operated or managed | count | 1..1 integer 1–366. |
| F70G | G — Tonnage Tax profits | amount £p | 1..1 ≥0 = daily profit × F. |
| F70H | H — Flagged in register of United Kingdom — Yes or No | tick (X) (yes/no) | 1..1 `YesNoType`. |
| F70I | I — Operated or managed for first time in AP — Yes or No | tick (X) (yes/no) | 1..1 `YesNoType`. |
| F70 | Total column G in box F70 and then copy the figure to box 200 on form CT600 | amount £ (whole pounds) | 1..1 in group = floor(ΣF70G) (9663). |

Column order A–I on the PDF (x-positions checked) matches the schema's F70A–F70I.

- **Calculations and rules**
  - **Daily profit per ship** (FA 2000 Sch 22 para 4, as amended by FA 2024 Sch 8 para 3; https://www.legislation.gov.uk/ukpga/2000/17/schedule/22/paragraph/4; TTM01300). Net tonnage is first **rounded down to the nearest multiple of 100 tons** (para 4(1)); then per 100-ton unit:

| Net tonnage band | Operated ship | Managed ship (code M) |
|---|---|---|
| each 100 t up to 1,000 t | £0.60 | £0.12 |
| each 100 t between 1,000 and 10,000 t | £0.45 | £0.09 |
| each 100 t between 10,000 and 25,000 t | £0.30 | £0.06 |
| each 100 t above 25,000 t | £0.15 | £0.03 |

  - Rates have **not** been uprated since 2000; the only change is the FA 2024 managed-ship column (1/5 of operated; elections on/after 1 April 2024; TTM01040). The CT600F guidance lists only the operated rates.
  - Formula: `units = floor(NT / 100)`; `daily = 0.60·min(u,10) + 0.45·clamp(u−10,0,90) + 0.30·clamp(u−100,0,150) + 0.15·max(u−250,0)` (× 1/5 for M). `F70G = daily × days` (days in AP operated/managed; leap year 366). `F70 = floor(Σ F70G)`.
  - Joint interests: each joint operator taxed on its share of the ship's profit; multiple operators at different levels each taxed as sole operator (para 5; TTM01310/01320).
  - **Ring fence**: no relief, deduction or set-off of any description against tonnage tax profits — no pre-entry or non-tonnage trade losses, group relief, interest (TTM07200). Tax attributable to tonnage tax profits is payable without set-off of DTR or surplus ACT; only marginal relief and income tax suffered remain available (TTM07210). Tonnage tax profits are treated as nil for CIR tax-EBITDA.
  - **75% chartered-in limit**: ≤75% of net tonnage of qualifying ships may be chartered in other than bareboat, measured on aggregate daily net tonnage; group-wide for groups ignoring intra-group charters (paras 37–40; TTM05000).
  - **Offshore training allowance** (para 114; TTM11400/11410): set against CT on offshore-activity profits only; = cost of training requirement agreed with DfT minus what it would have been had the ship not been qualifying, using PILOT rate (£1,421 per trainee per month from 1 Oct 2023); excess carried forward (F50).
  - Flagging conditions (introduced in 2005) repealed from 1 April 2022 (FA 2022 s25(7); guidance; TTM01040).

- **Main-return linkage**
  - CT600 **box 120** tick. N100 present ⇒ 120 = yes (9310); 120 + new ⇒ N100 present (9126); 120 ⇒ box 200 present (9127).
  - **F70 → CT600 box 200** "Tonnage Tax profits" (guide; 9155: 200 = F70 if F70 present; 9154: 200 only if 120 ticked or amended return).
  - Box 200 is part of **box 235** = 165+170+175+180+185+190+195+200+205+220 − (225+230) (9332) → box 315 → taxed at the normal CT rates (marginal relief allowed). Implementation must ensure deductions in boxes 240–312 are not absorbed by the tonnage tax profit (ring fence; no schema rule enforces this).
  - **F45 → included in CT600 box 450** (Double Taxation Relief) (guide; 9140: F45 present ⇒ box 450 present and ≥ F45). Box 450 ≤ 440 − 445 (9242); 470 = 445 + 450 + 465 (9247).
  - Relevant shipping profits (F55–F65) are excluded from the CT computation; they feed no CT600 box.

- **Key schema validation rules**
  - 9650: CT600F requires Part 3 (`RelevantShippingProfits`) or Part 4 (`QualifyingShips`).
  - 9651/9653: F10 iff F5A; 9652/9659: F25 iff F5A; 9656: F5A ⇒ F20 = na.
  - 9464: box 30 ≥ 2022-04-01 ⇒ F30 = na; 9664/9665: F35 iff F30 = yes.
  - 9660/9666: offshore training allowance group iff F40A.
  - 9663: F70 = floor(ΣF70G).
  - XSD: F55/F60 Profit xor Loss (Loss > 0); ship rows 1–200; IMO 7–8 digits; NT 0–9,999,999; days 1–366; code ∈ {O,F,T,G,M}.

- **Worked example** (AP 1 Jan–31 Dec 2025, 365 days)

| Ship | C | NT (rounded) | Units per band (0.60/0.45/0.30/0.15) | Daily | Days | F70G |
|---|---|---|---|---|---|---|
| Northern Star | O | 30,099 (30,000) | 10 / 90 / 150 / 50 | £99.00 | 365 | £36,135.00 |
| Tern | M | 5,450 (5,400) | 10 / 44 / 0 / 0 at managed rates 0.12/0.09 | £5.16 | 183 | £944.28 |

  - F70 = floor(36,135.00 + 944.28) = **£37,079** → CT600 box 200 = 37,079; box 120 ticked.
  - Cross-check with HMRC: 30,099 nt ⇒ £99 daily (guidance example); 17,371 nt ⇒ £68.40 (TTM01300); 32,495 nt ⇒ £102.60 (TTM01340).

- **Unverified / caveats**
  - TTM01400 ("The tonnage tax return (CT600F)", updated 2026-01-19) still describes the pre-2015 form (F10 → box 145, F8 → box 61); ignore its box numbers.
  - F70D gross tonnage has no schema description or bounds; F70C = M with pre-1 April 2024 elections is not blocked by the schema.
  - Guidance text "If No (F5B) complete box F15A, box F15B or box F15C" understates the schema: F15, F20, F30, F40 are always mandatory.
  - Whether CT600F must be filed with only Part 3 (no ships) is allowed by 9650 but its practical scenario (e.g. ships ceased) is not documented.
  - Paper page header for F55 is shortened in the table above; full text: "The profit or loss in the company's accounts. Do not include other non-tonnage tax profits or losses included elsewhere on form CT600 or any amounts entered in boxes F60A, F60B or F65 below".

---

## CT600G — Northern Ireland (DORMANT — no form published, no NI rate in force)

> **Status: not in use.** No Northern Ireland rate of Corporation Tax has been set, the CT600 guide says to leave every NI box blank, and the HMRC schema only accepts the NI boxes on the main return for periods ending on or after **1 April 2050** (a placeholder date). Implement CT600G only as a schema-shaped, disabled feature. Everything below comes from the XML schema (v1.995 `[CTG]`, 148 elements), not from a paper form.

- **Form version(s)**
  - **No CT600G (2015) v3 PDF exists on gov.uk.** CT600 (2026) v3 page 2 lists "125 Northern Ireland – form CT600G" (`text/CT600_2026_v3.txt`), but a gov.uk search for CT600G returns only the obsolete *Corporation Tax: Corporate Venturing Scheme (CT600G (2006) Version 2)* (https://www.gov.uk/government/publications/corporation-tax-corporate-venturing-scheme-ct600g-2006-version-2, 2014 archive) — a different form for pre-2015 periods.
  - HMRC's COTAX manual lists "CT600G CT600 return form supplementary page. Corporate Venturing Scheme. This is not used with the CT600 v3." (COM132011, updated 2025-12-31: https://www.gov.uk/hmrc-internal-manuals/cotax-manual/com132011).
  - CT600 publication page: "This form has been updated in readiness for when a Northern Ireland Executive together with the UK government decide to introduce a devolved rate … Do not make entries in any of the Northern Ireland boxes until a Northern Ireland rate has been intro[duced]" (https://www.gov.uk/government/publications/corporation-tax-company-tax-return-ct600-2015-version-3).
  - No CT600G guidance page; the CT600 guide (https://www.gov.uk/guidance/the-company-tax-return-guide) says: "Leave the Northern Ireland section (boxes 5 to 8) blank. There is no separate Corporation Tax rate for Northern Ireland."; box 325 "Leave this box blank."; box 586 "Leave this box blank."; "Northern Ireland information — Leave this section (boxes 856 to 858) blank."
  - Policy/legal guidance: *Northern Ireland Corporation Tax regime: draft guidance* (https://www.gov.uk/government/publications/northern-ireland-corporation-tax-regime-draft-guidance, last updated 2018-01-31; local `downloads/NI_CTregime-draft_guidance.pdf`, 121 pp): the Government "will commence the Act … once a restored Northern Ireland Executive demonstrates its finances are on a sustainable footing".
  - Schema: `[CTG]`, element `NorthernIreland` (N101) under `CompanyTaxReturn`; identical in v1.994 and v1.995.
  - Applicability: none today. Legally, CTA 2010 Part 8B applies to APs beginning on/after the first day of a Treasury-appointed financial year (Corporation Tax (Northern Ireland) Act 2015 s5(3)–(4): https://www.legislation.gov.uk/ukpga/2015/21/section/5). No appointing regulations were found on legislation.gov.uk (search 2026-09-28); legislation.gov.uk shows Part 8B "inserted (with effect in accordance with s. 5 of the amending Act)".

- **Purpose / who must file (if ever commenced)**
  - CTA 2010 Part 8B (s357H onwards; https://www.legislation.gov.uk/ukpga/2010/4/section/357H): Northern Ireland profits of a trade are charged at the Northern Ireland rate instead of the main rate (s357JA(2)); the rate would be set by the NI Assembly (s357IA; CT(NI)A 2015 s5(3)).
  - Applies to a "Northern Ireland company" (s357KA): carries on a qualifying trade (s357KB; excluded trades Ch 17, with an election to bring in back-office activities of lending/investment, investment management and re-insurance trades) and meets the SME (NI employer) condition, the SME (election) condition, or the large company condition (not SME and has an NI regional establishment).
  - Profit attribution: Ch 6 (SME that is an NI employer — workforce-based) or Ch 7 (large companies and electing SMEs — NI RE attribution); CT600 boxes 5–8 capture which regime applies and CT600G splits every computation line into NI / rest of UK.
  - Losses: NI and mainstream losses relieved separately (s357JB); NI losses set against mainstream profits give a restricted deduction when the NI rate is below the main rate (s357JC, s357JJ: `(NIR/MR) × L1 + L2`, L1 unmatched loss, L2 matched loss).

- **Box table** (schema only; there are no G1–G4 company-information boxes in the schema and no paper labels. "Label" = schema description; group label — column. A = Northern Ireland, B = Rest of UK, C = Total. "1..1" totals are mandatory only when their parent group is present.)

| Box | Label (schema description; no PDF) | Type | Notes / calculation |
|---|---|---|---|
| G5A | Trading profits — Northern Ireland | amount £ | schema 0..1 |
| G5B | Trading profits — Rest of UK | amount £ | schema 0..1 |
| G5C | Trading profits — Total | amount £ | schema 1..1; = CT600 box 155; rules 9187, 9189, 9191, 9192 |
| G10A | Trading losses brought forward - value set against trading profits — Northern Ireland | amount £ | schema 0..1 |
| G10B | Trading losses brought forward - value set against trading profits — Rest of UK | amount £ | schema 0..1 |
| G10C | Trading losses brought forward - value set against trading profits — Total | amount £ | schema 1..1; = CT600 box 160; rules 9194, 9196, 9205, 9215, 9217 |
| G15B | Trading losses brought forward - amount used against profits — Rest of UK | amount £ | schema 1..1 |
| G15C | Trading losses brought forward - amount used against profits — Total | amount £ | schema 1..1; rules 9219 |
| G20A | Net trading profits — Northern Ireland | amount £ | schema 0..1 |
| G20B | Net trading profits — Rest of UK | amount £ | schema 0..1 |
| G20C | Net trading profits — Total | amount £ | schema 1..1; = CT600 box 165; rules 9243, 9253, 9255, 9256 |
| G25B | Non-trade profits and gains — Rest of UK | amount £ | schema 1..1 |
| G25C | Non-trade profits and gains — Total | amount £ | schema 1..1; rules 9259 |
| G30A | Total profits and gains — Northern Ireland | amount £ | schema 0..1 |
| G30B | Total profits and gains — Rest of UK | amount £ | schema 0..1 |
| G30C | Total profits and gains — Total | amount £ | schema 1..1; rules 9262, 9265, 9266 |
| G35B | Losses brought forward against certain investment income — Rest of UK | amount £ | schema 1..1 |
| G35C | Losses brought forward against certain investment income — Total | amount £ | schema 1..1; = CT600 box 225; rules 9292, 9293, 9090 |
| G40B | Non-trade deficits on loan relationships (including interest) and derivative contracts (financial instruments) brought forward set against non-trading profits — Rest of UK | amount £ | schema 1..1 |
| G40C | Non-trade deficits on loan relationships (including interest) and derivative contracts (financial instruments) brought forward set against non-trading profits — Total | amount £ | schema 1..1; = CT600 box 230; rules 9091, 9092, 9093 |
| G45A | Profits before other deductions and reliefs — Northern Ireland | amount £ | schema 0..1; rules 9095 |
| G45B | Profits before other deductions and reliefs — Rest of UK | amount £ | schema 0..1; rules 9096 |
| G45C | Profits before other deductions and reliefs — Total | amount £ | schema 1..1; = CT600 box 235; rules 9097, 9098, 9280, 9294, 9295 |
| G50A | Losses on unquoted shares — Northern Ireland | amount £ | schema 0..1 |
| G50B | Losses on unquoted shares — Rest of UK | amount £ | schema 0..1 |
| G50C | Losses on unquoted shares — Total | amount £ | schema 1..1; = CT600 box 240; rules 9299, 9311, 9317, 9402 |
| G55A | Management expenses — Northern Ireland | amount £ | schema 0..1 |
| G55B | Management expenses — Rest of UK | amount £ | schema 0..1 |
| G55C | Management expenses — Total | amount £ | schema 1..1; = CT600 box 245; rules 9410, 9441, 9442, 9443 |
| G60A | UK property business losses for this or previous accounting period — Northern Ireland | amount £ | schema 0..1 |
| G60B | UK property business losses for this or previous accounting period — Rest of UK | amount £ | schema 0..1 |
| G60C | UK property business losses for this or previous accounting period — Total | amount £ | schema 1..1; = CT600 box 250; rules 9444, 9445, 9446, 9447 |
| G65A | Capital allowances for the purposes of management of the business — Northern Ireland | amount £ | schema 0..1 |
| G65B | Capital allowances for the purposes of management of the business — Rest of UK | amount £ | schema 0..1 |
| G65C | Capital allowances for the purposes of management of the business — Total | amount £ | schema 1..1; = CT600 box 255; rules 9448, 9449, 9530, 9531 |
| G70A | Non-trade deficits for this accounting period from loan relationships and derivative contracts (financial instruments) — Northern Ireland | amount £ | schema 0..1 |
| G70B | Non-trade deficits for this accounting period from loan relationships and derivative contracts (financial instruments) — Rest of UK | amount £ | schema 0..1 |
| G70C | Non-trade deficits for this accounting period from loan relationships and derivative contracts (financial instruments) — Total | amount £ | schema 1..1; = CT600 box 260; rules 9532, 9533, 9534, 9535 |
| G73A | Carried forward non-trade deficits from loan relationships and derivative contracts (financial instruments) — Northern Ireland | amount £ | schema 0..1 |
| G73B | Carried forward non-trade deficits from loan relationships and derivative contracts (financial instruments) — Rest of UK | amount £ | schema 0..1 |
| G73C | Carried forward non-trade deficits from loan relationships and derivative contracts (financial instruments) — Total | amount £ | schema 1..1; = CT600 box 263; rules 9536, 9537, 9538, 9539 |
| G75A | Non-trading losses on intangible fixed assets — Northern Ireland | amount £ | schema 0..1 |
| G75B | Non-trading losses on intangible fixed assets — Rest of UK | amount £ | schema 0..1 |
| G75C | Non-trading losses on intangible fixed assets — Total | amount £ | schema 1..1; = CT600 box 265; rules 9540, 9541, 9542, 9570 |
| G80A | Total trading losses of this or a later accounting period - value — Northern Ireland | amount £ | schema 0..1 |
| G80B | Total trading losses of this or a later accounting period - value — Rest of UK | amount £ | schema 0..1 |
| G80C | Total trading losses of this or a later accounting period - value — Total | amount £ | schema 1..1; = CT600 box 275; rules 9571, 9572, 9573, 9574 |
| G85B | Total trading losses of this or a later accounting period - amount used — Rest of UK | amount £ | schema 1..1 |
| G85C | Total trading losses of this or a later accounting period - amount used — Total | amount £ | schema 1..1; rules 9575 |
| G90 | Are amounts carried back from later accounting periods included in box G80? | tick (X) | schema 0..1; rules 9576 |
| G92A | Trading losses carried forward and claimed against total profits - value — Northern Ireland | amount £ | schema 0..1 |
| G92B | Trading losses carried forward and claimed against total profits - value — Rest of UK | amount £ | schema 0..1 |
| G92C | Trading losses carried forward and claimed against total profits - value — Total | amount £ | schema 1..1; = CT600 box 285; rules 9577, 9578, 9579, 9580 |
| G93B | Trading losses carried forward and claimed against total profits - amount used — Rest of UK | amount £ | schema 1..1 |
| G93C | Trading losses carried forward and claimed against total profits - amount used — Total | amount £ | schema 1..1; rules 9581 |
| G95A | Non-trade capital allowances — Northern Ireland | amount £ | schema 0..1 |
| G95B | Non-trade capital allowances — Rest of UK | amount £ | schema 0..1 |
| G95C | Non-trade capital allowances — Total | amount £ | schema 1..1; = CT600 box 290; rules 9582, 9583, 9584, 9585 |
| G100A | Total of deductions and reliefs — Northern Ireland | amount £ | schema 0..1 |
| G100B | Total of deductions and reliefs — Rest of UK | amount £ | schema 0..1 |
| G100C | Total of deductions and reliefs — Total | amount £ | schema 1..1; = CT600 box 295; rules 9586, 9587, 9588, 9589, 9590 |
| G105A | Profits before qualifying donations and group relief — Northern Ireland | amount £ | schema 0..1 |
| G105B | Profits before qualifying donations and group relief — Rest of UK | amount £ | schema 0..1 |
| G105C | Profits before qualifying donations and group relief — Total | amount £ | schema 1..1; = CT600 box 300; rules 9591, 9592, 9593, 9594, 9595 |
| G110A | Qualifying donations — Northern Ireland | amount £ | schema 0..1 |
| G110B | Qualifying donations — Rest of UK | amount £ | schema 0..1 |
| G110C | Qualifying donations — Total | amount £ | schema 1..1; = CT600 box 305; rules 9596, 9597, 9598, 9599 |
| G115A | Group relief — Northern Ireland | amount £ | schema 0..1 |
| G115B | Group relief — Rest of UK | amount £ | schema 0..1 |
| G115C | Group relief — Total | amount £ | schema 1..1; = CT600 box 310; rules 9701, 9702, 9703, 9704 |
| G117A | Group relief for carried forward losses — Northern Ireland | amount £ | schema 0..1 |
| G117B | Group relief for carried forward losses — Rest of UK | amount £ | schema 0..1 |
| G117C | Group relief for carried forward losses — Total | amount £ | schema 1..1; = CT600 box 312; rules 9705, 9706, 9707, 9708 |
| G120A | Profits chargeable to corporation tax — Northern Ireland | amount £ | schema 0..1 |
| G120B | Profits chargeable to corporation tax — Rest of UK | amount £ | schema 0..1 |
| G120C | Profits chargeable to corporation tax — Total | amount £ | schema 1..1; = CT600 box 315; rules 9709, 9808, 9809, 9810 |
| G125A | Research and Development credit — Northern Ireland | amount £p | schema 0..1 |
| G125B | Research and Development credit — Rest of UK | amount £p | schema 0..1 |
| G125C | Research and Development credit — Total | amount £p | schema 1..1; = CT600 box 530; rules 9820, 9821, 9822, 9823 |
| G130A | Creative tax credit — Northern Ireland | amount £p | schema 0..1 |
| G130B | Creative tax credit — Rest of UK | amount £p | schema 0..1 |
| G130C | Creative tax credit — Total | amount £p | schema 1..1; = CT600 box 540; rules 9824, 9825, 9826, 9827 |
| G135A | Total of Research and Development credit or creative tax credit — Northern Ireland | amount £p | schema 0..1 |
| G135B | Total of Research and Development credit or creative tax credit — Rest of UK | amount £p | schema 0..1 |
| G135C | Total of Research and Development credit or creative tax credit — Total | amount £p | schema 1..1; = CT600 box 545; rules 9828, 9829, 9830, 9831, 9832 |
| G140A | Land remediation tax credit — Northern Ireland | amount £p | schema 0..1 |
| G140B | Land remediation tax credit — Rest of UK | amount £p | schema 0..1 |
| G140C | Land remediation tax credit — Total | amount £p | schema 1..1; = CT600 box 550; rules 9833, 9834, 9835, 9957 |
| G145B | Life assurance company tax credit — Rest of UK | amount £p | schema 1..1 |
| G145C | Life assurance company tax credit — Total | amount £p | schema 1..1; = CT600 box 555; rules 9958, 9959, 9960 |
| G150A | Total land remediation and life assurance company tax credit — Northern Ireland | amount £p | schema 0..1; rules 9962 |
| G150B | Total land remediation and life assurance company tax credit — Rest of UK | amount £p | schema 0..1 |
| G150C | Total land remediation and life assurance company tax credit — Total | amount £p | schema 1..1; = CT600 box 560; rules 9963, 9967, 9968, 9969, 9964 |
| G155A | Capital allowances first-year tax credit — Northern Ireland | amount £p | schema 0..1 |
| G155B | Capital allowances first-year tax credit — Rest of UK | amount £p | schema 0..1 |
| G155C | Capital allowances first-year tax credit — Total | amount £p | schema 1..1; = CT600 box 565; rules 9972, 9977, 9978, 9979 |
| G165A | Losses of trades carried on wholly or partly in the UK — Northern Ireland | amount £ | schema 0..1 |
| G165B | Losses of trades carried on wholly or partly in the UK — Rest of UK | amount £ | schema 0..1 |
| G165C | Losses of trades carried on wholly or partly in the UK — Total | amount £ | schema 1..1; = CT600 box 780 ('Arising' element of 780/785); rules 9980, 9981, 9982, 9983 |
| G170B | Losses of trades carried on wholly outside the UK — Rest of UK | amount £ | schema 1..1 |
| G170C | Losses of trades carried on wholly outside the UK — Total | amount £ | schema 1..1; = CT600 box 790; rules 9984, 9985, 9986 |
| G175 | Back-office activities | tick (X) | schema 0..1; rules 9987 |
| G180 | Pre-commencement assets | tick (X) | schema 0..1 |
| G185 | SME election into large company regime | tick (X) | schema 0..1; rules 9988 |

Groups (all 0..1 unless stated): `Trading` (G5–G20), `TotalProfits` (G25, G30; G30 group 1..1 inside), `ProfitsBeforeDeductions` (G35–G45; G45 1..1 inside), `DeductionsAndReliefs` (G50–G120), `TaxReconciliation` (G125–G155), `LossesDeficitsAndExcess` (G165–G170), `Indicators` (G175–G185). Several lines have no A column (G15, G25, G35, G40, G85, G93, G145, G170): those amounts can only be rest-of-UK by construction.

- **Calculations and rules**
  - Every "C" total = A + B (rules listed in table) and = the corresponding CT600 box (table "= CT600 box n").
  - Within the page: `G20C = G5C − G10C` (9255); `G45A = G30A` (9095); `G45B = G30B − (G35B + G40B)` (9096); `G45C = G30C − (G35C + G40C)` (9280); `G100C = G50C+G55C+G60C+G65C+G70C+G73C+G75C+G80C+G92C+G95C` (9588); `G105C = G45C − G100C` (9593); `G120C = G105C − (G110C + G115C + G117C)` (9808); `G135C = G125C + G130C` (9830); `G150C = G140C + G145C` (9968); `G150A = G140A` (9962).
  - Implied (no explicit rule): `G30C = G20C + G25C`, i.e. G30C = CT600 boxes 165+170+…+220; `G120A` is the NI profits figure that would populate CT600 box 325.
  - "value" vs "amount used" pairs (G10/G15, G80/G85, G92/G93): "value" = the deduction given (restricted deduction under s357JJ when NI losses are used against mainstream profits); "amount used" = the loss actually consumed. Interpretation inferred from the descriptions and s357JC/s357JJ — not documented by HMRC.
  - **Tax**: NI profits charged at the NI rate, rest at main/small profits rate (s357JA); in the main return this appears as separate lines in the FY1/FY2 tax calculation (boxes 330–425) using schema parameter `[CT RATE FOR NI TRADING PROFITS]` (rules 9200/9201/9143/9145 etc.), and CT600 box 586 "NI Corporation Tax included" must be completed when that rate differs from all other rates and is used (9147/9156).
  - CFC charge ignores the NI rate (TIOPA 2010 s371BC(4)).

- **Main-return linkage** (all dormant)
  - CT600 **box 125** "Northern Ireland – form CT600G" tick. N101 present ⇒ 125 = yes (9183); 125 = yes ⇒ N101 present (9133).
  - CT600 **boxes 5–8** (NI trading activity, SME, NI employer, Special circumstances; `CT_YesType`): group N009 only if box 35 ≥ **2050-04-01** (9102). Box 125 required if box 5 and none of 6/7/8 (9014) or if box 8 (9108); forbidden if 6 or 7 without 8 (9128) or without box 5 (9131); box 7 ⇒ box 6 (9107). So CT600G is needed for large companies / special circumstances, not for SME NI employers (who use boxes 6+7 only).
  - **Box 325** "Northern Ireland profits included": only with box 5 (9138); ≤ box 315 (9139).
  - **Box 586** "NI Corporation Tax included" (£p): only with box 5 (9142); required when the NI rate is used (9147/9156).
  - **Boxes 856/857/858** (group relief relating to NI losses vs rest-of-UK/mainstream profits, NI vs NI, mainstream losses vs NI profits; whole £): group N203 only if box 35 ≥ 2050-04-01 (9162); each requires box 310 (9163–9165).
  - **CT600C C46** "Trading losses - Northern Ireland" (≤ C45, requires box 5: 9177/9168) and **C161** "Trading losses carried forward - Northern Ireland" (≤ C160, requires box 5: 9182/9181).
  - Box 280 + box 125 ⇒ G90 required (9135); G90 ⇒ box 280 (9576).
  - Every G "C" total must equal its CT600 box: 155, 160, 165, 225, 230, 235, 240, 245, 250, 255, 260, 263, 265, 275, 285, 290, 295, 300, 305, 310, 312, 315, 530, 540, 545, 550, 555, 560, 565, 780 ('Arising' element), 790.

- **Key schema validation rules** (see table for per-box codes)
  - Dormancy gates: 9102 and 9162 (period end ≥ 2050-04-01) make boxes 5–8 and 856–858 unusable today; via 9131, box 125 (and therefore CT600G) cannot be submitted either.
  - Presence chains: 9184 (G5C > 0 ⇒ G20C), 9266 (G30C > 0 ⇒ G45C), 9295 (G45C > 0 ⇒ G105C), 9297 (any deduction ⇒ G100C), 9298 (G105C > 0 ⇒ G120C), 9811/9812 (credit subtotals).
  - Each C total "can only be completed if Box nnn is completed", "can only be completed if Box GxxA or GxxB are completed", "must equal the sum of A and B", "must equal Box nnn".
  - Date/indicator: 9414 G155 only if box 30 ≤ 2020-03-31 (first-year tax credits ended); 9987 G175 and 9988 G185 require box 8.
  - Indicator meanings (inferred from Part 8B): G175 back-office activities election (s357KB(2)); G180 pre-commencement assets (intangible fixed assets transitional rules, Part 8B Ch 8; draft guidance NICT06120); G185 SME election into the large-company regime (s357KA(2A)).

- **Worked example**: not provided — no NI rate exists, so any figure would be fictitious. Validators should treat any NI box or a CT600G on a period ending before 2050-04-01 as an error (9102/9162/9131).

- **Unverified / caveats**
  - Box labels are schema descriptions; a real CT600G form (if ever published) may word them differently and may add G1–G4 company-information boxes.
  - The 2050-04-01 gate is a placeholder in the schema; it will change if a rate is ever appointed. Do not hard-code the date outside the schema-rules layer.
  - Absence of a commencement SI is based on a legislation.gov.uk search on 2026-09-28 and on the CT600 guide (updated 2026-06-02) still saying there is no NI rate.
  - Meanings of G180 and the "value"/"amount used" pairs are inferred, not documented by HMRC.

---

## CT600H — Company Tax Return – supplementary page: Cross-border Royalties

- **Form version(s)**: `CT600H (2015) Version 3 for accounting periods starting on or after 1 April 2015`; footer `CT600H(2015) Version 3 Page 1/2 HMRC 04/15`. Two pages: company info, then the payments table.
  - Local file: `downloads/CT600H_2015.pdf` (text: `text/CT600H_2015.txt`). MD5 matches the live gov.uk asset (checked 2026-09-28).
  - Publication: https://www.gov.uk/government/publications/corporation-tax-cross-border-royalties-ct600h-2015-version-3 (asset https://assets.publishing.service.gov.uk/media/5a80341aed915d74e33f90fd/CT600H_2015.pdf; page updated 2025-04-01, links only).
  - Guidance: https://www.gov.uk/guidance/supplementary-pages-ct600h-cross-border-royalties (updated 2024-01-02).
  - XML: `CompanyTaxReturn/CrossBorderRoyalties` (type `CTH`), schema v1.995.
  - Applicability: APs starting on or after 1 April 2015. It is still current.
- **Purpose / who must file**
  - Complete it if a UK company (or the UK permanent establishment of a foreign company) made cross-border royalty payments after 1 October 2002 and **reasonably believed the recipient would be entitled to treaty relief**. The payment was then made gross or at the treaty rate instead of the full rate (guidance).
  - Duty to deduct: ITA 2007 Part 15 Ch 6 s903 ("Deduction from patent royalties") and Ch 7 s906 ("Certain royalties etc where usual place of abode of owner is abroad"), at the basic rate of 20%.
  - Treaty-rate deduction: **ITA 2007 s911** ("Double taxation arrangements: deduction at treaty rate", https://www.legislation.gov.uk/ukpga/2007/3/section/911). A company that *reasonably believes* the payee is entitled to DTA relief may deduct at the treaty rate. If the belief is wrong, the relief is retrospectively lost (s911(3)).
  - **EU Interest and Royalties Directive route abolished**: ITA 2007 ss914–917 ("discretion to make royalty payments gross") and ITTOIA 2005 ss757–767 were repealed by **FA 2021 s34** (https://www.legislation.gov.uk/ukpga/2021/26/section/34), for payments on or after **1 June 2021**, and from 3 March 2021 in "disqualifying circumstances". Option (a) of column E is therefore only relevant to earlier payments.
  - HMRC manuals: INTM630000 Royalty Withholding (https://www.gov.uk/hmrc-internal-manuals/international-manual/intm630000) and INTM400000 Interest and Royalty Payments, the historical IRD material (https://www.gov.uk/hmrc-internal-manuals/international-manual/intm400000). The tax deducted is accounted for quarterly on form CT61 (ITA 2007 Part 15 Ch 15), not on the CT600.

### Box table

| Box | Label (verbatim from form) | Type | Notes / calculation |
|---|---|---|---|
| H1 | Company name | text | Paper only. Not in CTH XML; comes from CT600 box 1. |
| H2 | Tax reference | text (10-digit UTR) | Paper only. Comes from CT600 box 3. |
| H3 | from DD MM YYYY | date | Period covered by this supplementary page (cannot exceed 12 months). Comes from CT600 box 30. |
| H4 | to DD MM YYYY | date | Comes from CT600 box 35. |
| H5 | Details of payments made | repeating table, **1..∞** (`[ROYALTIES]` `CTH/Royalties`) | The paper form has 9 rows; the XML is unbounded. One row per royalty recipient/payment. Columns follow. |
| H5A | Name of recipient of the royalty | text | `RecipientName`, 1..1, `CTexcludedCharsStringType`, length 2–56. Must match the CT charset `[A-Za-z0-9 ,.()/&'-"!%*_+:@<>?=;]` and must not contain `£$#~€`. |
| H5B | Full address of recipient of the royalty | text (address) | `AddressOfRecipient`, 1..1, `CTaddressStructure`: 2–3 `Line` (each ≤28 chars), optional `AdditionalLine` (≤18), optional `PostCode` (≤8). |
| H5C | Type of royalty payment made | text | `PaymentType`, 1..1, 2–56 chars. |
| H5D | Gross amount of royalty paid | amount £ (whole pounds, **> 0**) | `Amount`, 1..1, `CT_CTnonZeroWholePoundStructure`. The paper column shows £ only. |
| H5E | Agreement under which relief claimed* | text, choice of one | `RoyaltiesAgreement`, 1..1. Footnote: "*(a) Interest and Royalties Directive or (b) country with Double Taxation Agreement with UK". |
| H5Ea | (a) Interest and Royalties Directive | text | `RoyaltiesAgreement/InterestAndRoyalties`, 2–56 chars. XSD `choice`: Ea **xor** Eb. Obsolete for payments on or after 1 Jun 2021 (FA 2021 s34). |
| H5Eb | (b) country with Double Taxation Agreement with UK | text | `RoyaltiesAgreement/DoubleTaxationAgreement`, 2–56 chars. Guidance: "enter the name of the country with the Double Taxation Agreement with the UK". |
| H5F | Rate of tax deducted from payment % | % (decimal, exactly 2 dp, 0.00–100.00) | `DeductionRate`, 1..1, `CT_IRnonNegativeDecimalType`, e.g. `10.00`; `0.00` for a gross payment. |
| H5G | Amount of tax deducted from payment | amount £p | `DeductionAmount`, 1..1, `CTpoundPenceStructure` (≥0, ≤99,999,999,999.99). Must equal H5D × H5F / 100, rounded (rule 9750). |
| H5H | Additional notes | text | `AdditionalNotes`, **0..1**, 2–56 chars. |

Form-vs-schema notes:
- The paper column letters A–H map to H5A–H5H.
- The schema splits E into Ea and Eb as an exclusive choice.
- The paper page shows no box for the row total. There is **no total box**.

### Calculations and rules

- **Per row**: `H5G = round_half_up(H5D × H5F / 100, 2)` (rule 9750). The schematron computes `round(Amount × rate×100 / 100) / 100` with XPath `round()`, i.e. half-up to the penny.
- **Rate to enter**: the treaty rate under s911 when a DTA claim is made (e.g. 0.00, 5.00, 10.00 or 15.00 depending on the treaty royalties article). Without treaty relief, tax is deducted at the basic rate of 20% (ITA 2007 s903(5)–(6) for patent royalties; s906 for other IP royalties).
- **Scope vs box 645**: box 645 ("has made cross-border royalty payments") is ticked for *any* royalty paid overseas, whether paid gross or at a DTA rate under s911, or gross under the former IRD (main guide). CT600H itself is only mandatory where treaty or IRD relief was applied. The schema enforces only 130 ⇒ 645, not 645 ⇒ 130.
- **Penalty and direction cites in the guidance are stale**: ICTA 1988 s349E is superseded by ITA 2007 ss911–912, and TMA 1970 s98(4DA) was repealed by FA 2021 s34(2). The current direction power is ITA 2007 s912 ("Power to make directions disapplying section 911").

### Main-return linkage

| CT600 box | Label | Link |
|---|---|---|
| 130 | Cross-border royalties – form CT600H | Tick (`SupplementaryPages/CT600H`). |
| 645 | has made cross-border royalty payments | Tick (`IndicatorsAndInformation/CrossBorderRoyalty`). Must be `yes` whenever 130 is `yes` (rule 9130). |

No CT600 amount box is fed by CT600H. Royalty tax deducted is reported and paid via CT61, not in boxes 515 or 595.

### Key schema validation rules (v1.995)

- **9129**: `[130]='yes'` on a New return → CTH (`[N102]`) must be present.
- **9312**: CTH present → `[130]='yes'`.
- **9130**: `[130]='yes'` → `[645]='yes'`.
- **9750**: for each `[ROYALTIES]` row, `[H5G] = [H5D] × [H5F]/100` rounded to the nearest penny, half up.
- XSD facets: H5D > 0 (non-zero whole pounds); H5F 0.00–100.00 with 2 dp; H5E is an exclusive choice; at least one `Royalties` row.

### Worked example

UK Co pays a £250,000 software/know-how royalty to a US parent. It reasonably believes the US–UK DTA gives a 0% rate. It also pays a £40,000 royalty to an Indian licensor at the 15% treaty rate (illustrative rates; check the treaty).

| Row | H5A | H5C | H5D | H5Eb | H5F | H5G |
|---|---|---|---|---|---|---|
| 1 | US Parent Inc | Software licence royalty | 250000 | United States | 0.00 | 0.00 |
| 2 | Licensor Pvt Ltd | Patent royalty | 40000 | India | 15.00 | 6000.00 |

Row 2 check: 40,000 × 15.00/100 = 6,000.00, which satisfies rule 9750. On the CT600, boxes 130 and 645 are both ticked. The £6,000 is paid over via CT61.

### Unverified / caveats

- Treaty rates in the example are illustrative only. The s906 subsection text was not re-fetched; s903(5)–(6) was checked on legislation.gov.uk.
- The guidance still describes the IRD route and ICTA s349E. Software should warn if option (a) is used for a payment dated on or after 2021-06-01. The schema does **not** enforce this.
- H3/H4 give a period, but there is no per-payment date field. Payments are only implicitly within the AP.

---

## CT600I — Company Tax Return – supplementary page: Supplementary charge in respect of ring fence trades

- **Form version(s)**: `CT600I (2019) Version 3 for accounting periods starting on or after 1 April 2015`; footer `CT600I(2019) Version 3 Page 1/2/3 HMRC 04/19`. Three pages: company info; calculation; transferred tax history (TTH).
  - Local file: `downloads/CT600I_2019_v0_9.pdf` (text: `text/CT600I_2019_v0_9.txt`). The asset file name says "v0_9" but the printed version is "(2019) Version 3". MD5 matches the live gov.uk asset (checked 2026-09-28).
  - Publication: https://www.gov.uk/government/publications/corporation-tax-supplementary-charge-in-respect-of-ring-fence-trades-ct600i-2015-version-3 (asset https://assets.publishing.service.gov.uk/media/5c88c1a1ed915d50ae3f2a72/CT600I_2019_v0_9.pdf; page updated 2025-04-01, links only). The slug still says "2015-version-3".
  - Guidance: https://www.gov.uk/guidance/supplementary-pages-ct600i-supplementary-charge-in-respect-of-ring-fence-trades (updated 2024-01-02).
  - XML: `CompanyTaxReturn/RingFenceTrade` (type `CTI`), schema v1.995.
  - Applicability: APs starting on or after 1 April 2015. The 2019 edition added the TTH page (I90–I160).
- **Purpose / who must file**
  - Complete it for any period beginning (or deemed to begin) on or after 17 April 2002 in which the company carried on a **production ring fence trade** under CTA 2010 Part 8 (s274 oil extraction activities / oil rights; s277 separate trade). Source: guidance.
  - **Do not** complete it for a contractor ring fence under Part 8ZA. The main guide says so for boxes 320, 585, 590 and CT600I.
  - **Supplementary charge (SC)**: CTA 2010 **s330(1)** charges "a sum equal to **10%** of its adjusted ring fence profits" as if it were corporation tax (https://www.legislation.gov.uk/ukpga/2010/4/section/330, checked 2026-09-28). Rate history (OT21202, https://www.gov.uk/hmrc-internal-manuals/oil-taxation-manual/ot21202):
    - 10% from 17 Apr 2002
    - 20% for APs beginning on or after 1 Jan 2006
    - 32% from 24 Mar 2011
    - 20% from 1 Jan 2015 (FA 2015 s48)
    - **10% for APs beginning on or after 1 Jan 2016 (FA 2016 s58)**. Confirmed current.
  - **Adjusted ring fence profits** (s330(2)–(3)): ring fence profits computed on the assumption that **financing costs are left out of account**, both in the trade profit/loss and in any loss relief surrendered to the company under s305(1). Financing costs are defined in s331. Further adjustments for decommissioning are in s330A and s330B. Manual: OT21195 onward (https://www.gov.uk/hmrc-internal-manuals/oil-taxation-manual/ot21195).
  - **SC-reducing allowances** (all reported in I60), with ordering chosen by the company under s330ZA:
    - Ch 6A investment allowance (s332A onward; OT21550)
    - Ch 7 field allowance ("reduction of supplementary charge for eligible oil fields", s333 onward; OT21400)
    - Ch 8 onshore allowance (s356C onward; OT21500)
    - Ch 9 cluster area allowance (s356JA onward)
  - **Transferable tax history (TTH)**: available for licence sales approved on or after 1 Nov 2018 by joint election under FA 2019 Sch 15 (OT60000, https://www.gov.uk/hmrc-internal-manuals/oil-taxation-manual/ot60000). The guidance says boxes I90–I160 "do not form part of the company's tax return", but they are in the XML.

### Box table

| Box | Label (verbatim from form) | Type | Notes / calculation |
|---|---|---|---|
| I1 | Company name | text | Paper only; comes from CT600 box 1. |
| I2 | Tax reference | text | Paper only; comes from CT600 box 3. |
| I3 | from DD MM YYYY | date | Period covered by this supplementary page (cannot exceed 12 months). Comes from box 30. |
| I4 | to DD MM YYYY | date | Comes from box 35. |
| **Calculation of supplementary charge** | | | `[SI021]` `CalculationOfSupplementaryCharge`, 1..1 |
| I5 | Ring fence profits or losses of ring fence trade | amount £ (whole, ≥0) | `Trade/Amount`, 1..1, `CTwholePoundStructure`. Magnitude only; the sign is carried by I10/I15. Figure is after group relief surrendered to the company and set against RF profits, but **before** losses brought forward or carried back. |
| I10 | If entry in I5 is Profits – put an 'X' in box I10 | tick (X) | `Trade/Profits` `CT_YesType`. XSD **choice** with I15: exactly one of I10 or I15. |
| I15 | If entry in I5 is Losses – put an 'X' in box I15 | tick (X) | `Trade/Losses`. |
| I20 | Disallowed financing costs – relating to the company itself | amount £ (whole, >0) | `DisallowedFinancingCosts/RelatedToCompany`, 0..1, non-zero. |
| I25 | relating to loss relief surrendered to the company | amount £ (whole, >0) | `.../RelatedToLossRelief`, 0..1, non-zero. |
| I30 | Total disallowed finance costs — box I20 plus I25 | amount £ | `.../Total`, 1..1 within the optional `[DISALLOWEDFINANCINGCOSTS]` group. |
| I35 | Adjusted ring fence profits — enter '0' if a loss — box I5 adjusted by I30 | amount £ | `Profits`, 1..1. |
| I40 | Decommissioning adjustment | amount £ | `DecommissioningAdjustment`, 0..1. CTA 2010 s330A increase. Applies only while the SC rate is above 20%, so nil at 10%. |
| I45 | Revised ring fence profits — box I35 adjusted by I40 | amount £ | `RevisedProfits`, 0..1. **Must be supplied** whenever I65 > 0, because rule 9817 sums I45 as 0 if absent. |
| I50 | Less — Losses brought forward or from a later accounting period | amount £ (>0) | `MinusLosses`, 0..1, non-zero. Losses recomputed with financing costs left out (s330(3)); s37 carry-backs are included. |
| I55 | Decommissioning reduction | amount £ | `DecommissioningReduction`, 0..1. s330B. Only relevant at an SC rate above 20%. Do not exceed the amount needed to reduce I65 to nil. |
| I60 | Field allowance | amount £ | `FieldAllowance`, 0..1. Includes investment, onshore, cluster area and HPHT cluster allowances. |
| I65 | Net profits subject to ring fence charge — box I45 minus boxes I50 to I60 | amount £ | `NetProfits`, 1..1. |
| I70 | Tax at supplementary charge rate – copy the figure to box 505 on form CT600 | amount £p (>0) | `Tax`, 0..1, `CT_CTnonZeroPoundPenceStructure`. **Omit if I65 = 0**; required if I65 > 0. |
| **Losses (where appropriate)** | | | |
| I75 | Ring fence trade losses arising in period | amount £ (>0) | `LossesArising`, 0..1, non-zero. Loss computed on the s330(3) assumption, i.e. excluding finance costs. |
| **Net ring fence trade** | | | `[SI020]` `NetRingFenceTrade`, 0..1 |
| I80 | Ring fence Corporation Tax – enter figure net of any deductions in terms of tax. Copy the figure to box 585 on CT600 | amount £p | `RingFenceCorpTaxIncluded`, 0..1. |
| I85 | Supplementary charge tax — enter figure net of any deductions in terms of tax. Copy the figure to box 590 on CT600 | amount £p | `SupplementaryChargeTax`, 0..1. |
| **Transferred tax history** | | | `[TRANSFERREDTAXHISTORY]`, 0..1; contains `[ELECTIONTOTRANSFER]` 1..1 |
| I90 | An election to transfer tax history has been made in the period covered by this return – put an 'X' in the appropriate box(es) — Asset(s) acquired | tick (X) | `AssetAcquiredThisPeriod`, 0..1. |
| I95 | (same) — Asset(s) disposed of | tick (X) | `AssetDisposedOfThisPeriod`, 0..1. |
| I100 | An election to transfer tax history has been made in a previous accounting period – put an 'X' in the appropriate box(es) — Asset(s) acquired | tick (X) | `AssetAcquiredPreviousPeriod`, 0..1. |
| I105 | (same) — Asset(s) disposed of | tick (X) | `AssetDisposedOfPreviousPeriod`, 0..1. |
| **Asset information and tracking (complete boxes I110 – I160 for each asset acquired)** | | repeating group **0..999** | `[ASSETINFORMATION]`. The paper form has one block; the guidance says to "enclose an additional sheet" for more. |
| I110 | Description of asset | text (≤300) | `DescriptionOfAsset`, 1..1. The name of the acquired field. |
| I115 | Asset reference | text, pattern `[A-Z]{6}[0-9]{3}` | `AssetReference`, 1..1. HMRC-issued. Must be unique in the submission (rule 9475). |
| I120 | Put an 'X' in box I120 if OGA has approved the cessation of production | tick (X) | 0..1. The OGA is now the NSTA. |
| I125 | Put an 'X' in box I125 if STO certification of tracking is qualified | tick (X) | 0..1 (Senior Tracking Officer; FA 2019 Sch 15 Part 9). |
| **Tracking of transferred tax history** | | | `[TRACKINGOFTRANSFERREDTAXHISTORY]`, 1..1 per asset |
| I130 | Put an 'X' in box I130 if a detailed schedule of the accounting periods and rates applying is included in the tax computations | tick (X) | 0..1. |
| I135 | Transferred tax history – Ring fence corporation tax | group, 1..1 | Each column is a `CT_ProfitsTaxStructure` pair: Profits = £ whole; Tax = £p. The paper form shows £ for both. |
| I135A | A Amount brought forward or acquired — Profits / Tax | amount £ / £p | 1..1 |
| I135B | B Amount transferred — Profits / Tax | amount £ / £p | 0..1 |
| I135C | C Amount used this period — Profits / Tax | amount £ / £p | 0..1 |
| I135D | D Amount carried forward — Profits / Tax | amount £ / £p | 1..1; = A − B − C for each component. |
| I140 | Transferred tax history – Supplementary charge | group, **0..1** | Same columns: I140A (1..1), I140B (0..1), I140C (0..1), I140D (1..1). |
| I140A | A Amount brought forward or acquired — Profits / Tax | amount £ / £p | |
| I140B | B Amount transferred — Profits / Tax | amount £ / £p | Requires I135B. |
| I140C | C Amount used this period — Profits / Tax | amount £ / £p | Requires I135C. |
| I140D | D Amount carried forward — Profits / Tax | amount £ / £p | = A − B − C. |
| I145 | Tracked profits or losses | group, 1..1 | `CT_ProfitsLossesStructure` = **choice** of Profits (£ ≥0) **or** Losses (£ >0). |
| I145A | A Balance brought forward — Profits / Losses | amount £ (choice) | 0..1 |
| I145B | B Profits/losses for this period — Profits / Losses | amount £ (choice) | 1..1 |
| I145C1 | C Other adjustments — Plus (+) | amount £ | XSD **choice** with C2: only one may be given, although the paper form shows both. |
| I145C2 | C Other adjustments — Minus (–) | amount £ | |
| I145D | D Amount carried forward — Profits / Losses | amount £ (choice) | 1..1 |
| I150 | Decommissioning expenditure | group, 0..1 | |
| I150A | A Balance brought forward | amount £ | 0..1 |
| I150B | B Expenditure for this period | amount £ | 0..1 |
| I150C1 | C Other adjustments — Plus (+) | amount £ | Choice with C2. |
| I150C2 | C Other adjustments — Minus (–) | amount £ | |
| I150D | D Amount carried forward | amount £ | 1..1 |
| I155 | Activated TTH – Ring fence | group, 0..1 | Profits/Tax pairs. |
| I155A | A Previously activated — Profits / Tax | amount £ / £p | 0..1 |
| I155B | B Activated this period — Profits / Tax | amount £ / £p | 0..1 |
| I155C | C Total activated — Profits / Tax | amount £ / £p | 1..1 |
| I155D | D Total used — Profits / Tax | amount £ / £p | 0..1 |
| I160 | Activated TTH – Supplementary charge | group, 0..1 | I160A–D mirror I155A–D and each requires its I155 counterpart. |
| I160A | A Previously activated — Profits / Tax | amount £ / £p | 0..1 |
| I160B | B Activated this period — Profits / Tax | amount £ / £p | 0..1 |
| I160C | C Total activated — Profits / Tax | amount £ / £p | 1..1 |
| I160D | D Total used — Profits / Tax | amount £ / £p | 0..1 |

### Calculations and rules

**SC computation (model):**
- `I30 = I20 + I25` (absent = 0).
- If I10 (profit): `I35 = I5 + I30`.
- If I15 (loss): `I35 = max(I30 − I5, 0)` (rules 9803 and 9804).
- `I45 = I35 ± I40`. At a 10% rate, I40 = 0, so I45 = I35.
- `I65 = I45 − (I50 + I55 + I60)` (rule 9817).
- Constraints: `I50 ≤ I35` (rule 9805); `I60 ≤ I35 − I50` (rule 9816). The guidance adds "cannot exceed I45" for I50 and "not greater than needed to reduce I65 to nil" for I55/I60.
- **Negative net financing costs** (i.e. net finance income within the RF profits) are *subtracted*, and the guidance says to enter that adjustment in **I50** (OT21220–OT21222).
- **I70**:
  - No rate change in the AP: `I70 = I65 × rate` (rule 9818). Rate = **10%** for APs on or after 2016-01-01. The schematron constant is 0.10 from 2016-01-01 and 0.20 for 2015-01-01 to 2015-12-31.
  - Rate change in the AP (only the 31 Dec 2015 / 1 Jan 2016 boundary is coded): `part1 = round_half_up_to_£(I65 × days(from box 30 to 2015-12-31 inclusive) / days(AP))`, `part2 = I65 − part1`, and `I70 = part1 × 20% + part2 × 10%` (rule 9819). The statute allows a just-and-reasonable election instead of time apportionment (guidance).
- **I75** is required where I15 is ticked and `I5 − I20 > 0` (rule 9801), i.e. a loss still remains after removing company finance costs.
- **I80 / I85** hold RFCT (CTA 2010 s279A: main ring fence profits rate **30%**, small ring fence profits rate 19%) and SC, each **net of any deduction in terms of tax** shown after box 510 on the CT600 (e.g. box 515 income tax suffered).
  - They exist because large-company RFCT and SC (and EPL) are paid in **3 instalments** instead of the 4 used for other CT (APs ending on or after 1 Jul 2005; OT21300, https://www.gov.uk/hmrc-internal-manuals/oil-taxation-manual/ot21300).
- **Box 320**: the production ring fence profits included in box 315, which are the profits charged at the RF rates in boxes 330+.
- **TTH arithmetic**:
  - I135D = I135A − I135B − I135C, separately for Profits and Tax (rules 9476 and 9477). Same for I140 (rules 9480 and 9481).
  - I145D = A + B + C1 − C2, with profits positive and losses negative (rule 9482).
  - I150D = A + B + C1 − C2 (rule 9484).
  - I155C = A + B for each component (rules 9486 and 9487), and I155D ≤ I155C (rules 9488 and 9489).
  - TTH is **activated** when cumulative decommissioning expenditure on the asset (I150) ≥ cumulative net tracked profits (I145); see OT64000.
- **Energy (Oil and Gas) Profits Levy (EPL)** is **not** on CT600I.
  - It is reported on the CT600 as box **986** "Energy (Oil and Gas) Profits Levy (EOGPL) amounts liable" (£ whole) and box **501** "EOGPL payable" (£p). 501 is part of box 510.
  - Legislation: Energy (Oil and Gas) Profits Levy Act 2022 (c. 40) s1 (https://www.legislation.gov.uk/ukpga/2022/40/section/1, checked 2026-09-28): "a sum equal to **38%** of its levy profits", for qualifying APs beginning on or after 26 May 2022 and ending on or before **31 March 2030**. Levy profits = RF profits with financing *and decommissioning* costs left out, plus investment expenditure uplift, and no loss or group relief.
  - Rate history: **25%** from 26 May 2022 to 31 Dec 2022; **35%** from **1 Jan 2023**; **38%** from **1 Nov 2024**. Sources: https://www.gov.uk/government/publications/changes-to-the-energy-oil-and-gas-profits-levy/energy-oil-and-gas-profits-levy and https://www.gov.uk/government/publications/energy-profits-levy-reforms-2024/energy-profits-levy-reforms-2024. The 2024 reforms also removed the 29% EPL investment allowance and cut the decarbonisation allowance to 66%.
  - Straddling APs are split into separate periods (EPLA 2022 ss15–16; OT21710). EPL is treated as CT for administration and paid in the same 3 instalments (OT21805).

### Main-return linkage

| CT600 box | Label (CT600 (2026) v3) | Link |
|---|---|---|
| 135 | Supplementary charge in respect of ring fence trades – form CT600I | Tick. |
| 320 | Ring fence profits included | Production RF profits within box 315. Only allowed if 135 is ticked (or the return is amended). |
| 505 | Supplementary charge (ring fence trades) payable | = **I70** (rule 9807 / SI010.0). Included in 510. |
| 585 | Ring fence Corporation Tax included | = **I80** (rules 9813 and 9271); ≤ 525. |
| 590 | Ring fence supplementary charge included | = **I85** (rules 9814 and 9274); ≤ 505. |
| 435 | Marginal relief | Allowed if 135 is ticked or the AP ends on or after 2023-04-01 (rule 9350). This covers ring fence marginal relief. |
| 986 / 501 | EOGPL amounts liable / EOGPL payable | EPL. Separate from CT600I, but the same RF trade. |

### Key schema validation rules (v1.995)

- **Presence**: 9132 (135 on a New return → CTI present); 9313 (CTI → 135); 9254 (505 only if 135, New); 9269 (585 only if 135); 9273 (590 only if 135); 9956 (320 only if 135 or Amended); 9190 (320 ≤ 315).
- **Calculation**: 9802 (I30 = I20 + I25); 9803 and 9804 (I35); 9805 (I50 ≤ I35); 9816 (I60 ≤ I35 − I50); 9817 (I65); 9800 (I70 required if I65 > 0); 9818 and 9819 (I70 rate); 9801 (I75).
- **Cross-page**: 9807 (505 = I70); 9813 (585 = I80); 9814 (590 = I85); 9271 and 9274 (reverse checks on New returns); 9270 (585 ≤ 525); 9272 (590 ≤ 505).
- **TTH**: 9328 and 9329 (I90 or I100 → at least one ASSETINFORMATION); 9330 (at least one of I90–I105); 9475 (I115 unique); 9476–9493 (arithmetic and dependency rules above).
- **XSD**: I10/I15 is an exclusive choice; I145C1/C2 and I150C1/C2 are exclusive choices; I70 > 0; I20, I25, I50 and I75 are non-zero if present; ASSETINFORMATION maxOccurs 999.

### Worked example

AP 1 Jan 2025 – 31 Dec 2025 (no SC rate change). Offshore producer.
- RF trade profit after group relief surrendered: £50,000,000 (I5, I10 X).
- Company's own financing costs deducted in that profit: £4,000,000.
- CT RF loss b/f: £13,000,000. The same loss recomputed without finance costs is £10,000,000.
- Investment allowance activated: £6,000,000.

| Box | Value | Working |
|---|---|---|
| I5 / I10 | 50000000 / X | |
| I20 | 4000000 | |
| I30 | 4000000 | I20 + I25 (I25 absent) |
| I35 | 54000000 | 50,000,000 + 4,000,000 |
| I45 | 54000000 | I40 nil at a 10% rate |
| I50 | 10000000 | ≤ I35 ✓ |
| I60 | 6000000 | ≤ I35 − I50 = 44,000,000 ✓ |
| I65 | 38000000 | 54,000,000 − 16,000,000 |
| I70 | 3800000.00 | 38,000,000 × 10% → **box 505** |
| CT600 315 / 320 | 37000000 / 37000000 | 50,000,000 − 13,000,000 (no other profits) |
| RFCT | 11100000.00 | 37,000,000 × 30% (boxes 330+ at the FULL RF rate) |
| I80 | 11100000.00 | → **box 585** (no box 515 deductions) |
| I85 | 3800000.00 | → **box 590** (≤ 505 ✓) |
| CT600 986 / 501 | 45000000 / 17100000.00 | EPL: illustrative levy profits × 38% |
| CT600 510 | 32000000.00 | 475 (11,100,000) + 501 (17,100,000) + 505 (3,800,000) |

Loss variant: RF loss £3,000,000 (I5 = 3000000, I15 X) and I20 = £1,000,000.
- I30 = 1,000,000.
- I35 = max(1,000,000 − 3,000,000, 0) = **0**.
- I65 = 0, so I70 is **omitted**.
- I75 is required (rule 9801: I5 − I20 = 2,000,000 > 0). I75 = 2,000,000, the loss with finance costs removed.

### Unverified / caveats

- **Schema vs parsed table**: `schema/CTI-boxes.txt` lists I10 and I15 both as 1..1. The XSD has them as a `choice`, so exactly one applies. The I145C1/C2 and I150C1/C2 pairs are likewise choices, although the paper form shows both columns.
- **Guidance typos**:
  - I65 is described as "I45 minus I50 to 165".
  - The TTH tick instructions say "I190/I195" where I90/I95 and I100/I105 are meant.
  - The 1 Jan 2016 transitional paragraph repeats "before 1 January 2015".
  - The rule 9804 English message says "If Box I5 is completed" but the logic applies when **I15** is ticked.
  - The guidance says I50 "cannot exceed I45"; the schema checks I50 ≤ **I35**.
- The schematron hard-codes only the 2015 and 2016 SC rates and the 2015-12-31 straddle. A future SC rate change would need a new schema release.
- The brief suggested "EPL 35% from 1 Nov 2023". Per the gov.uk policy papers it is **35% from 1 Jan 2023** and 38% from 1 Nov 2024. HMRC's OT21715 still says 35% (stale); the legislation reads 38%.
- Legislative section ranges for Chapters 8 and 9 (onshore and cluster allowances) are cited at chapter level only. The field allowance was replaced for new fields by the investment allowance (FA 2015), but existing field allowance can still be activated. Details not re-verified.
- The EPL levy-profit composition (investment expenditure uplift, decarbonisation allowance) is summarised, not modelled. See OT21700 onward.

---

## CT600J — Company Tax Return – supplementary page: Disclosure of tax avoidance schemes

- **Form version(s)**: `CT600J (2015) Version 3 for accounting periods starting on or after 1 April 2015`; footer `CT600J(2015) Version 3 Page 1 HMRC 04/15`. Single page.
  - Local file: `downloads/CT600J_2015.pdf` (text: `text/CT600J_2015.txt`). MD5 matches the live gov.uk asset (checked 2026-09-28).
  - Publication: https://www.gov.uk/government/publications/corporation-tax-disclosure-of-tax-avoidance-schemes-ct600j-2015-version-3 (asset https://assets.publishing.service.gov.uk/media/5a80293de5274a2e87db8360/CT600J_2015.pdf; page updated 2025-04-01, links only).
  - Guidance: https://www.gov.uk/guidance/supplementary-pages-ct600j-disclosure-of-tax-avoidance-schemes (updated 2024-01-02).
  - XML: `CompanyTaxReturn/TaxAvoidanceSchemes` (type `CTJ`), schema v1.995.
  - Applicability: APs starting on or after 1 April 2015. It is still current.
- **Purpose / who must file**
  - A party to **notifiable arrangements** (FA 2004 s306) who has an 8-digit **scheme reference number (SRN)** must report it. Reporting applies where the company entered into a transaction forming part of the arrangements in this or an earlier AP and expects a tax advantage (FA 2004 s318) in this or a later AP.
  - Statutory duty: **FA 2004 s313(1)** requires a party to provide "(a) any reference number notified to him, and (b) the time when he obtains or expects to obtain ... an advantage" (https://www.legislation.gov.uk/ukpga/2004/12/section/313). s313(3)(a) allows regulations to require this "in any return". Current regulations: Tax Avoidance Schemes (Information) Regulations 2012 (SI 2012/1836), as amended (latest 2021/980). The guidance still cites the revoked 2004 Regulations.
  - **Promoter reference numbers (PRN)**: FA 2014 **s253** (POTAS). A client notified of a PRN must report it "in ... each tax return" for a period in which it expects a tax advantage from relevant arrangements (https://www.legislation.gov.uk/ukpga/2014/26/section/253). The guidance says to use CT600J for PRNs (CT, IT, CGT, VAT and NIC advantages), but not for IHT, PRT, SDLT or SDRT.
  - **Use form AAG4 instead** when:
    - the return is filed late or was already filed without the SRN;
    - there are more SRNs than spaces on the return. The schema caps rows at 10; see https://www.gov.uk/guidance/forms-to-disclose-tax-avoidance-schemes.
    - For PRNs in these cases, use form AAG4(PRN).
  - Employment-related arrangements (s313ZC) are reported annually by the employer on **AAG8** instead.
  - **Penalties**:
    - TMA 1970 s98C(3): £5,000 per scheme, rising to £7,500 and then £10,000 per scheme for repeat failures within 36 months.
    - FA 2014 Sch 35 para 2(3): £5,000 / £7,500 / £10,000 for failure to report a PRN (s253).

### Box table

| Box | Label (verbatim from form) | Type | Notes / calculation |
|---|---|---|---|
| J1 | Company name | text | Paper only; not in CTJ XML. Comes from CT600 box 1. |
| J2 | Tax reference | text (10-digit UTR) | Paper only; comes from box 3. |
| J3 | from DD MM YYYY | date | Period covered by this supplementary page (cannot exceed 12 months). Comes from box 30. |
| J4 | to DD MM YYYY | date | Comes from box 35. |
| J5–J50 | Disclosure of tax avoidance schemes | repeating table **1..10** (`[AVOIDANCESCHEMES]` `CTJ/AvoidanceSchemes`) | The paper form has 10 fixed rows: J5/J5A, J10/J10A, J15/J15A … J50/J50A. XML uses one repeating element with columns J5 and J5A. |
| J5 (…J50) | Scheme reference number | text/integer, exactly 8 digits | `ReferenceNumber`, 1..1, `xsd:integer`, pattern `[0-9]{8}`, maxInclusive 99999999. |
| J5A (…J50A) | Accounting period in which the expected advantage arises DD/MM/YYYY | date | `AccountingPeriod`, 1..1, `CT_DateType` (YYYY-MM-DD). Enter the **last day** of the AP in which the tax advantage is expected to arise. If the advantage spans several APs, enter the **earliest** AP. |

### Calculations and rules

- No arithmetic.
- **Which SRNs to include**: every SRN from which a CT advantage is still expected in this AP **or any later AP**, even if it was already reported on an earlier return. Drop an SRN once no further advantage is expected (guidance). An SRN can therefore recur across many years' returns, with J5A pointing to the earliest AP of the advantage.
- **Row cap**: at most **10** schemes per return (XSD maxOccurs 10, matching the paper rows). Any excess goes on AAG4.
- **PRN format**: the schema accepts only 8-digit integers. The PRN format was not confirmed as compatible (see caveats).

### Main-return linkage

| CT600 box | Label | Link |
|---|---|---|
| 65 | Notice of disclosable avoidance schemes | Tick (`ReturnInfoSummary/RegisteredAvoidanceScheme`). The guide says to tick it if the company must disclose use of avoidance schemes **or** has been notified of a PRN. |
| 140 | Disclosure of Tax Avoidance Schemes – form CT600J | Tick (`SupplementaryPages/CT600J`). |

Linkage logic:
- On a **New** return, box 65 ⇔ box 140 (rules 9109 and 9134).
- On an **Amended** return, 65 may be ticked without 140, but 140 still requires 65.
- No CT600 amount box is fed by CT600J.

### Key schema validation rules (v1.995)

- **9109**: New return and `[65]='yes'` → `[140]` must be `yes`.
- **9134**: `[140]='yes'` → `[65]` must be `yes`.
- **9136**: `[140]='yes'` on a New return → CTJ (`[N104]`) must be present.
- **9314**: CTJ present → `[140]='yes'`.
- XSD: 1–10 `AvoidanceSchemes` rows; `ReferenceNumber` must match `[0-9]{8}`; `AccountingPeriod` must be a valid date.
- `CTJ-rules.txt` contains no additional form-level rules. There is no check that J5A falls on or after the return period.

### Worked example

AP 1 Apr 2025 – 31 Mar 2026. The company entered scheme SRN 12345678 in the AP to 31 Mar 2024 and expects advantages from AP 2024/25 onward. It also has SRN 87654321, first advantage expected in the AP ending 31 Mar 2027.

| Row | J5 | J5A |
|---|---|---|
| 1 | 12345678 | 31/03/2025 |
| 2 | 87654321 | 31/03/2027 |

CT600: box 65 = X, box 140 = X.

### Unverified / caveats

- **PRN format**: the guidance says to report PRNs on CT600J. Whether a POTAS PRN is always 8 numeric digits, which the schema enforces, was not verified. If it is not, a PRN cannot be filed in XML and AAG4(PRN) would be needed.
- The guidance cites the Tax Avoidance Schemes (Information) Regulations **2004**. These were revoked and replaced by SI 2012/1836 per that instrument's explanatory note.
- "Earliest AP" for J5A: the guidance wording ("If you expect the tax advantage to cover more than one accounting period, enter the earliest period") was followed literally. Whether a previously reported SRN should keep its original earliest date or roll forward was not confirmed by HMRC guidance.

---

## CT600K — Company Tax Return – supplementary page: Restitution Tax

- **Form version(s)**: `CT600K (2017) Version 3 for accounting periods starting on or after 1 April 2015`; footer `CT600K(2017) Version 3 Page 1 HMRC 04/17`. Single page.
  - Local file: `downloads/CT600K_2017.pdf` (text: `text/CT600K_2017.txt`). MD5 matches the live gov.uk asset (checked 2026-09-28).
  - Publication: https://www.gov.uk/government/publications/corporation-tax-restitution-tax-ct600k-2017-version-3 (first published 2017-04-10; asset https://assets.publishing.service.gov.uk/media/5a82e2cae5274a2e8ab59d8b/CT600K_2017.pdf; updated 2025-04-01, links only).
  - Guidance: https://www.gov.uk/guidance/supplementary-pages-ct600k-restitution-tax (updated 2024-01-02).
  - XML: `CompanyTaxReturn/RestitutionTax` (type `CTK`), schema v1.995.
  - Applicability: APs starting on or after 1 April 2015. It is still current.
- **Purpose / who must file**
  - Complete it if the company is chargeable to CT on **restitution interest** under **CTA 2010 Part 8C** (inserted by F(No.2)A 2015 s38) and that interest is not exempt. Charge: s357YA (https://www.legislation.gov.uk/ukpga/2010/4/section/357YA). Charitable companies are excluded (s357YA(2)).
  - **Restitution interest** (s357YC, https://www.legislation.gov.uk/ukpga/2010/4/section/357YC) means interest paid or payable by HMRC in respect of a restitution claim where all three conditions hold:
    - **A**: the claim concerns tax paid under a mistake of law, or tax unlawfully collected;
    - **B**: there is a final court determination, or a final settlement agreement;
    - **C**: the interest is **not** limited to simple interest at or below a statutory rate. In practice this means compound or "San Paolo/Littlewoods"-type interest.
  - Commencement: interest where the court determination became final, or the settlement was agreed, on or after **21 October 2015**. HMRC withholding under s357YO applies to payments on or after 26 October 2015 (F(No.2)A 2015 s38(9)–(11)).
  - **Rate**: **s357YK**: "The 'restitution payments rate' is **45%**" (https://www.legislation.gov.uk/ukpga/2010/4/section/357YK, checked 2026-09-28). The schema constant `[RESTITUTION INTEREST TAX RATE]` = 45 for all FYs from 2015.
  - **Ring-fenced from other profits** (s357YL): restitution interest is excluded from "total profits" (s4(3)). No reliefs, set-offs or other tax credits may be set against the 45% charge.
  - **Timing** (s357YE): the interest is brought in when recognised in the accounts under GAAP.
  - **Withholding**: HMRC must deduct 45% at source when paying restitution interest (s357YO). The amount deducted is treated as paid on account of the company's restitution-interest CT (s357YP), which is box K25.
  - Restitution tax sits **outside the instalment payments regime** (s357YT).

### Box table

| Box | Label (verbatim from form) | Type | Notes / calculation |
|---|---|---|---|
| K1 | Company name | text | Paper only; comes from CT600 box 1. |
| K2 | Tax reference | text | Paper only; comes from box 3. |
| K3 | from DD MM YYYY | date | Period covered by this supplementary page (cannot exceed 12 months). Comes from box 30. |
| K4 | to DD MM YYYY | date | Comes from box 35. |
| **Tax calculation** | | | `[SK001]` `TaxCalculation`, 1..1 |
| K5 | Self–assessment of tax payable before restitution tax — copy the figure from box 525 on CT600 | amount £p | `SAbeforeRestitutionTax`, 1..1, `CTpoundPenceStructure`. = box 525 (rule 9462). |
| K10 | Restitution interest | amount £ (whole) | `RestitutionInterest`, 1..1, `CTwholePoundStructure` (paper: `£ • 0 0`). |
| K15 | (table) A Financial year (yyyy) / B Amount of interest / C Rate of tax % / D Tax | table of **1 or 2 fixed rows** | `TaxCalculation/TaxCalculation`, 1..1. Row 1 = `FinancialYearOne` (1..1); row 2 = `FinancialYearTwo` (**0..1**). Not an unbounded repeat. |
| K15.1A | Financial year (yyyy) — row 1 | text `[0-9]{4}` (`xsd:gYear`) | The FY in which box 30 falls (FY *n* runs 1 Apr *n* – 31 Mar *n+1*). |
| K15.1B | Amount of interest — row 1 | amount £ (whole) | `CTwholePoundStructure`. |
| K15.1C | Rate of tax % — row 1 | % (decimal, 2 dp, 0–100) | Must be **45.00**. |
| K15.1D | Tax — row 1 | amount £p | = K15.1B × 45/100, rounded half up to 2 dp. |
| K15.2A | Financial year (yyyy) — row 2 | text `[0-9]{4}` | = K15.1A + 1. Only if the AP straddles 31 March. |
| K15.2B | Amount of interest — row 2 | amount £ | = K10 − K15.1B. |
| K15.2C | Rate of tax % — row 2 | % | 45.00. |
| K15.2D | Tax — row 2 | amount £p | = K15.2B × 45/100, rounded. |
| K20 | Total restitution tax — total of column D | amount £p | `TotalRestitutionTax`, 1..1. = K15.1D + K15.2D. |
| K25 | Tax already withheld | amount £p | `TaxAlreadyWithheld`, **0..1**. Tax withheld by HMRC under s357YO relating to this AP. Must be ≤ K20. |
| K30 | Self–assessment of tax payable after restitution tax — box K5 plus box K20 minus box K25 | amount £p | `SAafterRestitutionTax`, 1..1. |
| K35 | Restitution tax now payable — box K20 minus box K25 — copy the figure to box 527 on CT600 | amount £p | `RestitutionTaxNowPayable`, 1..1. It is an unsigned (≥0) type, which is consistent with K25 ≤ K20. |

### Calculations and rules

- `K5 = CT600 box 525` (box 510 − box 515, floored at 0).
- `K10` = restitution interest recognised in the AP (s357YE).
- **FY split**:
  - If boxes 30 and 35 fall in the same FY: one row, `K15.1A = FY(box 30)` and `K15.1B = K10`.
  - If the AP straddles 1 April: two rows, `K15.2A = K15.1A + 1` and `K15.1B + K15.2B = K10` (rules 9222, 9223 and 9228).
  - The form and schema do not prescribe the split basis. Time apportionment by days is the usual CT approach. Because both FYs are at 45%, the split affects only pence rounding.
- `K15.nD = round_half_up(K15.nB × 45 / 100, 2)` (rules 9225 and 9230).
- `K20 = K15.1D + K15.2D`.
- `K25 ≤ K20` (rule 9232).
- `K30 = K5 + K20 − K25`.
- `K35 = K20 − K25` → **CT600 box 527**.
- **Main-return arithmetic**: `528 = 525 + 526 + 527` (rule 9370). So K30 = 528 − 526.
- **Exclusions elsewhere on the CT600**:
  - Restitution interest must **not** be included in **box 170** (non-trading loan relationship profits). The guide says: "Do not include any amounts of restitution interest. These are accounted for separately on the supplementary page CT600K."
  - It is therefore also outside boxes 235, 300 and 315, and outside the associated-company and marginal-relief computations (s357YL(1)).
  - Box **595** (tax already paid) must **not** include restitution tax (guide).
  - No reliefs or set-offs reduce K20 (s357YL(2)–(4)). For example, box 515 income tax or R&D credits cannot be offset against it.

### Main-return linkage

| CT600 box | Label (CT600 (2026) v3) | Link |
|---|---|---|
| 141 | Restitution tax – form CT600K | Tick. |
| 525 | Self-assessment of tax payable before restitution tax and coronavirus support scheme overpayments | Source of **K5**. |
| 527 | Restitution tax | = **K35** (rule 9239). |
| 528 | Self-assessment of tax payable | = 525 + 526 + 527. |
| 170 | Bank, building society or other interest, and profits from non-trading loan relationships | Must **exclude** restitution interest. |
| 595 | Tax already paid (and not already repaid) | Must exclude restitution tax. |

### Key schema validation rules (v1.995)

- **Presence**: 9137 (141 on a New return → CTK present); 9461 (CTK → 141); 9368 (527 only if 141, New return); **9369** (if K35 is absent and 141 is not ticked, box 527 must be 0); 9367 (527 present → 528 present); 9370 (528 = 525 + 526 + 527).
- **Calculation**: 9462 (K5 = 525); 9220 and 9226 (K15.2 present iff 30 and 35 are in different FYs); 9221 (K15.1A = FY of box 30); 9222 and 9223 (K15.1B vs K10); 9224 and 9229 (rate = 45); 9225 and 9230 (tax rounding); 9227 (K15.2A = K15.1A + 1); 9228 (K15.2B = K10 − K15.1B); 9231 (K20); 9232 (K25 ≤ K20); 9233 (K30); 9235 (K35 = K20 − K25); **9239** (K35 → 527 present and equal).

### Worked example

AP 1 Jan 2025 – 31 Dec 2025 (straddles FY2024/FY2025). A settlement agreed in 2025 lets the company **retain** £1,000,000 of compound interest already paid to it, so no s357YO withholding applies (K25 absent). Box 525 = £250,000.00.

| Box | Value | Working |
|---|---|---|
| K5 | 250000.00 | = box 525 |
| K10 | 1000000 | |
| K15.1 | 2024 / 246575 / 45.00 / 110958.75 | 1,000,000 × 90/365 = 246,575.34 → 246,575; × 45% |
| K15.2 | 2025 / 753425 / 45.00 / 339041.25 | 1,000,000 − 246,575; × 45% |
| K20 | 450000.00 | 110,958.75 + 339,041.25 |
| K25 | (absent) | |
| K30 | 700000.00 | 250,000 + 450,000 − 0 |
| K35 | 450000.00 | → **box 527** |
| CT600 528 | 700000.00 | 525 + 526 (0) + 527 |

Typical HMRC-paid case: HMRC paid the interest net of 45% (K25 = 450,000.00), so K35 = **0.00** and box 527 = 0.00. Rule 9239 still requires 527 to be present.

### Unverified / caveats

- **FY split basis** for K15.1B/K15.2B: not specified by the form, guidance or schema. Days-based apportionment was assumed. The alternative is to split by when amounts were recognised (s357YE).
- Rule 9369's English text ("If Box K35 is not completed and Box 141 is not completed then Box 527 must be 0") implies 527 may appear as 0.00 even without CT600K. Rule 9368 forbids 527 without 141 on New returns. Software should simply omit 527 when there is no CT600K.
- Whether K5 should be **positive only** is not stated. 525 is floored at 0 by rule 9347, so K5 ≥ 0.
- K25 is described as tax withheld "that relates to this accounting period" (guidance, s357YO). Where HMRC withholding spans APs, allocation was not researched.

---

## CT600L — Research and development

- **Form versions** (all say "for accounting periods starting on or after 1 April 2015"):
  - `downloads/CT600L_2022_v3.pdf`: "CT600L (2022) Version 3", HMRC 04/22. The 2022 publication was the live attachment until April 2025, so it applies to 2024 filings.
  - `downloads/CT600L_2025_v3.pdf`: "CT600L (2025) Version 3", HMRC 04/25.
  - `downloads/CT600L.pdf`: "CT600L (2026) Version 3", HMRC 04/26.
  - Publication: https://www.gov.uk/government/publications/corporation-tax-research-and-development-ct600l-2021-version-3
  - Guidance: https://www.gov.uk/guidance/supplementary-pages-ct600l-research-and-development (updated 2026-04-05; saved in `guidance/`).
- **Version changes**:
  - **2022 → 2025**:
    - Step 3 retitled "PAYE and National Insurance Contributions liability cap". L75 was "Total relevant expenditure on R&D workers' PAYE and NIC" and became "PAYE and NIC liability cap".
    - The SME section was renamed "SME R&D and enhanced support for R&D intensive SME (ERIS)", and L170/L175/L180 were relabelled "SME/R&D intensive SME…".
  - **2025 → 2026**:
    - New Step 3 boxes **L71** (s1112E exception tick), **L71A**, **L72**, **L72A**, **L73** and **L73A** (PAYE data for RDEC-only claims). L75 relabelled "PAYE/NICs liability cap".
    - L123 extended to "…or not payable by section 1112F(2)".
    - L167 now "s1058D **or s1112E**".
    - Page 6 now holds overflow PAYE references for L72A/L168A and L73A/L169A.
  - The schema (v1.995) contains the 2026 set. L71A may only be used for periods starting ≥ 1 Apr 2024 (rule 8032).
- **Who files**: any company claiming RDEC (old Chapter 6A or merged-scheme Chapter 1A) or an SME/ERIS **payable** tax credit, and ticks CT600 box **142**. An ERIS/SME claim that takes only the additional deduction, with no payable credit, needs no CT600L; boxes 650–660 on the CT600 carry it.

### Box table (2026 form; ⁺ marks boxes absent before 2026)

**Company information**

| Box | Label (form) | Type |
|---|---|---|
| L1 | Company name | text |
| L2 | Tax reference | UTR |
| L3 | From | date |
| L4 | To | date |

**Pre-step 1 restriction.** Complete if there is a step 2 restriction brought forward, or RDEC surrendered in from group companies.

| Box | Label (form) | Type | Calculation / rule |
|---|---|---|---|
| L5 | Step 2 restriction brought forward from previous accounting periods and/or surrendered from group companies | £p | |
| L6 | Corporation Tax liability | £p | = CT600 box 475 (rule 9623) |
| L7 | Amount of Step 2 brought forward and surrendered RDEC used to discharge CT liability – copy to L194 | £p | = min(L5, L6) |
| L8 | Amount of Step 2 brought forward RDEC carried forward to next AP – L5 minus L7 – copy to L129 | £p | |
| L9 | Remaining CT liability carried forward to Step 1 – L6 minus L7 – copy to L30 | £p | |

**Step 1 – RDEC set against CT liability**

| Box | Label (form) | Type | Calculation / rule |
|---|---|---|---|
| L10 | R&D expenditure on which RDEC is claimed in this AP | £p | |
| L15 | RDEC claim for this AP | £p | < L10. Gross credit, including amounts later extinguished (L123). If L185/L190 are used (pre-2024 SMEs), L15 = L185 + L190 |
| L20 | Step 3 amounts from a previous AP treated as RDEC for this AP | £p | |
| L25 | Total RDEC for the AP – total of L15 and L20 | £p | |
| L30 | Remaining CT liability | £p | = L9 if completed, otherwise box 475 |
| L35 | Income Tax deducted from profits (applicable to CT liability) | £p | ≤ box 515 and ≤ L30 |
| L40 | Maximum amount available for Step 1 set-off – L30 minus L35 | £p | |
| L45 | Amount of RDEC used to discharge CT at Step 1 – copy to L195 | £p | = min(L25, L40); 0 if L40 is blank |

**Step 2 – notional tax charge**

| Box | Label (form) | Type | Calculation / rule |
|---|---|---|---|
| L50 | Step 1 balance carried forward to Step 2 | £p | = L25 − L45 |
| L55 | CT charge on RDEC for this AP | £p | = L15 × notional rate (see rules below). Rule 9738: ≥ L15 × the lowest applicable CT rate |
| L60 | Total RDEC arising in this AP less CT charge on the RDEC – L15 minus L55 | £p | |
| L62 | RDEC arising in this AP less remaining CT liability at step 1 | £p | = L15 − L40 if L40 < L15, else 0 |
| L65 | Step 2 restriction carried forward to next AP – copy to L130 | £p | = max(0, L62 − L60) (rules 9631/9989, for periods starting ≥ 1 Apr 2022) |

**Step 3 – PAYE and NIC liability cap**

| Box | Label (form) | Type | Calculation / rule |
|---|---|---|---|
| L70 | Step 2 balance carried forward to Step 3 | £p | = L50 − L65 |
| L71⁺ | Does the exception at s1112E CTA 2009 apply? | tick | RDEC-only claims |
| L71A⁺ | Total expenditure on externally provided workers from, and subcontracting to, connected persons | £ | Required with L71; ≤ 15% × L10. Not allowed if the SME section is used |
| L72⁺ | PAYE/NICs for which the company is liable in this AP | £p | Not allowed with L71. Requires L72A |
| L72A⁺ | Employer PAYE reference | PAYE ref (0..2) | |
| L73⁺ | Relevant PAYE/NICs liability of connected companies | £p | Requires L73A |
| L73A⁺ | Connected companies' employer PAYE reference | PAYE ref (0..∞) | |
| L75 | PAYE/NICs liability cap | £p | See the cap formulas below |
| L80 | Step 3 restriction carried forward to next AP – copy to L145 | £p | = max(0, L70 − L75), and 0 if L71 or L167 is ticked (rule 9746) |

**Steps 4 to 7**

| Box | Label (form) | Type | Calculation / rule |
|---|---|---|---|
| L85 | Step 3 balance carried forward to Step 4 | £p | = L70 − L80 |
| L90 | Amount used to discharge CT liability of another AP | £p | ≤ L85 |
| L95 | Step 4 balance carried forward to Step 5 | £p | = L85 − L90 |
| L100 | Credit surrendered to group member – copy to L160 | £p | ≤ L95 |
| L105 | Step 5 balance carried forward to Step 6 | £p | = L95 − L100 |
| L110 | Amount used to discharge other company liability on this CTSA – copy to L200 | £p | ≤ L105. For example boxes 480–505 liabilities |
| L115 | Amount used to discharge any other company liability | £p | ≤ L105 − L110. For example VAT or PAYE |
| L120 | Total used to discharge other company liability | £p | = L110 + L115 |
| L123 | Amounts extinguished by s104S(2)(b) CTA 2009 [or not payable by s1112F(2)] | £p | Going-concern failures |
| L125 | Payable RDEC – L105 minus (L120 + L123) | £p | **→ CT600 box 880** |

**RDEC carried forward**

| Box | Label (form) | Type | Calculation / rule |
|---|---|---|---|
| L129 | Pre-step 1 restriction | £p | = L8 |
| L130 | Step 2 restriction | £p | = L65 |
| L135 | Surrendered to other group company – copy to L155 | £p | |
| L140 | Balance carried forward to next AP | £p | = L129 + L130 − L135 |
| L145 | Step 3 restriction | £p | = L80 |
| L150 | Total carried forward to next AP | £p | = L140 + L145 |

**RDEC surrendered**

| Box | Label (form) | Type | Calculation / rule |
|---|---|---|---|
| L155 | Step 2 restriction surrendered | £p | = L135 |
| L160 | Step 5 credit surrendered to group member | £p | = L100 |
| L165 | Total surrendered | £p | = L155 + L160 |

**SME R&D and ERIS.** For periods starting ≥ 1 Apr 2024 this section is only allowed if CT600 box 653 is ticked (rule 9885).

| Box | Label (form) | Type | Calculation / rule |
|---|---|---|---|
| L166 | R&D expenditure | £ | = CT600 box **659** (rule 9439) |
| L167 | Does the exception at s1058D or s1112E CTA 2009 apply? | tick | s1058D for periods starting < 1 Apr 2024; s1112E for periods starting ≥ 1 Apr 2024 |
| L167A | Total expenditure on externally provided workers from, and subcontracting to, connected persons | £ | Required with L167. ≤ 15% × L166 (pre-2024), or ≤ 15% × (L166 + L10) (≥ 1 Apr 2024) |
| L168 | PAYE/NICs for which the company is liable in this AP | £p | Not allowed with L167. Combined figure if the company also claims RDEC. Requires L168A |
| L168A | Employer PAYE reference | PAYE ref (0..2) | |
| L169 | Relevant PAYE/NICs liability of connected companies | £p | Requires L169A |
| L169A | Connected companies' employer PAYE reference | PAYE ref (0..∞) | |
| L170 | SME/R&D intensive SME R&D payable tax credit claim for this AP | £p | If L167 is not ticked (periods starting ≥ 1 Apr 2021): ≤ 3 × (L168 + L169) + £20,000 |
| L175 | SME/R&D intensive SME payable tax credit set-off against other liabilities on this return – copy to L205 | £p | ≤ L170 |
| L180 | SME/R&D intensive SME balance payable tax credit – L170 minus L175 | £p | **→ CT600 box 875** |
| L185 | SME RDEC claim from work subcontracted to it by a large company | £p | Not allowed for periods starting ≥ 1 Apr 2024 (rule 9886) |
| L190 | SME RDEC claim for subsidised and capped work | £p | Not allowed for periods starting ≥ 1 Apr 2024 |

**Total R&D set-off against liabilities in this return**

| Box | Label (form) | Type | Calculation / rule |
|---|---|---|---|
| L194 | RDEC pre-step 1 discharge amount | £p | = L7 |
| L195 | RDEC Step 1 discharge amount | £p | = L45 |
| L200 | RDEC Step 6 discharge amount for this AP | £p | = L110 |
| L205 | SME R&D payable tax credit used to discharge other liabilities on this return | £p | = L175 |
| L210 | Total – total of L194 to L205 | £p | **→ CT600 box 530** (rule 9791) |

Section-presence rules 9710–9716 and 9734–9776: each Step section is required if the previous step leaves a positive balance, and is only allowed if the previous step is present.

### Main-return linkage (CT600L ↔ CT600)

| Direction | Link |
|---|---|
| CT600 → CT600L | box 475 → L6 / L30; box 515 caps L35; box 659 = L166 |
| CT600L → CT600 | L210 → **530**; L180 → **875**; L125 → **880** |
| Ticks | 142 (page enclosed); 650/653/655 (company type); 656 (claim notification); 657 (additional information form) |
| Other CT600 boxes | 659 / 660 / 670 (SME/ERIS expenditure); 615 (RDEC surrendered *to* this company); 943 (nominee for a payable credit) |
| Totals | 530 is part of 545, which flows to 570 and 600/605. 880 and 875 are repayment boxes, and the bank details in 920–940 are expected |
| Merged RDEC income | The gross credit (L15) is taxable trading income, included in box 155 (CIRD112000) |

---

## CT600M — Company Tax Return – supplementary page: Freeports and Investment Zones

- **Form version(s)**: `CT600M (2024) Version 3 for accounting periods starting on or after 1 April 2015`; footer `CT600M(2024) Version 3 Page 1/2/3 HMRC 04/24`. Three pages: company info; enhanced SBA table (M5, 12 paper rows); ECA table (M20, 12 paper rows).
  - Local file: `downloads/CT600M_2024_v3.pdf` (text: `text/CT600M_2024_v3.txt`). MD5 matches the live gov.uk asset (checked 2026-09-28).
  - Publication: https://www.gov.uk/government/publications/corporation-tax-freeports-ct600m-2022-version-3 (first published 2022-04-01; 2024-04-05 "now covers Investment Zones"; asset https://assets.publishing.service.gov.uk/media/65e88fc45b65240011f21aed/CT600M_2024_v3.pdf; updated 2025-04-01). The slug says "2022-version-3" but the printed version is "(2024) Version 3".
  - Guidance: https://www.gov.uk/guidance/supplementary-pages-ct600m-freeports-and-investment-zones. Updated **2026-04-16** (two new Investment Zones added to the column A code list); earlier updates 2025-11-21 and 2025-02-26.
  - XML: `CompanyTaxReturn/Freeports` (type `CTM`), schema v1.995.
- **Purpose / who must file**
  - File it when claiming **enhanced structures and buildings allowance (eSBA)** or **enhanced capital allowances (ECA) for plant and machinery** on qualifying expenditure for a **Freeport or Investment Zone special tax site** (guidance). Only companies qualify for ECA (s45O(6)).
  - **ECA (100% FYA)**: **CAA 2001 s45O** "Expenditure on plant and machinery for use in special tax sites" (https://www.legislation.gov.uk/ukpga/2001/2/section/45O, checked 2026-09-28). Conditions:
    - A: for use primarily in an area that is a special tax site when the expenditure is incurred;
    - B: unused and not second-hand;
    - C: for a qualifying activity within s15(1)(a) (trade) or (f) (a deemed trade, e.g. mines, transport undertakings);
    - D: incurred on or before the applicable sunset date;
    - E: the company is within the charge to CT.
  - Related ECA sections:
    - s45P: power to amend conditions;
    - s45Q: exclusion for P&M partly for use outside special tax sites (just and reasonable apportionment);
    - s45R: failure of ongoing requirements, a **5-year primary-use** clawback that must be notified within 3 months;
    - s45S: other cases;
    - s45T: disqualifying arrangements.
    - Manual: CA23121–CA23128 (https://www.gov.uk/hmrc-internal-manuals/capital-allowances-manual/ca23121).
  - **eSBA at 10%**: **CAA 2001 s270AA(5)**: the annual allowance is "(a) in the case of special tax site qualifying expenditure, **10%** of the expenditure, and (b) in the case of other qualifying expenditure, **3%**".
    - s270AA(2A): the allowance period is **10 years** for special tax site expenditure, versus 33⅓ years otherwise.
    - "Special tax site qualifying expenditure" is defined in s270BNA; apportionment for straddling buildings or late use is in s270BNB.
    - Manual: CA94750–CA94760 (https://www.gov.uk/hmrc-internal-manuals/capital-allowances-manual/ca94750).
    - An **allowance statement** stating the expenditure is special tax site qualifying expenditure is required (CA94760).
  - **Sunset dates**: F(No.2)A 2023 s332(4) allows the date to be set by regulations. The **Special Tax Sites (Applicable Sunset Date) Regulations 2024 (SI 2024/574)**, reg 2, set it to:
    - **30 September 2031** for special tax sites connected to a Freeport in **England**;
    - **30 September 2034** for all others (Scottish Green Freeports, Welsh Freeports, all Investment Zones).
    - Sources: https://www.legislation.gov.uk/uksi/2024/574/made (in force 21 May 2024) and https://www.gov.uk/government/publications/extension-to-freeport-and-investment-zones-special-tax-site-sunset-dates.
    - The original date was 30 Sept 2026.
    - For eSBA, the building must be **brought into qualifying use** and the expenditure **incurred** on or before the sunset date. Construction must **begin** (first contract, or start of works if earlier) while the land is a special tax site (https://www.gov.uk/guidance/check-if-you-can-claim-enhanced-structures-and-buildings-allowance-relief-in-freeport-tax-sites).
  - **Start date**: no relief before the site's **designation** by regulations (The Designation of Special Tax Sites (…) Regulations, one per site). Examples from the legislation.gov.uk feed:
    - Humber Freeport: SI 2024/71
    - Inverness and Cromarty Firth: SI 2024/380
    - Liverpool City Region, West Midlands and North East IZs: SI 2024/383, in force 8 Apr 2024
    - Forth: SI 2024/671
    - Celtic: SI 2024/1035
    - Anglesey: SI 2024/1286 and SI 2025/1079
    - East Midlands IZ: SI 2025/111
    - Flintshire and Wrexham IZ: SI 2025/1080
    - North East of Scotland IZ: SI 2026/90
    - Glasgow City Region IZ: SI 2026/92
    - Earlier English Freeport designations were made in 2021–23 and are not listed here.

### Box table

| Box | Label (verbatim from form) | Type | Notes / calculation |
|---|---|---|---|
| M1 | Company name | text | Paper only; comes from CT600 box 1. |
| M2 | Tax reference | text | Paper only; comes from box 3. |
| M3 | from DD MM YYYY | date | Period covered by this supplementary page (cannot exceed 12 months). Comes from box 30. |
| M4 | to DD MM YYYY | date | Comes from box 35. |
| M5 | Enhanced structures and buildings allowances in Freeports and Investment Zones | repeating table **0..∞** (`[M5]` `EnhancedSBAinFreeports`) | Paper form has 12 rows. **One row per building or structure.** |
| M5A | Location of Freeport and/or Investment Zone | count (integer code 1–300) | `LocationOfFreeport`, 1..1, `xsd:integer` 1..300. **A code, not free text.** See the code list below. |
| M5B | Address of business operation | text (address) | `CTaddressStructure`: 2–3 lines of ≤28 chars, optional AdditionalLine ≤18, optional PostCode ≤8. |
| M5C | Date structure or building was brought into qualifying use DD MM YYYY | date | 1..1. The guidance says to enter the **later** of the qualifying-use date and the date the qualifying expenditure was incurred, i.e. the allowance period start. |
| M5D | Date of first contract for construction DD MM YYYY | date | 1..1. If there is no contract, or the contract post-dates the start of works, enter the date works began. |
| M5E | Total amount of qualifying expenditure | amount £ (whole, ≥0) | 1..1. Enter the **full** Freeport/IZ qualifying expenditure only if you are the **first claimant claiming for the first time**. Otherwise enter **0**, including subsequent owners and later years. Excludes the non-site part of any apportioned expenditure. |
| M5F | Total Structures and Building Allowance (SBA) claim amount | amount £ (whole, ≥0) | 1..1. The enhanced (10%) claim for this period only. Excludes the 3% element of apportioned buildings. |
| M10 | Total (of column E) — Add this amount to the entry in box 771 on form CT600 | amount £ | `QualifyingExpenditureTotal`, 0..1, but required if any M5 row exists. = Σ M5E. |
| M15 | Total (of column F) — Add the amount relating to a trade in box 711 and the amount unrelated to a trade in box 736 on form CT600 | amount £ | `SBAclaimTotal`, 0..1, but required if any M5 row exists. = Σ M5F. |
| M20 | Enhanced capital allowance (ECA) for plant machinery in Freeports and Investment Zones | repeating table **0..∞** (`[M20]` `ECAforPlantAndMachineryInFreeports`) | Paper form has 12 rows. **One row per Freeport/IZ** (guidance: "A separate entry must be made for claims relating to different Freeports and Investment Zones"). |
| M20A | Location of Freeport and/or Investment Zone | count (integer code 1–300) | 1..1. |
| M20B | Address of business operation | text (address) | 1..1, `CTaddressStructure`. |
| M20C | Put an 'X' in the column below if you made an Enterprise Zone claim relating to this ECA claim | tick (X) | 0..1. Enterprise Zone FYA (boxes 721/746) is not available for expenditure on or after 16 Mar 2024, per the main guide. |
| M20D | Total amount of ECA claimed for the accounting period | amount £ | 0..1. If the full 100% is claimed, this equals the expenditure. |
| M20E | Disposal value | amount £ | 0..1. Enter even where it is brought into a main, special rate or single-asset pool and no balancing charge arises. |
| M25 | Total (of column D) | amount £ | `AmountOfECAclaimedWithinTheAccountingPeriodTotal`, 0..1. = Σ M20D. Include in CT600 **box 760** with other FYA expenditure (guidance). |
| M30 | Total (of column E) | amount £ | `DisposalValueTotal`, 0..1. = Σ M20E. |

**Column A codes** (guidance, 2026-04-16; the XSD permits 1–300):

| Code | Location | Code | Location |
|---|---|---|---|
| 1 | Freeport: East Midlands Airport | 11 | Freeport: Anglesey |
| 2 | Freeport: Felixstowe and Harwich | 12 | Freeport: Celtic (Port Talbot and Milford Haven) |
| 3 | Freeport: Humber | 13 | Investment Zone: Liverpool City Region |
| 4 | Freeport: Liverpool City Region | 14 | Investment Zone: North East |
| 5 | Freeport: Plymouth and South Devon | 15 | Investment Zone: West Midlands |
| 6 | Freeport: Solent | 16 | Investment Zone: East Midlands |
| 7 | Freeport: Thames | 17 | Investment Zone: Flintshire and Wrexham |
| 8 | Freeport: Teesside | 18 | Investment Zone: North East of Scotland |
| 9 | Freeport: Inverness and Cromarty Firth | 19 | Investment Zone: Glasgow City Region |
| 10 | Freeport: Forth | | |

Sunset date by code:
- Codes 1–8 (English Freeports): 30 Sep 2031.
- Codes 9–12 (Scottish Green and Welsh Freeports) and 13–19 (Investment Zones): 30 Sep 2034.

### Calculations and rules

- **eSBA per building per period**: `M5F = 10% × special-tax-site qualifying expenditure × (days in AP in the allowance period ÷ 365)`. The basic rule is set for a 1-year chargeable period (s270AA(5)); pro-rating for short periods and part-periods applies as for normal SBA (CA90000). The allowance runs for 10 years from the later of first non-residential use and the date expenditure was incurred.
  - **Apportionment**: where a building straddles the site boundary, or part is brought into use after the sunset date, split the expenditure. The site part gets 10% and goes on CT600M; the rest gets 3% and goes on CT600 only (s270BNB; CA94755).
- **M5E**: only in the first claim by the first claimant. The same amount must appear in CT600 box 771 "Structures and buildings" (qualifying expenditure), with M10 ≤ 771 (rule 9655).
- **M15 → 711/736**: the eSBA claim is also included in CT600 box **711** (SBA included in trading profit computations) or box **736** (SBA not included in trading computations, e.g. property business), with M15 ≤ 711 + 736 (rule 9658).
- **ECA per row**: 100% FYA on qualifying expenditure. The claim may be for less than 100% (FYA may be disclaimed or partly claimed). Any unclaimed balance goes to the main or special rate pool.
  - Mixed-use P&M: apportion under s45Q. The guidance example uses £400,000 × 2/3 = £266,667 as ECA.
- **M25 → 760**: M25 must be included in CT600 box **760** "Machinery and plant on which first year allowance is claimed" (rule 9667 requires 760 when M25 is present).
- **Allowance boxes**: per the CT600M guidance, do **not** include M20D/M20E amounts in CT600 boxes 690–730 unless a disposal value went into a pool. The Freeport/IZ ECA *allowance* amount is therefore reported only on CT600M; its *expenditure* is in 760.
- **Disposals / clawback**: M20E records disposal values for State aid purposes. If primary use in the site ceases within 5 years, s45R withdraws the ECA and HMRC must be notified within 3 months.

### Main-return linkage

| CT600 box | Label (CT600 (2026) v3) | Link |
|---|---|---|
| 143 | Freeports and Investment Zones – form CT600M | Tick. |
| 771 | Structures and buildings (qualifying expenditure) | Includes **M10**; rule 9655: M10 ≤ 771. |
| 711 | Structures and buildings (allowances included in trading computations) | Includes the trade part of **M15**. |
| 736 | Structures and buildings (allowances not included in trading computations) | Includes the non-trade part of **M15**; rule 9658: M15 ≤ 711 + 736. |
| 760 | Machinery and plant on which first year allowance is claimed | Includes **M25**; required when M25 is present (rule 9667). |
| 721/722, 746/747 | Enterprise zones | Relevant only to M20C. Not in use for APs beginning on or after 1 Apr 2024. |

### Key schema validation rules (v1.995)

- **Presence**: 9600 (143 → CTM present; note there is no "New return" qualifier); 9649 (CTM → 143); 9644 (CTM must contain at least one M5 or M20 row).
- **Totals**: 9645 and 9646 (M10 and M15 required if any M5); 9647 (M25 required if any M20D); 9648 (M30 required if any M20E); 9657 (M10 = Σ M5E); 9661 (M15 = Σ M5F); 9668 (M25 = Σ M20D); 9669 (M30 = Σ M20E).
- **Cross-checks**: 9655 (M10 ≤ 771); 9658 (M15 ≤ 711 + 736); 9667 (M25 → 760 present); 9662 (each M20 row needs at least one of M20C, M20D or M20E).
- Main-return date gates: 9412, 9260 and 9291 (771, 711 and 736 are allowed only if box 35 ≥ 2018-10-29).

### Worked example

Company, y/e 31 Mar 2026, trading, 12-month AP.

eSBA:
- Warehouse in the **Thames Freeport** tax site (code 7). First contract 01/06/2023; construction started later. Completed and first used 01/04/2025. Qualifying expenditure £1,200,000; the company is the first claimant.
- A second building in the **West Midlands IZ** (code 15), claimed since 2024/25 on £500,000.

| M5 row | A | C | D | E | F |
|---|---|---|---|---|---|
| 1 | 7 | 01/04/2025 | 01/06/2023 | 1200000 | 120000 (10% × 1,200,000 × 365/365) |
| 2 | 15 | 01/10/2024 | 15/05/2024 | 0 | 50000 (10% × 500,000; already reported in E in 2024/25). The first contract post-dates the 8 Apr 2024 designation (SI 2024/383). |

- M10 = **1,200,000**. It must be included in 771; if there is no other SBA expenditure, 771 = 1,200,000.
- M15 = **170,000**. Included in 711 (trade), e.g. 711 = 170,000 + any 3% SBA on other buildings.

ECA:
- New racking £300,000 for the Thames site (code 7), full claim.
- Plant used in the Liverpool City Region IZ (code 13) that was sold during the year for £20,000.

| M20 row | A | C | D | E |
|---|---|---|---|---|
| 1 | 7 | | 300000 | |
| 2 | 13 | | | 20000 |

- M25 = **300,000**, included in box 760 (e.g. 760 = 300,000 + any full-expensing expenditure).
- M30 = **20,000**.
- The £300,000 allowance is deducted in the trading computation but **not** entered in boxes 690–730.

Contrast: a standard SBA on the same £1.2m outside a site would give 3% × 1,200,000 = £36,000 a year.

### Unverified / caveats

- **ECA allowance destination**: neither the main guide nor the CT600M guidance names a CT600 *allowances* box for the Freeport/IZ ECA amount. The guidance only says to exclude it from 690–730. It appears to be reported on CT600M only (analogous to the old EZ boxes 721/746), which leaves a potential gap in box-level reconciliation of trading-profit allowances. Needs HMRC confirmation.
- **M5A/M20A** are labelled like free text on the PDF but are integer codes in the XSD (1–300). The code list lives only in the guidance and has grown (18 and 19 were added 2025–26). Keep it data-driven.
- **M5C** label vs guidance: the label says "Date … brought into qualifying use", but the guidance says to use the later of use and the date expenditure was incurred.
- **M15 split**: M15 is a single total, but the CT600 splits it across 711 and 736. The schema only checks M15 ≤ 711 + 736, so the split is not validated.
- Rule 9600 lacks the "return type is New" qualifier that the other supplementary-page presence rules (9124, 9129 and so on) have.
- The designation date per site is needed to validate "no relief before designation". The regulation dates were not tabulated (see the list of `The Designation of Special Tax Sites (…) Regulations` instruments on legislation.gov.uk).
- The pro-rating of eSBA for short APs and part-year use follows general SBA rules (s270AA(2), CA90000); it was not separately re-verified for special tax sites.

---

## CT600N — Company Tax Return – supplementary page: Residential Property Developer Tax

- **Form version(s)**: `CT600N (2023) Version 3 for accounting periods starting on or after 1 April 2022`. The page footer reads `CT600N(2023) Version 3 … HMRC 04/23`.
  - Local file: `downloads/CT600N.pdf` (text in `text/CT600N.txt`).
  - Publication: https://www.gov.uk/government/publications/corporation-tax-residential-property-developer-tax-ct600n. It was first published 2023-04-01 and last updated 2025-04-01 (link changes only). The asset is https://assets.publishing.service.gov.uk/media/6405cbffd3bf7f564ee6bb08/CT600N.pdf.
  - Guidance: https://www.gov.uk/guidance/supplementary-pages-ct600n-residential-property-developer-tax (local `guidance/supplementary-pages-ct600n-residential-property-developer-tax.md`, updated 2025-02-12).
  - Schema: HMRC CT XML spec v1.995, element `[CTN]` = `/IRenvelope/CompanyTaxReturn/ResidentialPropertyDeveloperTax` (main-return id `[N120]`). See `schema/CTN-boxes.txt` and `schema/CTN-rules.txt`.
  - Applicability: accounting periods starting on or after 1 April 2022. RPDT applies to profits arising on or after 1 April 2022. For an accounting period that straddles that date, a separate RPDT period is deemed to start on 1 April 2022, and profits are time-apportioned into it (FA 2022 s51(1)-(3); https://www.gov.uk/hmrc-internal-manuals/residential-property-developer-tax-manual/rpdt40100). Only one CT600N version has been published, so there is no version switch to model.

### Purpose / who must file
- Complete CT600N if the company is recording an amount of RPDT in CT600 box 497 (guidance "When to complete"). The page carries the RPDT computation. The group's allocating member may also use it to file the allowance allocation statement. It is also used for claims and surrenders of RPDT group relief unless the group uses "simplified arrangements" (https://www.gov.uk/hmrc-internal-manuals/residential-property-developer-tax-manual/rpdt30300).
- **Charge.** 4% of a residential property developer's RPD profits for an accounting period, to the extent they exceed the developer's allowance. It is charged "as if it were an amount of corporation tax" (FA 2022 s33, https://www.legislation.gov.uk/ukpga/2022/3/section/33; RPDT20100).
- **Who is an RP developer.** A company within the charge to CT that carries on residential property development activities, or that has a substantial interest (≥10%, including group holdings) in a JV company that is an RP developer. Non-profit housing companies and their wholly owned subsidiaries are excluded (FA 2022 s34, s35, s40; RPDT10100 https://www.gov.uk/hmrc-internal-manuals/residential-property-developer-tax-manual/rpdt10100; RPDT10200).
- **Reporting threshold.** A company need not return its RPD profits if it is reasonable to assume there would be no RPDT liability, ignoring the deduction of RPDT losses and group relief (FA98 Sch18 para 7A, inserted by FA22 Sch8 para 2(3); RPDT30300). For example, gross RPD profits of £27m with a £25m allowance must be reported even if losses bring the charge to nil.
- **Administration.** RPDT is administered as CT (returns, payments, quarterly instalment payments, enquiries, penalties, interest) under FA 2022 s45 (RPDT30100). Legislation: FA 2022 Part 2 (ss.32-56 and Schs 7-9), https://www.legislation.gov.uk/ukpga/2022/3/part/2. Regulations: SI 2022/266.

### Box table
Types:
- The schema has no N1-N4. The `[CTN]` element starts at Section 1, so company name, UTR and period come from the CT600 itself (boxes 1, 3, 30, 35). N1-N4 are print-only.
- `CTwholePoundStructure` = amount £ (whole pounds, may be 0). `CT_CTnonZeroWholePoundStructure` = amount £, non-zero. `CTpoundPenceStructure` = amount £p. `CT_YesType` = tick (X), and the only allowed value is "yes". `PeriodType` = period (from–to). `CT_UTRtype` = 10-digit UTR. `CTexcludedCharsStringType` = text.
- The PDF prints 7 rows for each table. The schema allows 0..∞ or 1..∞ as noted.
- Rows marked **(schema-only)** are XML elements with no printed box.

| Box | Label (verbatim from form) | Type | Notes / calculation |
|---|---|---|---|
| N1 | Company name | text | Print only; not in schema. |
| N2 | Tax reference | text (10-digit UTR) | Print only. |
| N3 | Period covered by this supplementary page (cannot exceed 12 months) – from | date | Print only (equals CT600 box 30). |
| N4 | … to | date | Print only (equals CT600 box 35). |
| — | *Section 1: Allocation statement* (`SN001`, 0..1) | section | Only the allocating member completes it. |
| N5 | Put an 'X' in box N5 if you are the nominated allocating member | tick | Schema **1..1** within Section 1. If Section 1 is present, N5 must be "yes". |
| N10 | Put an 'X' in N10 if the Allocation statement has been sent to HMRC for this period | tick | 0..1. If N10 is ticked, N15-N65 must be absent (9525, 9605, 9635, 9638, 9654, 9673, 9676, 9678-9680). |
| N15/N20 | The period which relates to the allocation – From / To | period | One `PeriodType` in the schema. Required if N10 is not ticked (9497). ≤12 months (9527). From ≤ box 35 (9526). To ≥ box 30 (9604). |
| N25 | Nominating allocating member | text | PDF prompt: "If the nominated allocating member is a different company at the beginning of the period". Schema: "Previous allocating member name". N25 and N30 must be completed together (9498/9499). |
| N30 | Tax reference | UTR | See N25. |
| N35 | Put an 'X' in box N35 if you are the Ultimate Parent Company of the group | tick | |
| N40 | Enter the name of the Ultimate Parent Company if N35 is not completed | text | Required if neither N10 nor N35 (9500). Forbidden if N35 (9672). |
| N45 | Provide details of the group companies receiving an allocation of allowance (including the allocating company itself, where relevant) | repeating table, 0..∞ | Required if N10 is not ticked (9501). |
| N45A | Name of company | text | 1..1 per row. |
| N45B | Accounting period | period | 1..1. ≤12 months (9674). To ≥ From (9675). |
| N45C | Tax reference* (10 digit taxpayer reference) | UTR | 1..1. |
| N45D | Amount allocated | amount £ (non-zero) | 1..1. |
| N50 | Total | amount £ (non-zero) | = Σ N45D (9677). Required if N10 is not ticked (9508). |
| N55 | If the statement has been authorised put an 'X' in box N55 to confirm | tick | Required if N10 is not ticked (9509). |
| N60 | Full name of person authorising – any person authorised to act on behalf of the company that is authorised to act for the companies within the arrangement | text | Required if N10 is not ticked (9512). |
| N65 | Status of the person authorising | text | Required if N10 is not ticked (9520). |
| — | *Section 2: Joint Venture Companies* (`SN018`, 0..1) | section | For a relevant JV company whose allowance is restricted because of an excluded member and which has received a notional allowance. |
| N70 | Notional allowance claimed | amount £ | Schema **1..1** within Section 2. The PDF shows pre-printed ".00". |
| N75 | Put an 'X' in box N75 if an amount of notional allowance is being allocated in respect of an excluded body | tick | "You must complete table N80 if N75 is completed" (9681, 9683). |
| N80 | Provide details of any company providing an allocation of notional allowance on behalf of an excluded body | repeating table, 0..∞ | Only if N75 is ticked. |
| N80A | Name of the allocating company | text | 1..1. |
| N80B | Tax reference* (if applicable) | UTR | **0..1**. |
| N80C | Amount | amount £ (non-zero) | 1..1. |
| N85 | Total | amount £ (non-zero) | = Σ N80C (9684). Required if N80 is present (9682). |
| N90 | Members of the excluded body's group that are members of the relevant joint venture company (Provide details of the excluded companies that are members of the joint venture company) | repeating table, 0..∞ | |
| N90A | Name of the excluded body | text | 1..1. |
| N90B | Excluded body's tax reference* (if applicable) | text | Schema **1..1**, free text rather than a UTR type, although the PDF says "if applicable". |
| — | *Section 3* (`SN029`) / *Part 1 – Claims to RPDT group relief* (`SN030`) | section | If Section 3 is present, at least one Part is required (9685). Part 1 requires Section 4 (9686). |
| N95 | Details of surrender (claims) | repeating table, **1..∞** | |
| N95A | Name of surrendering company | text | 1..1. |
| N95B | Accounting period of surrendering company* (only if different from this return) | period | 0..1. From ≤ box 35 (9688). ≤12 months (9689). To ≥ From (9690). To ≥ box 30 (9691). |
| N95C | Tax reference** | text | Free text (the company registration number is allowed if there is no UTR). |
| N95D | Amount claimed | amount £ (non-zero) | |
| N100 | Total | amount £ (non-zero) | 1..1. = Σ N95D (9692). "Copy this figure to box N260" (9693, 9861). |
| SN038 | Notice/s of consent attached? **(schema-only)** | tick | Exactly one of SN038 or SN039 (9694). If SN038 = yes, a PDF attachment of type "other" is required (9695). |
| SN039 | Authorisation of claim to group relief for simplified arrangements **(schema-only group)** | group | Contains N105-N115. The claim-authorisation section (SN037) is required on a new return (9687). |
| N105 | If the statement has been authorised put an 'X' in box N105 to confirm | tick | 1..1 within SN039. |
| N110 | Full name of person authorising – any person authorised to act on behalf of the company that is authorised to act for the companies within the arrangement | text | 1..1. |
| N115 | Status | text | 1..1. |
| — | *Part 2: Amounts surrendered as RPDT group relief* (`SN043`) | section | Consent section SN050 is required on a new return (9696). |
| N120 | Details of surrender | repeating table, **1..∞** | |
| N120A | Name of claimant company | text | |
| N120B | Accounting period of claimant company* | period | 0..1. Same four date rules (9697-9700). |
| N120C | Tax reference** | text | |
| N120D | Amount surrendered | amount £ (non-zero) | |
| N125 | Total | amount £ (non-zero) | 1..1. = Σ N120D (9773). |
| SN051 | Type of consent **(schema-only)** | group | At least one of SN052/SN053/SN054 (9792). |
| SN052 | Is a simplified arrangement in force? **(schema-only)** | tick | |
| SN053 | Has CT600N notice of consent been completed? **(schema-only)** | tick | Not allowed together with SN054 (9793). |
| SN054 | Notice/s of consent attached? **(schema-only)** | tick | Not allowed if the declaration SN055 is present (9794). Requires a PDF attachment of type "other" (9795). |
| N130 | Company name (Details of company surrendering relief) | text | 1..1 within the declaration SN055 ("complete the whole of this section if you are using this form as the notice of consent"). |
| N135 | Tax reference | UTR | 1..1. |
| N140/N145 | Accounting period Start date / End date | period | 1..1. ≤12 months (9796). End ≥ Start (9797). |
| SN059 | I certify that all the information I have given on these pages is correct and complete to the best of my knowledge and belief. **(printed text, schema tick)** | tick | 1..1 within SN055. |
| N150 | Full name of person authorising | text | 1..1. |
| N155 | Status | text | 1..1. |
| — | *Part 3 – Claims to RPDT group relief for carried forward losses* (`SN062`) | section | Requires Section 4 (9798). SN069 is required on a new return (9799). |
| N160 | Details of surrender (claims, carried-forward losses) | repeating table, **1..∞** | |
| N160A | Name of surrendering company | text | |
| N160B | Accounting period of surrendering company* | period | 0..1. Date rules 9806, 9815, 9836, 9837. |
| N160C | Tax reference** | text | |
| N160D | Amount claimed | amount £ (non-zero) | |
| N165 | Total | amount £ (non-zero) | = Σ N160D (9838). "Copy this figure to box N265" (9840, 9862). |
| SN070 | Notice/s of consent attached? **(schema-only)** | tick | Exactly one of SN070 or SN071 (9841). Requires a PDF of type "other" (9842). |
| N170 | If the statement has been authorised put an 'X' in box N170 to confirm | tick | Within SN071. The schema text says "If the claim has been authorised". |
| N175 | Name of authorised company | text | Present only in Part 3. |
| N180 | Full name of person authorising – any person authorised to act on behalf of the company that is authorised to act for the companies within the arrangement | text | |
| N185 | Status | text | |
| — | *Part 4: Amounts surrendered as RPDT group relief for carried forward losses* (`SN076`) | section | SN083 is required on a new return (9843). |
| N190 | Details of surrender | repeating table, **1..∞** | |
| N190A | Name of claimant company | text | |
| N190B | Accounting period of claimant company* | period | 0..1. Date rules 9844-9847. |
| N190C | Tax reference** | text | |
| N190D | Amount surrendered | amount £ (non-zero) | |
| N195 | Total | amount £ (non-zero) | = Σ N190D (9848). |
| SN084-SN087 | Type of consent / Simplified arrangement in force? / CT600N notice of consent completed? / Notice/s of consent attached? **(schema-only)** | ticks | Same pattern as Part 2 (9849-9852). |
| N200 | Company name | text | Within the declaration SN088. |
| N205 | Tax reference | UTR | |
| N210/N215 | Accounting period Start date / End date | period | Rules 9853, 9854. |
| SN092 | I certify that all the information … **(printed text, schema tick)** | tick | |
| N220 | Full name of person authorising | text | |
| N225 | Status | text | |
| — | *Section 4: Calculation of RPD profits and RPDT Payable* (`SN095`) | section | Allowed only if N230 or N240 is present (9855). |
| N230 | Adjusted trading profit or loss in relation to the accounting period – Profit | amount £ | Mutually exclusive with N235 (9856/9857). FA22 s38 "A" (positive). |
| N235 | … – Loss | amount £ | Entered as a positive number. "A" (negative). |
| N240 | Amount of any joint venture profits or loss that are attributed to the developer – Profit | amount £ | Mutually exclusive with N245 (9858/9859). FA22 s38 "B". |
| N245 | … – Loss | amount £ | Positive number. |
| N250 | Total of profit – total of (N230+N240) minus (N235+N245) | amount £ | Schema 1..1. **Floored at 0** (9860). |
| N255 | Amount of allowable loss relief | amount £ | FA22 s38 "C" (own carried-forward RPD losses; Sch 7 Pt 1). Capped by s42. |
| N260 | Amount of allowable RPDT group relief claimed | amount £ (non-zero) | "D". = N100 when Part 1 is present (9861). |
| N265 | Amount of allowable RPDT group relief for carried-forward losses claimed | amount £ (non-zero) | "E". = N165 when Part 3 is present (9862). Capped by s42. |
| N270 | RPD profits in relation to the accounting period – net sum of box N250 minus N255, N260 and N265 | amount £ | 1..1. max(0, N250 − N255 − N260 − N265) (9863). |
| N275 | Amount of allowance allocation in relation to the accounting period | amount £ | Allowance from the allocation statement (or the default/stand-alone amount). |
| N280 | Profits chargeable to RPDT – box N270 minus box N275 | amount £ | 1..1. max(0, N270 − N275) (9864). |
| N285 | RPDT payable – Enter this amount in box 497 on the CT600 | amount £p | 1..1. **= N280 × 4%**. No schema rule enforces the 4% (see caveats). |

### Calculations and rules
**Page arithmetic** (from the PDF and schema rules; all amounts are whole pounds except N285):
- `N50 = Σ N45D`; `N85 = Σ N80C`; `N100 = Σ N95D`; `N125 = Σ N120D`; `N165 = Σ N160D`; `N195 = Σ N190D`.
- `N260 = N100` (if Part 1 is present); `N265 = N165` (if Part 3 is present).
- `N250 = max(0, (N230 + N240) − (N235 + N245))`.
- `N270 = max(0, N250 − (N255 + N260 + N265))`.
- `N280 = max(0, N270 − N275)`.
- `N285 = 4% × N280`, in pounds and pence (FA 2022 s33(1)). N285 is then copied to CT600 box 497.

**Statutory model** (FA 2022 Part 2; https://www.legislation.gov.uk/ukpga/2022/3/part/2):
- **RPD profits** (s38): `A + B − C − D − E`.
  - A = adjusted trading profits or losses (s39).
  - B = attributed JV profits or losses (s40).
  - C = RPDT loss relief (Sch 7 Pt 1).
  - D = RPDT group relief (Sch 7 Pt 2).
  - E = RPDT group relief for carried-forward losses (Sch 7 Pt 3).
  - Group relief can reduce the claimant's RPD profits to nil but cannot create a loss (RPDT20100, https://www.gov.uk/hmrc-internal-manuals/residential-property-developer-tax-manual/rpdt20100).
- **Adjusted trading profits** (s39; RPDT20210 https://www.gov.uk/hmrc-internal-manuals/residential-property-developer-tax-manual/rpdt20210). Start from CT trading profits or losses and ignore:
  - (a) profits, losses and capital-allowance allowances or charges from non-RPD activities, apportioned on a just and reasonable basis (s39(3));
  - (b) charitable-trade profits applied to charitable purposes;
  - (c) CT loss relief, group relief and group relief for carried-forward losses (CTA 2010 Parts 4-5A);
  - (d) loan-relationship credits and debits (CTA 2009 Part 5). This is the **interest add-back**: interest and other trading loan-relationship debits do not reduce RPD profits. Unwound "interest" on deferred land consideration is not a loan relationship and stays deductible;
  - (e) derivative-contract credits and debits (CTA 2009 Part 7).
  - Reliefs given as trading deductions and attributable to RPD activity, such as land remediation relief or RDAs, are **not** added back.
  - Transfer pricing applies (FA22 Sch 9 paras 3-4).
- **JV attribution** (s40; RPDT20300 https://www.gov.uk/hmrc-internal-manuals/residential-property-developer-tax-manual/rpdt20300):
  - A member holding ≥10% (group holdings aggregated) is attributed its share of the JV's RPD profits, but only the part of those profits within the JV's own allowance.
  - Where accounting periods differ, the share is apportioned on a time basis (s40(7)).
  - JV losses are attributed only on a joint election, made within 2 years of the end of the JV's accounting period (s40(5), (10), (11)).
- **Loss restriction** (s42; RPDT20440 https://www.gov.uk/hmrc-internal-manuals/residential-property-developer-tax-manual/rpdt20440). It limits C + E (N255 + N265). Let Z be the company's allowance.
  - If `A + B ≤ Z`: max(C + E) = the amount that reduces A + B to £0. Those losses are consumed even though no RPDT was at stake.
  - If `A + B > Z`: max(C + E) = `max(0, (A + B − Z)/2 − D)`.
  - Where s42(3) restricts the deduction, the loss available to carry forward = (total amount otherwise available − relief given) − Z, floored at 0 (s42(4)-(5)).
  - RPD losses arise only from 1 April 2022. They carry forward indefinitely and can be surrendered as carried-forward group relief (RPDT20410).
- **Group relief** (Sch 7 Pts 2-3; RPDT20420/RPDT20430):
  - Stand-alone RPDT versions of CT group relief (CTM80100+) and of group relief for carried-forward losses (CTM80200+).
  - "Group" means the **CT group-relief group** (75%), **not** the s48 allowance group.
  - Consortium relief does not apply.
  - Claims need a notice of consent (Parts 2 and 4 of the page can serve as the notice) unless simplified arrangements under FA98 Sch18 para 77 are in force.
- **Allowance** (s43; RPDT20510 https://www.gov.uk/hmrc-internal-manuals/residential-property-developer-tax-manual/rpdt20510):
  - £25,000,000 for a 12-month period, reduced pro rata for a shorter period.
  - In a group (s48 definition: ultimate-parent / 75% test, the same as CTA10 s269ZZB; RPDT10500), one £25m allowance per period is shared.
  - The allocating member is nominated by the ultimate parent (SI 2022/266 reg 3; RPDT20520). The nomination can be made on CT600N Section 1.
  - The allocating member allocates its "period A" allowance to members whose "period B" ends in or with period A, by an **allowance allocation statement** (reg 5; RPDT20530 https://www.gov.uk/hmrc-internal-manuals/residential-property-developer-tax-manual/rpdt20530). A member is entitled only to the amount in the statement (s43(7)).
  - The statement is due within 12 months of the end of the allocating member's accounting period. It can be amended until the later of 24 months after that period end and 30 days after an enquiry closes, amendment or appeal.
  - The statement must contain: the period dates, the allocating member at the start of the period, a signature, the ultimate parent, the total allowance, the amount allocated to the allocating member itself, and each recipient's UTR, accounting period and amount. These map to N15-N65.
  - If no allocating member is nominated, each RP developer gets £25m ÷ (number of group companies within the charge to CT at the end of the ultimate parent's accounting period), pro rata for short periods (s43(4)-(5)). A non-group company gets £25m, pro rata (s43(6)).
  - When the allocating member changes, the new member's first period is shortened to exclude the overlap, with a pro rata allowance (reg 4; RPDT20520 example: £12.5m).
- **JV notional allowance** (s44; RPDT20610-20630 https://www.gov.uk/hmrc-internal-manuals/residential-property-developer-tax-manual/rpdt20610):
  - A JV's allowance is reduced by the share attributable to an "excluded body", meaning a member outside CT or with exempt trading profits (s44(9)). CT600N guidance describes an excluded body as a non-profit housing company.
  - The excluded body's group has a £25m notional allowance per financial year. It can allocate this to JVs through a notional allowance statement (reg 10), due within 12 months of the end of the FY. This is Section 2 (N70-N90).
  - The restriction is disapplied where it would not change the JV's liability (reg 7).
- **Payments and QIPs** (RPDT30100/RPDT30200/RPDT40200):
  - RPDT is paid with CT, including in quarterly instalments (TMA70 s59E as amended by FA22 Sch 8 para 1) and under group payment arrangements.
  - A company paying RPDT must tell HMRC how much of each payment is RPDT, on or before the payment date, using the quantification notice (FA22 s46). Failure can bring a £300 penalty plus up to £60 a day.
  - HMRC says there is no need to submit the allocation statement before QIPs.
  - Straddling accounting periods: instalments due before 1 April 2022 carry no RPDT; that RPDT moves to the first later instalment date (s51(4)-(5)).
- Worked group example in RPDT20100 (group allowance £25m): G's profits are £38m and its allocated allowance is £14.9m, so £23.1m is chargeable and RPDT = 4% × £23.1m = £924,000. The manual's sentence says "£23,900,000 charged at 4% … £924,000". That figure is a manual typo for £23,100,000.

### Main-return linkage
- **CT600 box 144** "Residential Property Developer Tax (RPDT) – form CT600N" (tick; schema `SupplementaryPages/CT600N`). Rule 9218: if 144 = yes, `[N120]` (CTN) must be present. The box appears on CT600 (2023), (2024), (2025) and (2026) Version 3.
- **N285 → box 497** "Residential Property Developer Tax (RPDT) payable" (£p). Rule 9433: 497 = N285 if N285 is present. Rule 9865: 497 is required if N285 is present. Guide: https://www.gov.uk/guidance/the-company-tax-return-guide#497.
- 497 then flows on:
  - box 500 = 490 + 495 + 496 + 497 (rule 9434); box 500 is required if 497 > 0 (9424);
  - box 510 = 475 + 480 + 500 + 501 + 502 + 505 (guide);
  - box 525 = 510 − 515.
- No other CT600 box is fed by CT600N. Allocation, JV and group-relief data stay on the page.

### Key schema validation rules
- 9495: at least one of Sections 1-4 must be present.
- Section 1 (allocation statement): N10 ticked excludes N15-N65, and N10 absent requires N15/N20, N45, N50, N55, N60 and N65 (9497, 9501, 9508, 9509, 9512, 9520, 9525, 9605…9680). Also N40 is required unless N35 or N10 (9500) and forbidden with N35 (9672). N25 and N30 go together (9498/9499). N50 = Σ N45D (9677). Allocation period ≤12 months and overlapping box 30-35 (9526-9528, 9604).
- Section 2: N75 ⇔ N80 (9681/9683); N85 required if N80 is present (9682); N85 = Σ N80C (9684).
- Section 3: at least one Part if the section is present (9685). Parts 1 and 3 require Section 4 (9686/9798).
  - Totals: 9692, 9773, 9838, 9848. Cross-copies: N260 = N100 (9693/9861); N265 = N165 (9840/9862).
  - Consent and authorisation: exactly one of consent-attached or simplified-arrangements authorisation per claim Part (9694/9841). Consent-type rules 9792-9795 and 9849-9852. A PDF attachment of type "other" is required whenever "notice/s of consent attached" = yes (9695, 9795, 9842, 9852). Authorisation/consent sections are required when the return type is "new" (9687, 9696, 9799, 9843).
  - Counterparty periods: ≤12 months, To ≥ From, overlapping this return's box 30-35 (9688-9691 etc.).
- Section 4:
  - Present only if N230 or N240 is present (9855). A company with **only** RPD losses cannot file Section 4.
  - Profit and loss boxes are mutually exclusive (9856-9859).
  - N250, N270 and N280 are floored at 0 (9860, 9863, 9864).
- Main return: 9218 (144 ⇒ CTN present), 9433 (497 = N285), 9865 (N285 ⇒ 497), 9424/9434 (box 500).

### Worked example
Single stand-alone developer (no group), 12-month accounting period 1 Jan-31 Dec 2025. Only Section 4 is filed.

| Box | Value | Working |
|---|---|---|
| N230 | 40,000,000 | adjusted trading profit of RPD activities (interest and non-RPD activity already stripped out) |
| N240 | 2,000,000 | 20% share of a JV's RPD profits within the JV's allowance |
| N250 | 42,000,000 | 40m + 2m − 0 |
| N255 | 5,000,000 | £5m RPD loss b/f. s42 cap = (42m − 25m)/2 − 0 = £8.5m, so all £5m is usable |
| N260 / N265 | (blank) | no group relief |
| N270 | 37,000,000 | 42m − 5m |
| N275 | 25,000,000 | s43(6) stand-alone allowance, 12 months |
| N280 | 12,000,000 | 37m − 25m |
| N285 | 480,000.00 | 4% × 12,000,000 |

CT600: box 144 = X; box 497 = 480,000.00; box 500 = 480,000.00 (if 490/495/496 are nil). Box 510 then includes 480,000.00 on top of the box 475 CT. For a 9-month period, N275 would be £25m × 9/12 = £18.75m (see caveat on the pro-rata basis).

### Unverified / caveats
- **Guidance typos:**
  - For N285 the CT600N guidance says "Calculate 4% of the amount in box **N285**". It should read N280 (PDF formula and FA22 s33).
  - For N245 the guidance says "Do not complete N245 if box N240 includes a figure", where the parallel wording implies N240/N245. It is harmless.
- **The 4% is not validated.** No schema rule checks N285 = 4% × N280. The rounding convention (pence, half-up?) is unstated. We assume pounds and pence, rounded to the nearest penny.
- **N250 floor vs PDF wording.** The PDF says "total of (N230+N240) minus (N235+N245)", but rule 9860 floors it at 0. A net RPD loss therefore cannot be shown in Section 4. Rule 9855 also blocks Section 4 when only loss boxes would be completed. Losses are carried in the company's records and notified only when used (RPDT20410).
- **Schema cardinality stricter than the PDF:** N5 is 1..1 (Section 1 implies "I am the nominated allocating member"); N70 is 1..1 in Section 2; N90B is required although the PDF says "if applicable"; N95C/N120C/N160C/N190C are free text, not UTR type.
- **Schema-only elements.** SN038/SN039, SN051-SN054, SN059, SN070/SN071, SN084-SN087 and SN092 are schema-only yes/no elements with no printed box number. Implementers must emit them.
- **Cap checks not in the schema:**
  - No rule checks N275 against the allocation statement, or N50 against £25m pro rata. Validate in software.
  - The s42 loss cap on N255/N265 is not validated by the schema. Model it.
- **Pro-rata basis unspecified.** "Reduced by a pro rata amount" (s43(2)(b), (5)(b), (6)(b)) does not say whether days or months are used. HMRC's example (RPDT20520: 6 months → £12.5m) is consistent with either. Days/365 is the usual CT convention; this is unconfirmed.
- **No filing route before CT600N.** Box 497 does not appear in the archived Nov-2022 CT600 guide (web.archive.org snapshot 20221122). CT600 (2023) v3 (published 2023-03-31) appears to be the first version with boxes 144/497. How RPDT for periods filed before April 2023 was reported was not researched. It is not needed for returns filed now.
- **Box 497 on older forms.** CT600 (2024) v3 and CT600 (2025) v3 both carry box 144 and box 497 (checked in `downloads/CT600_2024_v3.pdf` and `downloads/CT600_2025_v3.pdf`). The 2023 CT600 PDF was not downloaded.

---

## CT600P — Company Tax Return – supplementary page: Creative industries

- **Form version(s)**: `CT600P (2026) Version 3 for accounting periods starting on or after 1 April 2015`. The page footer reads `CT600P(2026) Version 3 … HMRC 04/26`.
  - Local files: `downloads/CT600P.pdf` (text in `text/CT600P.txt`) and `downloads/CT600P_Welsh.pdf`.
  - Publication: https://www.gov.uk/government/publications/corporation-tax-creative-industries-ct600p. First published 2026-04-06; Welsh added 2026-04-17. Asset: https://assets.publishing.service.gov.uk/media/69cd2618b5210036050bc66a/CT600P.pdf.
  - Guidance: https://www.gov.uk/guidance/completing-the-ct600p-page-for-creative-industries-reliefs. First published 2026-04-08; reallocated-UK-expenditure section added 2026-07-01. Local copy: `guidance/completing-the-ct600p-page-for-creative-industries-reliefs.md`.
  - Schema: HMRC CT XML spec v1.995, element `[CTP]` = `/IRenvelope/CompanyTaxReturn/CreativeIndustries` (main-return id `[N123]`). See `schema/CTP-boxes.txt` and `schema/CTP-rules.txt`.
- **Applicability**:
  - The form text says APs starting on or after 1 April 2015, so any open period can be amended through it.
  - **CT600P is mandatory for returns submitted on or after 6 April 2026** that claim any creative relief or credit, whether new or amended (https://www.gov.uk/guidance/corporation-tax-creative-industry-tax-reliefs, change note 2026-02-19). The CT online service changes page says: "The Corporation Tax online service has now been updated to support the supplementary page CT600P. If you're claiming one or more of the creative reliefs and credits, you must include the CT600P with your return. This applies to both new and amended claims." (https://www.gov.uk/guidance/changes-and-issues-affecting-the-corporation-tax-online-service; local `guidance/changes-and-issues-affecting-the-corporation-tax-online-service.md`).
  - An earlier plan to require CT600P from April 2025 was withdrawn on 2025-03-13 (change notes on the creative-reliefs and OTR guidance).
  - The predecessor-relief section (P260-P285) is barred for APs whose box 30 is on or after 1 April 2027 (rule 8061).

### Purpose / who must file
- Any company claiming one of the following (guidance "When to complete"):
  - **AVEC**, including the enhanced independent-film rate and the VFX additional credit;
  - **VGEC**;
  - one of the **predecessor reliefs**: Film Tax Relief, High-end TV Tax Relief, Children's TV Tax Relief, Animation Tax Relief or Video Games Tax Relief;
  - one of the **cultural reliefs**: Theatre, Orchestra, or Museums and Galleries Exhibition Tax Relief.
- A company that is not claiming itself but uses AVEC/VGEC **surrendered to it by a group member**, or Step 2 amounts brought forward, completes the pre-Step 1 section (guidance P50).
- Legislation (CTA 2009): Part 14A (AVEC/VGEC, ss.1179A-1179HD), Part 15 (film), 15A (TV), 15B (video games), 15C (theatre), 15D (orchestra), 15E (museums and galleries). See https://www.legislation.gov.uk/ukpga/2009/4/part/14A and https://www.legislation.gov.uk/ukpga/2009/4/part/15.
- The Part 14A regime was introduced by FA 2024 (CREC010100, https://www.gov.uk/hmrc-internal-manuals/creative-industries-expenditure-credit-manual/crec010100). A claim is only valid if the **creatives additional information form** was submitted on or before the day the return is filed (required since 1 April 2024). CT600 box 658 confirms it.
- HMRC manuals:
  - CREC (AVEC/VGEC): https://www.gov.uk/hmrc-internal-manuals/creative-industries-expenditure-credit-manual
  - FPCM (film): https://www.gov.uk/hmrc-internal-manuals/film-production-company-manual
  - TPCM (TV): https://www.gov.uk/hmrc-internal-manuals/television-production-company-manual
  - APCM (animation): https://www.gov.uk/hmrc-internal-manuals/animation-production-company-manual
  - VGDCM (video games): https://www.gov.uk/hmrc-internal-manuals/video-games-development-company-manual
  - TTR (theatre): https://www.gov.uk/hmrc-internal-manuals/theatre-tax-relief
  - OTR (orchestra): https://www.gov.uk/hmrc-internal-manuals/orchestra-tax-relief
  - MGETR (museums and galleries): https://www.gov.uk/hmrc-internal-manuals/museums-and-galleries-exhibition-tax-relief

### Box table
Types:
- `CTwholePoundStructure` = amount £; the PDF pre-prints ".00" or shows no pence cell.
- `CTpoundPenceStructure` = amount £p; the PDF shows a "P" or pence cell.
- `CT_CTnonZeroPoundPenceStructure` = amount £p, non-zero.
- P1-P4 are **not in the schema**. `[CTP]` starts at the AVEC section, and company info comes from CT600 boxes 1, 3, 30 and 35.
- Grid rows (P5, P10, …) are 0..1 groups whose columns are all 1..1, except where noted. Total rows are 1..1 when their section is present.
- For the grid tables each column is its own row below. Column meanings for AVEC/VGEC:
  - A = relevant global expenditure (RGE) for the AP, per s1179CA(2);
  - B = the part of A that is UK expenditure (s1179AB(1)). Reallocated prior-period UK expenditure is excluded from B but may be included in C;
  - C = step 4 "qualifying expenditure for the period";
  - D = step 5 credit;
  - E = VFX additional credit (s1179EC(3)).
- Column meanings for predecessor and cultural reliefs:
  - A = core expenditure for the AP;
  - B = UK core expenditure (European expenditure for video games, and for some cultural APs beginning before 1 April 2025);
  - C = additional deduction;
  - D = losses surrendered;
  - E = payable tax credit claimed.

| Box | Label (verbatim from form) | Type | Notes / calculation |
|---|---|---|---|
| P1 | Company name | text | Print only. |
| P2 | Tax reference | text (UTR) | Print only. |
| P3 | Period covered by this supplementary page (cannot exceed 12 months) – From | date | Print only. |
| P4 | … To | date | Print only. |
| — | *Audio-Visual Expenditure Credit* (`SP001`) | section | Needs at least one of P5-P25 (9015). |
| P5A | Film – Relevant global expenditure for this accounting period | amount £ | "Film" = films that are **not** animated or independent. |
| P5B | Film – Relevant global expenditure for this accounting period that is UK expenditure | amount £ | ≤ P5A (8042). |
| P5C | Film – Qualifying expenditure for this accounting period | amount £ | |
| P5D | Film – Expenditure credit claimed for this accounting period (excluding additional credit for visual effects) | amount £p | If C = 0 then D = 0, else D < C (8043). Rate 34%. |
| P5E | Film – Additional credit for visual effects for this accounting period | amount £p | 0..1. Cannot be negative: a negative VFX amount is deducted from D instead (CREC061460). |
| P10A-P10E | High-end TV programmes – columns A-E as P5 | £ / £ / £ / £p / £p | P10B ≤ P10A (8044). P10D rule 8045. E is 0..1. Rate 34%. |
| P15A | Children's TV programmes – Relevant global expenditure … | amount £ | No column E. |
| P15B | Children's TV programmes – … that is UK expenditure | amount £ | ≤ P15A (8046). |
| P15C | Children's TV programmes – Qualifying expenditure … | amount £ | |
| P15D | Children's TV programmes – Expenditure credit claimed … | amount £p | D < C (8047). Rate 39%. |
| P20A-P20D | Animation – columns A-D | £ / £ / £ / £p | Includes animated films **and** animated TV. P20B ≤ P20A (8048). P20D < P20C (8049). Rate 39%. |
| P25A-P25D | Independent film – columns A-D | £ / £ / £ / £p | BFI low-budget certificate. RGE counted at step 1 is capped at £15m per film (s1179DR), so the credit is ≤ £6.36m per film. P25B ≤ P25A (8050). P25D < P25C (8051). Rate 53%. |
| P30A | Total – col A | amount £ | = P5A + P10A + P15A + P20A + P25A (9016). |
| P30B | Total – col B | amount £ | Sum of the B column (8052). |
| P30C | Total – col C "Copy this figure to box P75" | amount £ | Sum (9017). Requires P75 (9018). |
| P30D | Total – col D "Copy this figure to box P80" | amount £p | Sum (9019). Requires P80 (9020). |
| P30E | Total – col E "Copy this figure to box P81" | amount £p | 0..1. = P5E + P10E (8053). Requires P81 (8054). |
| — | *Video Games Expenditure Credit* (`SP026`) | section | |
| P35A | Video games – Relevant global expenditure for this accounting period | amount £ | 1..1 in section. |
| P35B | Video games – … that is UK expenditure | amount £ | ≤ P35A (8055). |
| P35C | Video games – Qualifying expenditure … | amount £ | |
| P35D | Video games – Expenditure credit claimed … | amount £p | < P35C (8056). Rate 34%. |
| P45A | Total – col A | amount £ | = P35A (9021). |
| P45B | Total – col B | amount £ | = P35B (8057). |
| P45C | Total – col C "Copy this figure to box P85" | amount £ | = P35C (9022). Requires P85 (9023). |
| P45D | Total – col D "Copy this figure to box P90" | amount £p | = P35D (9024). Requires P90 (9025). |
| — | *Pre-step 1 restriction* (`SP035`) | section | Requires the c/f section SP071 (9026). |
| P50 | Step 2 restriction brought forward from previous accounting periods and/or amounts surrendered from group companies | amount £p | 1..1. Prior P210 plus group surrenders received (s1179CD/CE). |
| P55 | Corporation Tax liability | amount £p | = max(0, box 475 − box 530) (9027). |
| P60 | Amount of Step 2 brought forward and surrendered AVEC and VGEC used to discharge Corporation Tax liability – copy this figure to box P230 | amount £p | Guidance: lesser of P50 and P55. The schema only caps it at ≤ P50 and ≤ P55 (9028/9029). Requires P230 (9030). |
| P65 | Amount of Step 2 brought forward AVEC and VGEC carried forward – box P50 minus box P60 – copy this figure to box P195 | amount £p | = P50 − P60 (9031). = P195 (9032). |
| P70 | Remaining Corporation Tax liability carried forward to Step 1 – box P55 minus box P60 – copy this figure to box P100 | amount £p | = P55 − P60 (9033). = P100 (9034). |
| — | *Step 1 – Calculation of AVEC and VGEC set against Corporation Tax liability* (`SP041`) | section | |
| P75 | Qualifying expenditure on which AVEC is claimed in this accounting period | amount £ | = P30C (9036/9037). |
| P80 | AVEC claim for this accounting period (excluding additional credit for visual effects) | amount £p | = P30D (9038/9039). |
| P81 | Additional credit for visual effects for this accounting period | amount £p | = P30E (8058/8059). |
| P85 | Qualifying expenditure on which VGEC is claimed in this accounting period | amount £ | = P45C (9040/9041). |
| P90 | VGEC claim for this accounting period | amount £p | = P45D (9042/9044). |
| P95 | Total AVEC and VGEC for the accounting period – total of boxes P80, P81 and P90 | amount £p | 1..1 (9045). |
| P100 | Remaining Corporation Tax liability | amount £p | = P70. If there is no pre-step 1 section, = max(0, box 475 − box 530) (9035, 9046). |
| P105 | Income Tax deducted from profits (applicable to Corporation Tax liability) | amount £p | ≤ box 515 (9049). ≤ P100 (9050). Just-and-reasonable share of box 515 attributable to box 475. |
| P110 | Maximum amount available for Step 1 set-off – box P100 minus box P105 | amount £p | (9052). |
| P115 | Amount of AVEC and VGEC used to discharge Corporation Tax at Step 1 – copy this figure to box P235 | amount £p | = min(P95, P110). 0 if P110 is absent (9053). Requires P235 (9054). |
| — | *Step 2 – Calculation of notional tax charge* (`SP051`) | section | Required if P95 − P115 > 0 (9004). Needs Step 1 (9055) and the c/f section (9056). |
| P120 | Step 1 balance carried forward to Step 2 – box P95 minus box P115 | amount £p | (9057). |
| P125 | Corporation Tax charge on AVEC and VGEC for this accounting period (AP) | amount £p | P95 × main CT rate. Schema: must be ≥ P95 × main rate at box 30 or box 35 (9058). |
| P130 | Total AVEC and VGEC arising in this AP less Corporation Tax charge on the AVEC and VGEC for this AP – box P95 minus box P125 | amount £p | (9059). |
| P135 | AVEC and VGEC arising in this AP less remaining Corporation Tax liability at Step 1 | amount £p | = max(0, P95 − P110) (9060). Equal to P120. |
| P140 | Step 2 restriction carried forward to next accounting period – copy this figure to box P200 | amount £p | = max(0, P135 − P130) (9063). ≤ P120 (9061). = P200 (9062). |
| — | *Step 3 – AVEC/VGEC to be offset against outstanding Corporation Tax Liabilities* (`SP057`) | section | Required if P120 − P140 > 0 (9005). Needs Step 2 (9064). |
| P145 | Step 2 balance carried forward to Step 3 – box P120 minus box P140 | amount £p | (9065). |
| P150 | Amount used to discharge Corporation Tax liability on another accounting period | amount £p | ≤ P145 (9066). Outstanding (due, unpaid) CT of other APs. |
| — | *Step 4 – Amount surrendered to group member* (`SP060`) | section | Required if P145 − P150 > 0 (9006). Needs Step 3 (9067). |
| P155 | Step 3 balance carried forward to Step 4 – box P145 minus box P150 | amount £p | (9068). |
| P160 | Credit surrendered to group member – copy this figure to box P220 | amount £p | ≤ P155 (9069). Requires P220 (9070) and the P250 table (9071). Optional surrender (s1179CC step 4, s1179CE). |
| — | *Step 5 – Amount used to discharge other company liabilities* (`SP063`) | section | Required if P155 − P160 > 0 (9007). Needs Step 4 (9072). |
| P165 | Step 4 balance carried forward to Step 5 – box P155 minus box P160 | amount £p | (9073). |
| P170 | Amount used to discharge other company liability on this Corporation Tax Self Assessment – copy the figure to box P240 | amount £p | ≤ P165 (9074). Requires P240 and P180 (9075/9076). Examples: s455, CFC, bank levy on this return. |
| P175 | Amount used to discharge any other company liability | amount £p | ≤ P165 − P170 (9077). Examples: PAYE, VAT. Requires P180 (9078). |
| P180 | Total used to discharge other company liability – total of boxes P170 and P175 | amount £p | (9079). |
| — | *Step 6 – Payable AVEC and VGEC* (`SP068`) | section | Required if P165 − P180 > 0 (9008). Needs Step 5 (9080). |
| P185 | Amounts not payable due to section 1179CG CTA 2009 | amount £p | Company in administration or liquidation at the time of claim. ≤ P165 − P180 (9081). |
| P190 | Payable AVEC and VGEC – box P165 minus sum of boxes P180 and P185 – copy this figure to box 886 on the CT600 | amount £p | 1..1 (9083). If ≠ 0, box 886 is required (8060). |
| — | *AVEC and VGEC carried forward* (`SP071`) | section | Only with the pre-step 1 section or Step 2 (9085). |
| P195 | Pre-step 1 restriction | amount £p | = P65 (9086). Guidance: must not include unused group surrenders. |
| P200 | Step 2 restriction | amount £p | 1..1. = P140 (9087). |
| P205 | Surrendered to other group company – copy this figure to box P215 | amount £p | ≤ P195 + P200 (9089). = P215 (9888). Requires the P250 table (9889). |
| P210 | Total carried forward to next accounting period – total of boxes P195 and P200 minus P205 | amount £p | 1..1 (9890). Becomes next period's P50 (part). |
| — | *AVEC and VGEC surrendered* (`SP076`) | section | Needs P160 or P205 (9891). |
| P215 | Step 2 restriction surrendered | amount £p | = P205 (9888, 9892). |
| P220 | Step 4 credit surrendered to group member | amount £p | = P160 (9893/9894). |
| P225 | Total surrendered – total of boxes P215 and P220 | amount £p | 1..1 (9895). |
| — | *Total credits to discharge against liabilities in this Company Tax Return* (`SP080`) | section | |
| P230 | AVEC and VGEC pre-step 1 discharge amount | amount £p | = P60 (9896/9897). |
| P235 | AVEC and VGEC Step 1 discharge amount | amount £p | = P115 (9898/9899). |
| P240 | AVEC and VGEC Step 5 discharge amount for this accounting period | amount £p | = P170 (9938/9939). |
| P245 | Total (boxes P230 to P240) – copy this figure to box 541 on form CT600 | amount £p | 1..1. = P230 + P235 + P240 (9941). = box 541 (9904, 9940). |
| — | *Details of AVEC and VGEC surrendered* (`SP085`) | section | "Complete this section if you are surrendering the credit using box P205 and/or box P160" (9905). |
| P250 | (table) | repeating table, **1..∞** | PDF prints 7 rows. One row per claimant company per claimant AP. |
| P250A | Name of claimant company | text | |
| P250B | Tax reference | UTR | Note the column order: B = tax ref, C = period. The CT600N tables use the opposite order. |
| P250C | Accounting period | period | Start ≤ box 35 (9906). ≤12 months (9907). End ≥ start (9908). End ≥ box 30 (9909). |
| P250D | Amount | amount £p (non-zero) | |
| P255 | Total | amount £p (non-zero) | = Σ P250D (9911). = P225 (9910). |
| — | *Film, high-end TV, children's TV, animation and video games tax relief* (`SP092`) | section | Predecessor reliefs. Needs one of P260-P280 (9912) and requires SP144 (9913). **Not allowed if box 30 ≥ 2027-04-01** (8061). |
| P260A | Film – Total core expenditure for this accounting period | amount £ | Film row **includes animated films**. |
| P260B | Film – UK core expenditure for this accounting period | amount £ | ≤ P260A (8062). |
| P260C | Film – Additional deduction for this accounting period | amount £ | s1200 (100% × lesser of UK core and 80% core). Apportioned if the period of account > 12 months. |
| P260D | Film – Losses surrendered for tax credit | amount £ | s1201. |
| P260E | Film – Tax credit claimed for this accounting period | amount £p | s1202, 25% × D. If D = 0 then E = 0, else E < D (8063). |
| P265A-P265E | High-end TV – columns A-E | £ / £ / £ / £ / £p | ss.1216CG/CH/CI (25%). Rules 8064/8065. |
| P270A-P270E | Children's TV – columns A-E | £ / £ / £ / £ / £p | As P265. Rules 8066/8067. |
| P275A-P275E | Animation – columns A-E | £ / £ / £ / £ / £p | Animated **TV programmes only** (not films). Rules 8068/8069. |
| P280A-P280E | Video games – columns A-E | £ / £ / £ / £ / £p | Column B = **European** expenditure (s1217AE). Additional deduction s1217CG. Sub-contractor costs over the £1m cap are excluded (s1217CF(3A)). Credit s1217CI (25%). Rules 8070/8071. |
| P285A-P285E | Total – columns A-E | £ / £ / £ / £ / £p | Column sums of P260-P280 (9914, 8072, 9915, 9916, 9917). |
| — | *Cultural reliefs* (`SP123`) | section | Needs one of P290-P300 (9918) and requires SP144 (9919). |
| P290A-P290E | Theatre – columns A-E | £ / £ / £ / £ / £p | Core s1217GC. UK core s1217GB(2). Additional deduction s1217J. Loss s1217KA. Credit s1217K. Rules 8073/8074. |
| P295A-P295E | Orchestra – columns A-E | £ / £ / £ / £ / £p | ss.1217RC, 1217RB(2), 1217RE, 1217RH, 1217RG. Rules 8075/8076. |
| P300A-P300E | Museum/gallery exhibition – columns A-E | £ / £ / £ / £ / £p | ss.1218ZCD, 1218ZCC(2), 1218ZCF, 1218ZCI, 1218ZCH. Rules 8077/8078. |
| P305A-P305E | Total – columns A-E | £ / £ / £ / £ / £p | Column sums (9920, 8079, 9921, 9922, 9923). |
| — | *Cultural reliefs and film, high-end TV, children's TV, animation and video games tax relief* (`SP144`) | section | Only if SP092 or SP123 is present (9924). |
| P310 | Total core expenditure for this accounting period – total of boxes P285A and P305A – copy this figure to box 663 on form CT600 | amount £ | 1..1 (9926). = box 663 (9925/9927). |
| P315 | Total additional deduction for this accounting period – total of boxes P285C and P305C – copy this figure to box 665 on form CT600 | amount £ | 1..1 (9929). = box 665 (9928/9930). |
| P320 | Total tax credit claim for this accounting period – total of boxes P285E and P305E | amount £p | 1..1 (9931). |
| P325 | Payable tax credit set-off against other liabilities on this return – copy this figure to box 540 on form CT600 | amount £p | 1..1. ≤ P320 (9933). = box 540 (9932/9934). |
| P330 | Balance payable tax credit – box P320 minus box P325 – copy this figure to box 885 on form CT600 | amount £p | 1..1 (9936). If ≠ 0, box 885 is required (8080). |

### Calculations and rules
**AVEC/VGEC credit amount** (CTA 2009 s1179CA, https://www.legislation.gov.uk/ukpga/2009/4/section/1179CA; CREC060100-061300). The calculation is cumulative and per production. It feeds the P5-P45 columns.
1. RGE to date (Σ over all APs, including prior predecessor-relief periods for switched productions; CREC092200). For independent films, RGE is capped at £15m, with UK expenditure counted first (CREC061100).
2. Deduct non-UK expenditure to get UK expenditure to date. For games switched from VGTR in APs beginning on or after 26 Nov 2025, deduct non-European expenditure for the VGTR periods instead (CREC061100).
3. Qualifying expenditure to date = min(step 2, 80% × step 1).
4. **Qualifying expenditure for the period** = step 3 − step 3 of the last AP for which a credit was claimed on that production. This is column C.
5. Credit = relevant % × step 4. This is column D.
   - Rates: **34%** for film (not animated or independent) and HETV (s1179DV(2)); **39%** for animated film, animated TV and children's TV (s1179DV(3)); **53%** for independent (certified low-budget) film (s1179DV(5A)); **34%** for VGEC (s1179FN).
   - Rate lock-in: once claimed at 34%, a production stays at 34% (s1179DV(4)-(5)). Switching away from 39% or 53% needs withdrawal of the earlier claims (CREC061300, https://www.gov.uk/hmrc-internal-manuals/creative-industries-expenditure-credit-manual/crec061300).
- **VFX additional credit** (s1179EC; CREC061430) is column E. It applies only to HETV and to films that are not animated or independent. Eligible UK VFX costs incurred on or after 1 Jan 2025 get a 39% rate in total and are exempt from the 80% cap. The additional credit = 39% × VFX expenditure to date − the adjusted VFX portion of Chapter-3 credits already claimed − prior additional credit. It can be claimed only from the completion period. A negative amount reduces column D (guidance P5/P10; CREC061460). Claims are allowed from 1 April 2025.
- **Taxable receipt.** The credit (before redemption) is added to the separate production trade's profit (s1179CB), so it raises box 475 and quarterly instalment payments (QIPs). The credit is not a deduction in the QIP calculation (CREC072100).

**Commencement and transition** (CREC091000, https://www.gov.uk/hmrc-internal-manuals/creative-industries-expenditure-credit-manual/crec091000; CREC092100):
- AVEC/VGEC are available on expenditure from 1 Jan 2024, for APs ending on or after 1 Jan 2024. Opt-in is per production.
- They are mandatory for productions that had not started principal photography, or the video-game production phase, by 1 April 2025 (closure date 31 Mar 2025).
- All other productions switch by 31 Mar 2027. The predecessor reliefs cease on 1 April 2027 (hence rule 8061).
- The independent-film 53% rate applies to films starting principal photography on or after 1 Apr 2024, on expenditure from that date. Claims are allowed from 1 Apr 2025.
- A straddling AP is split into notional periods. The page then reports the production in both the AVEC and predecessor tables, as if it were two productions.

**Redemption steps** (s1179CC, https://www.legislation.gov.uk/ukpga/2009/4/section/1179CC; CREC071100-071800; the page's P50-P190). This mirrors the RDEC s104N steps on CT600L, with the old RDEC steps 3-4 folded into Step 2.
- **Pre-Step 1** (s1179CD/CE): Step 2 amounts b/f and group surrenders received discharge this AP's CT **first**, in this order: own b/f; group Step-2 surrenders; group Step-4 surrenders. Surrendered amounts the recipient cannot use are treated as never surrendered.
  - `P55 = max(0, 475 − 530)`
  - `P60 = min(P50, P55)`
  - `P65 = P50 − P60`
  - `P70 = P55 − P60`
- **Step 1**: current-AP credit discharges the remaining CT.
  - `P100 = P70` (or `max(0, 475 − 530)`)
  - `P110 = P100 − P105`
  - `P115 = min(P95, P110)`
- **Step 2** (notional tax at the **main rate**, 25% from FY2023): `P120 = P95 − P115`; `P125 = P95 × main rate`; `P130 = P95 − P125`; `P135 = max(0, P95 − P110)`; `P140 = max(0, P135 − P130)`.
  - P140 is the amount withheld. It is carried forward to the pre-Step 1 restriction of later APs indefinitely, or surrendered to a group member in this AP or later ones (P205). It is lost on wind-down (CREC071400).
  - Effect: a loss-maker nets 75% of the credit in cash. A taxpayer with CT of at least 75% of the credit is unaffected.
- **Step 3**: `P145 = P120 − P140`. P150 (≤ P145) discharges outstanding CT of other APs, in the company's chosen order.
- **Step 4**: `P155 = P145 − P150`. P160 (≤ P155) is an optional surrender to a 75% group member (CTA 2010 s152; CREC072000).
  - With non-coterminous APs, the usable surrender is apportioned by overlap (s1179CE).
  - Payments for surrendered credit, up to the amount surrendered, are ignored for CT if made on or after 26 Nov 2025.
- **Step 5**: `P165 = P155 − P160`. `P180 = P170 + P175`, where P170 = other liabilities on this return (s455, CFC, bank levy) and P175 = any other HMRC liability (PAYE, VAT).
- **Step 6**: `P190 = P165 − P180 − P185`.
  - Nothing is payable if the company is in administration or liquidation when it claims (s1179CG; P185).
  - HMRC may withhold payment while PAYE/NIC/s966 liabilities for periods ending in the AP are outstanding (s1179CH; CREC071800). This is not shown on the page.
- **Carried forward and surrendered**:
  - `P195 = P65`; `P200 = P140`; `P205 ≤ P195 + P200`; `P210 = P195 + P200 − P205`
  - `P215 = P205`; `P220 = P160`; `P225 = P215 + P220 = P255 = Σ P250D`
  - `P230 = P60`; `P235 = P115`; `P240 = P170`; `P245 = P230 + P235 + P240` → box 541.

**Predecessor reliefs** (Parts 15/15A/15B; FPCM/TPCM/APCM/VGDCM):
- Each production is a separate trade.
- **Additional deduction** = 100% × E, where E = lesser of UK (games: European) core expenditure and 80% of total core expenditure, cumulative less prior deductions (s1200 film, https://www.legislation.gov.uk/ukpga/2009/4/section/1200; s1216CG TV; s1217CG games). This is column C, apportioned to the AP when the period of account exceeds 12 months.
- The surrenderable loss (s1201/1216CH/1217CH) is capped by reference to E. It is column D.
- **Payable tax credit = 25%** of the loss surrendered (s1202 film; s1216CI TV; s1217CI games). This is column E.

**Cultural reliefs** (Parts 15C/15D/15E; TTR/OTR/MGETR manuals):
- **Additional deduction** = lesser of 80% of total core costs and UK core costs. For productions or APs before 1 April 2024, the UK+EEA ("European") core costs are used instead (transition: TTR50090, OTR60070, MGETR60070). This is column C.
- **Payable credit** on the surrendered loss (column E). Rates by period:

  | Period | Theatre non-touring / touring | Orchestra | Museums & galleries non-touring / touring |
  |---|---|---|---|
  | Productions before 27 Oct 2021 | 20% / 25% | 25% | 20% / 25% |
  | 27 Oct 2021 – 31 Mar 2025 (FA 2022 ss.17-21, extended by F(No.2)A 2023 s14) | 45% / 50% | 50% | 45% / 50% |
  | APs beginning on or after 1 Apr 2025 (permanent) | **40% / 45%** | **45%** | **40% / 45%** |

  - Sources for the rates: https://www.gov.uk/government/publications/cultural-relief-rate-rises-for-theatre-orchestra-and-museums-and-galleries-exhibition-tax-reliefs; https://www.gov.uk/government/publications/two-year-extension-of-the-higher-rates-for-theatre-orchestra-and-museums-and-galleries-exhibition-tax-reliefs.
  - The permanent rates were set by F(No.2)A 2024 s16, which substituted s1217K(4) with effect for APs beginning on or after 1 Apr 2025 (commentary on https://www.legislation.gov.uk/ukpga/2009/4/section/1217K). Current text: s1217K(4) 45% touring / 40% not touring; s1217RG(4) 45%; s1218ZCH(4) 45% / 40% (https://www.legislation.gov.uk/ukpga/2009/4/section/1218ZCH).
  - MGETR credit is capped at £80,000 per non-touring and £100,000 per touring exhibition (s1218ZCK).
  - The planned 2025-26 taper (30/35/35) and the return to 20/25/25 were superseded by the permanent rates.
- Cultural and predecessor-relief credits are **not** subject to the redemption steps. P325 is the part set against liabilities on this return (→ box 540). P330 is the balance payable (→ box 885).

**Before CT600P: CT600 (2024) and (2025) v3.** Box numbers and the treatment that applied before CT600P became mandatory on 6 Apr 2026.

- **CT600 (2024) Version 3** (HMRC 04/24; `downloads/CT600_2024_v3.pdf`). It has no box 96, 541, 614, 658, 663 or 886. Per the guide snapshot of 2024-11-26 (web.archive.org/web/20241126221425):
  - box 540 "Creatives tax credit" = the total of all creative credits **including AVEC and VGEC**, before set-off;
  - box 665 "Creative qualifying expenditure and/or additional deduction" = the predecessor-relief additional deduction **plus** AVEC/VGEC step-4 qualifying expenditure. Box 670 = 660 + 665;
  - box 885 "Payable creative tax credit" = all payable credits including AVEC/VGEC.
- **CT600 (2025) Version 3** (HMRC 04/25; `downloads/CT600_2025_v3.pdf`):
  - It already prints box 96 "Creative industries – form CT600P", 541, 614, 658, 663 and 886. Box 650's label then covered "and/or for all creatives claims". The CT600 (2026) v3 label drops that phrase.
  - The claims themselves went directly on the CT600, per the guide snapshots of 2025-06-02, 2025-09-18 (local `guidance/the-company-tax-return-guide_wayback-20250918.md`) and 2025-09-29:
    - 540 = total predecessor and cultural tax credits claimed (ss.1202/1216CI/1217CI/1217K/1217RG/1218ZCH), before set-offs;
    - 541 = Step-2 amounts b/f used + group Step-2/Step-4 surrenders used + the step-5 credit for the period (s1179CA) + VFX additional credit;
    - 663 = predecessor and cultural core expenditure, excluding AVEC/VGEC productions;
    - 665 = predecessor and cultural additional deduction;
    - 885 = payable predecessor and cultural credits (must not exceed box 570);
    - 886 = the Step 6 AVEC/VGEC amount;
    - 614 = AVEC/VGEC surrendered to this company.
  - The meaning of 540 and 541 changed with CT600P. From April 2026 they are the amounts **used to discharge liabilities** on the return (CREC083000, https://www.gov.uk/hmrc-internal-manuals/creative-industries-expenditure-credit-manual/crec083000), not the gross claim.

### Main-return linkage
- **CT600 box 96** "Creative industries – form CT600P" (tick; schema `SupplementaryPages/CT600P`). Rule 9872: 96 = yes ⇒ `[N123]` present. Printed on CT600 (2025) and (2026) Version 3.

| CT600P box | CT600 box | Rules | Notes |
|---|---|---|---|
| P310 | **663** Creatives core expenditure (£) | 9925, 9927 (P310 = 663), 9003; 8003 (663 needs box 96) | Only predecessor and cultural reliefs (CREC083000). |
| P315 | **665** Creatives additional deduction (£) | 9928, 9930, 9009; 8004 | 670 = 660 + 665 (9365). |
| P325 | **540** Creatives tax credit (£p) | 9932, 9934, 9010; 8001 | 545 = 530 + 535 + 540 + 541 (9360). 570 = max(0, 545 − 525) (9261). |
| P245 | **541** AVEC and VGEC (£p) | 9940, 9904, 9012; 8002 | Same 545 flow. |
| P330 | **885** Payable creatives tax credit (£p, non-zero) | 8080, 9011, 8015-8018 (885 = P330 if > 0; absent if P330 = 0; needs box 96) | Bank boxes 920-940. |
| P190 | **886** Payable AVEC and VGEC (£p, non-zero) | 8060, 9002, 8019-8022 | Bank boxes 920-940. |

- **Boxes read by the page**: 475 and 530 (for P55/P100; 9027, 9035, 9046), 515 (P105 ≤ 515; 9049), and 30/35 (main-rate test 9058; period tests 9906-9909; 8061).
- **Related CT600 boxes with no schema cross-check to CT600P**:
  - box 614 "AVEC and VGEC surrendered to this company". This is logically the group-surrender part of P50.
  - box 658 "Creatives additional information form" tick. The claim is invalid without the form, even if the box is not ticked (CREC083000).
  - box 650 (SME/creatives tick on the 2025 form).

### Key schema validation rules
- 9001: CT600P needs at least one of pre-step 1, Step 1, or SP144.
- The Step sections cascade: 9004-9008 require the next Step when a positive balance remains. 9055, 9064, 9067, 9072 and 9080 require the previous Step. 9026, 9056 and 9085 govern the carried-forward section.
- Every "copy to" is an equality rule: P30C/D/E → P75/P80/P81; P45C/D → P85/P90; P60 = P230; P65 = P195; P70 = P100; P115 = P235; P140 = P200; P160 = P220; P170 = P240; P205 = P215; P225 = P255 = Σ P250D.
- Credit caps:
  - AVEC/VGEC: D < C (8043-8051, 8056), with D = 0 allowed only when C = 0 (film and HETV rows).
  - Predecessor and cultural reliefs: E < D, or E = 0 when D = 0 (8063-8078).
  - UK expenditure ≤ global expenditure in every row (column B ≤ A).
- **Known online-service defect** for P260-P305 (CT online service changes page). The service rejects zero in both columns D and E, although rule 8063 etc. literally allow 0/0. The workaround is to enter **£1.00 in column D**, which HMRC says does not affect the claim. A fix is promised for April 2027. The AVEC/VGEC sections are not affected.
- P55/P100 must reproduce `max(0, 475 − 530)` exactly (9027/9046). P125 ≥ P95 × main rate (9058). P115 = min(P95, P110) (9053). P140 = max(0, P135 − P130) (9063).
- 8061: no predecessor-relief section when box 30 ≥ 2027-04-01.

### Worked example
The company is a loss-making HETV producer with one production, AP 1 Apr 2025 – 31 Mar 2026, main rate 25%. It is not in a group and has no b/f amounts, so the pre-step 1 section is omitted.

| Box | Value | Working |
|---|---|---|
| P10A | 1,000,000 | RGE this AP (first AP of the production) |
| P10B | 900,000 | UK part |
| P10C | 800,000 | min(900,000, 80% × 1,000,000) − 0 prior |
| P10D | 272,000.00 | 34% × 800,000 |
| P30A-D / P75 / P80 | 1,000,000 / 900,000 / 800,000 / 272,000.00 / 800,000 / 272,000.00 | totals and copies |
| P95 | 272,000.00 | P80 + P81 (nil) + P90 (nil) |
| P100 | 20,000.00 | box 475 = 20,000.00 (CT on the taxable credit net of trade loss); box 530 nil |
| P105 / P110 | 0 / 20,000.00 | |
| P115 | 20,000.00 | min(272,000, 20,000). This is P235 |
| P120 | 252,000.00 | 272,000 − 20,000 |
| P125 | 68,000.00 | 25% × 272,000 |
| P130 | 204,000.00 | 272,000 − 68,000 |
| P135 | 252,000.00 | 272,000 − 20,000 |
| P140 | 48,000.00 | 252,000 − 204,000. This is P200 and is carried forward |
| P145 / P150 | 204,000.00 / 0.00 | no other CT outstanding |
| P155 / P160 | 204,000.00 / — | no group |
| P165 / P170 / P175 / P180 | 204,000.00 / 0.00 / 0.00 / 0.00 | |
| P185 / P190 | — / 204,000.00 | → box 886 |
| P200 / P210 | 48,000.00 / 48,000.00 | next AP's P50 |
| P235 / P245 | 20,000.00 / 20,000.00 | → box 541 |

CT600 entries: box 96 = X; box 541 = 20,000.00; box 545 = 20,000.00. Box 525 = 20,000.00 (box 510 − 515), so box 570 = 0. Box 886 = 204,000.00, plus bank details in 920-940. Box 658 = X.

Economic check: 20,000 + 204,000 = 224,000 cash or relief now. A further 48,000 is withheld until a future CT liability or a group surrender.

Cultural add-on (the same return could also carry it). Theatre, non-touring, AP beginning on or after 1 Apr 2025:
- P290A = 500,000; P290B = 450,000; P290C = min(80% × 500,000, 450,000) = 400,000.
- P290D = 300,000 loss surrendered; P290E = 40% × 300,000 = 120,000.00.
- P305 has the same values, so P310 = 500,000 → 663 and P315 = 400,000 → 665.
- P320 = 120,000.00. If none of it is set against liabilities on this return: P325 = 0.00 → box 540 = 0.00 (P325 is 1..1, and 9932 then requires 540). P330 = 120,000.00 → box 885.

### Unverified / caveats
- **Unused group surrenders in P50.** P50 may include group surrenders, and P195 must equal P65 = P50 − P60. But the guidance says P195 "cannot include any amount of surplus surrender(s) from group companies", and CREC071100 treats unused received amounts as never surrendered. So in practice only the **usable** part of a received surrender (≤ P55 after own b/f) can go into P50. Any excess would wrongly show as the company's own c/f. The schema has no rule separating the two.
- **P60 is not enforced as the minimum.** The guidance says P60 = lesser of P50 and P55. The schema only enforces P60 ≤ P50 and P60 ≤ P55. Set-off at the pre-Step 1 restriction is mandatory in law (CREC071400), so compute the minimum.
- **P125 is an inequality.** The schema says P125 must be *not less than* P95 × main rate at box 30 **or** box 35 (9058), not an equality. For APs straddling a main-rate change, the statute uses "the main rate", and how to apportion is not stated on the form. Since FY2023 the rate is 25%, so this is moot for AVEC (from 2024) unless rates change.
- **No 34/39/53% check.** No schema rule checks D against the rate × C (only D < C). No rule checks P185 eligibility, or 614 against P50.
- **Credit caps are not validated:** the £15m independent-film RGE cap (credit ≤ £6.36m per film), the MGETR £80k/£100k per-exhibition credit caps (s1218ZCK), and the video-games £1m sub-contractor cap.
- **Surrenderable-loss formula not re-read.** The predecessor-relief surrenderable-loss formula (s1201/1216CH/1217CH) was not re-read in full here. It is stated from the guidance's section references.
- **Pre-2021 cultural rates.** The pre-27 Oct 2021 rates and the 2021-2025 temporary rates are taken from HM Treasury policy papers (TIINs), not from the enacted apportionment rules (FA 2022 s17-21 split straddling APs). Model those from legislation if older APs must be supported.
- **MGETR sunset.** The 2023 policy paper said MGETR would sunset after 31 Mar 2026. Current gov.uk guidance and s1218ZCH show 40%/45% with no end date, which implies a later extension (likely F(No.2)A 2024). The exact sunset date was **not verified**.
- **Transitional VGEC step 2.** It applies only to APs beginning on or after 26 Nov 2025 (CREC061100). The effect on column B vs C for switched games follows the guidance's "reallocated UK expenditure" note (added 2026-07-01).
- **Period rules not checked.** The P3/P4 "cannot exceed 12 months" limit is print-only. There is no P-page period in the schema.

---

# (c) Relief rules

## Relief rules (with worked examples and citations)

Manual pages cited here are saved under `manuals/` (fetched 2026-09-28 via the gov.uk Content API).

---

### Group relief (CTA 2010 Part 5) and group relief for carried-forward losses (CTA 2010 Part 5A)

**Eligibility — group condition** (CTA10 s131, s152; CTM80150, CTM80151)

- Both companies must be **"UK related"**, meaning either:
  - UK resident; or
  - non-resident but within the charge to CT (UK PE trade; UK land dealing from 5 Jul 2016; UK property business from 6 Apr 2020).
- One company must be a **75% subsidiary** of the other, or both must be 75% subsidiaries of a third company (which may be resident anywhere). "75% subsidiary" means:
  - ≥ 75% beneficial ownership of **ordinary share capital**, direct or indirect, multiplied through the chain (s1154–s1156);
  - **plus** ≥ 75% entitlement to **profits available for distribution** and to **assets on a winding-up** (s151(4), Part 5 Ch 6).
- Anti-arrangement rules (s154–156): companies are not grouped if arrangements exist for one to leave the group or come under different control.
- Worked example (CTM80151): A holds 90% of B and 60% of C; B holds 40% of C. A's interest in C = 60% + 90%×40% = 96%, so A, B and C are all in the group.

**Consortium condition** (CTA10 s132, s133, s153; CTM80530, CTM80540)

- The company "owned by a consortium" can be:
  - a trading company; or
  - a holding company of 90% trading subsidiaries; or
  - a 90% trading subsidiary of such a holding company.
- **≥ 75% of its ordinary share capital** must be beneficially owned by companies ("members") that **each own ≥ 5%**.
- It must not be a 75% subsidiary of any one company.
- A member's relief is capped at the **ownership proportion**: the lowest of its percentage of share capital, profits, assets and (for APs from 12 Jul 2010) votes, time-weighted over the overlapping period (s143 for claims up; s144 for claims down).
- Relief can flow **both ways**: from the consortium company to members, and from members to the consortium company.
- Consortium condition 2/3 extends this to companies in the same group as a member.

**What can be surrendered** (s99; CTM80110–80143)

| Category | Surrenderable when? | Surrenderer's CT600 box / CT600C box |
|---|---|---|
| Trading loss (s99(1)(a); s100: the loss of the period, excluding carry-forwards) | Always, even if the surrenderer has other profits | 785 / C45 |
| Excess non-trade capital allowances (s99(1)(b), s101) | Always | 840 / C50 |
| Non-trading loan-relationship deficit (s99(1)(c)) | Always | 800 / C55 |
| Qualifying charitable donations (s99(1)(d)) | Only the excess over the surrenderer's "profit-related threshold" (s105) | 845 / C60 |
| UK property business loss (s99(1)(e), s102) | As above | 810 / C65 |
| Excess management expenses (s99(1)(f), s103) | As above | 855 / C70 |
| Non-trading loss on intangible fixed assets (s99(1)(g), s104) | As above | 835 / C75 |

- **s105 restriction**: the four "relevant amounts" (donations, property losses, management expenses, non-trading intangibles losses) may only be surrendered to the extent that together they exceed the surrenderer's **gross profits of the period**, plus CFC apportionments for periods ending on or after 20 Mar 2013.
- Gross profits are measured ignoring all current-period losses and deficits and all amounts from other periods.
- The surrendered excess is deemed to come out in this order (s105(4); CTM80143):
  1. donations;
  2. UK property losses;
  3. management expenses;
  4. non-trading intangibles losses.
- For consortium claims there is an extra restriction on trading losses (CTM80570).

**Claimant side: available total profits and set-off order** (s137; CTM80145, CTM80400)

- Group relief is deducted from the claimant's **total profits** of the claim period, **after**:
  - all its own current-period reliefs that are actually claimed or automatic (s62(3) property losses, s459(1)(a) NTLR deficits, s1219 management expenses, s753 intangibles losses, qualifying charitable donations);
  - its **own current-year trading loss relief (s37(3)(a)) and excess CAs (CAA01 s260(3)(a)), deducted whether or not claimed**.
- It is **not** reduced by carry-backs from later periods (s37(3)(b), s260(3)(b), s459(1)(b)).
- On the CT600 this is the box sequence **235 → 295 → 300 → 305 (donations) → 310 (group relief) → 312 (group relief for carried-forward losses) → 315**. The schema caps are:
  - 310 ≤ 300 − 305 (rule 9337);
  - 312 ≤ 300 − 305 − 310 (rule 9374).
- A claim may be for less than the full loss (s137(2)). No amount can be relieved twice (s137(7)).
- A payment for group relief, up to the amount surrendered, is ignored for tax (s183).

**Non-coterminous periods and joining/leaving** (s138–s142; CTM80210–80270)

- The claim is limited to the **overlapping period**: the part of both APs during which the companies are grouped.
- Relief is the lower of:
  - the surrenderer's **unused part of the surrenderable amounts** = time-apportioned surrenderable amount for the overlap, less prior surrenders attributable to the overlap;
  - the claimant's **unrelieved part of available total profits** = time-apportioned available profits for the overlap, less prior claims attributable to the overlap.
- Time apportionment is the default. Another just and reasonable method (e.g. management accounts) is allowed if time apportionment would be unjust (s141(3); CTM80260, CTM80265).

**Group relief for carried-forward losses** (CTA10 Part 5A, s188AA–s188FD; CTM82000–82190)

- Only losses **arising on or after 1 April 2017** can be surrendered:
  - carried-forward trading losses (s45A);
  - NTLR deficits (CTA09 s463G);
  - UK property losses;
  - management expenses;
  - non-trading intangibles losses.
- These go into CT600C Part 4 (C160–C180). Pre-April-2017 losses cannot be surrendered (s188BC).
- The surrenderer cannot surrender an amount it could deduct from its own total profits for that period (s188BE). It also cannot surrender if it has no income-generating assets at the period end (s188BF), or where an investment business has become small or negligible (s188BD).
- The claimant must use its own carried-forward losses first (CTM82010).
- Relief is limited to the lower of the unused surrenderable amount and the claimant's **relevant maximum** for the overlapping period, less prior claims (s188DB; CTM82110).
- It is also within the **loss-restriction cap** (CTA10 s269ZD): carried-forward relief ≤ £5m deductions allowance + 50% of profits above it. The £5m is shared across the group through a group allowance allocation statement (s269ZR; guide box 312).
- On the CT600 the claim is box **312** = C130.

**Claims procedure** (FA98 Sch 18 paras 66–77)

- The claim is made in the claimant's return (CT600C Part 1/3) and needs the surrenderer's **notice of consent** (Part 2/4, or a separate notice) unless simplified arrangements (SI 1999/2975) apply. Consortium claims need the consent of every member.
- **Time limit (para 74)**: the claim can be made or withdrawn up to the latest of:
  - the first anniversary of the claimant's filing date;
  - 30 days after an enquiry closes;
  - 30 days after an HMRC amendment;
  - 30 days after an appeal is determined.
  
  Source: https://www.legislation.gov.uk/ukpga/1998/36/schedule/18/paragraph/74

**Worked example 1 — coterminous current-period relief (APs to 31 Dec 2025)**

P owns 100% of S. S has a trading loss of £200,000 and no other income. P has box 235 = £300,000, no deductions, and donations of £10,000.

| Return | Boxes |
|---|---|
| S's CT600 | 780 = 200,000; 785 = 200,000; box 105 ticked |
| S's CT600C | C45 = 200,000; C80 = 200,000; C85 row (P, P's UTR, 200,000); C90 = 200,000; C95–C120 consent completed |
| P's CT600 | 300 = 300,000; 305 = 10,000; 310 = 200,000; **315 = 90,000**; box 105 ticked |
| P's CT600C | C5 row (S, S's UTR, 200,000); C10 = 200,000 |

P's cap is 300,000 − 10,000 = 290,000, so the full £200,000 is allowable. P then has profits of £90,000; with one associated company the limits are £25,000 / £125,000, so marginal relief applies.

**Worked example 2 — non-coterminous periods** (CTM80255)

- D (loss £120,000, 12 months to 30 Sep 2011) surrenders to C (profit £5,000, 6 months to 30 Jun 2011). Overlap = 6 months. Unused surrenderable = 6/12 × 120,000 = 60,000; C's available = 5,000; relief = **5,000**.
- A (profit £72,000, 12 months to 31 Dec 2011) then claims from D. Overlap = 9 months. Surrenderable = 9/12 × 120,000 = 90,000, less C's prior claim attributable to the common period of 5,000 = 85,000. A's available = 9/12 × 72,000 = 54,000. Relief = **54,000**.

**Worked example 3 — consortium**

X Ltd owns 40% of the shares of JV Ltd, is entitled to 40% of its profits and assets, and holds 35% of the votes. JV (owned by consortium companies holding ≥ 75%, each ≥ 5%) has a trading loss of £100,000. X can claim at most 35% × 100,000 = **£35,000** (the lowest proportion). X enters the claim in C5, and JV's C85 shows X for £35,000.

---

### R&D relief

#### Scheme map by accounting period (AP) start date

| AP begins | Scheme(s) | Rates | Payable credit and cap | CT600 / CT600L |
|---|---|---|---|---|
| Before 1 Apr 2024 — large company or ineligible SME | **Old RDEC** (CTA09 Pt 3 Ch 6A, s104A–s104Y) | Credit rate on qualifying expenditure: 11% (1 Apr 2015–31 Dec 2017), 12% (1 Jan 2018–31 Mar 2020), 13% (1 Apr 2020–31 Mar 2023), **20% (from 1 Apr 2023)**; ring fence 49%. Rate follows the date expenditure is incurred, so straddling periods are split (CIRD89710) | Step 2 notional tax at the **main rate** (time-apportioned; 19%/25%). Step 3 cap = company's expenditure on R&D workers' PAYE/NIC plus connected EPWs (CIRD89790). Excess over the cap is carried forward | Box 655 (large) or 650 (SME claiming RDEC for subcontracted/subsidised work → L185/L190); CT600L Steps 1–7; L125 → 880; L210 → 530 |
| Before 1 Apr 2024 — SME | **SME scheme** (CTA09 Pt 13, s1039–s1062) | Additional deduction 130% (enhanced 230%) for expenditure 1 Apr 2015–31 Mar 2023; **86% (186%) from 1 Apr 2023**. Payable credit 14.5% of the surrenderable loss before 1 Apr 2023; **10% from 1 Apr 2023**, or **14.5% for R&D-intensive SMEs (intensity ≥ 40%)** for APs ending ≥ 1 Apr 2023 and beginning < 1 Apr 2024 (FA 2024, retrospective; CIRD123000, CIRD127000) | PAYE cap for APs beginning ≥ 1 Apr 2021: £20,000 + 3 × (PAYE/NIC of company + relevant connected companies), unless the s1058D exemption applies (CIRD140000 predecessor; L170 rule 9642) | 650 (+653 if intensive, APs ending > 31 Mar 2023), 659 qualifying expenditure, 660 enhanced expenditure, 675 subcontracted-from-large; CT600L L166–L180; L180 → 875 |
| **On or after 1 Apr 2024** — any company | **Merged-scheme RDEC** (CTA09 Pt 13 Ch 1A, s1042A–s1042O) | **20%** (ring fence 49%) of qualifying Ch 1A expenditure (s1042G; CIRD115000). Taxable as trading income | Step 2 notional tax at **25% (main rate) if profits before RDEC are chargeable at the main rate (including marginal relief cases), otherwise 19% (small profits rate)**, so loss-makers and small-profit companies use 19% (s1042K; CIRD112100). Step 3 **PAYE cap = £20,000 + 300% of relevant PAYE/NIC**, with £20,000 time-apportioned for short APs (s1112B). Exempt if s1112E conditions A and B are met: the company creates or manages IP through its own employees, **and** connected-party EPW/subcontractor spend is ≤ 15% of qualifying spend. Excess over the cap is carried forward as next-period RDEC | CT600L Steps 1–7 (L71–L75 PAYE data on the 2026 form); L125 → 880; L210 → 530; RDEC included in box 155 |
| **On or after 1 Apr 2024** — loss-making, R&D-intensive SME | **ERIS** (CTA09 Pt 13 Ch 2, s1044, s1045ZA, s1058) | Additional deduction **86%** (enhanced 186%). Payable credit **14.5%** of the surrenderable loss = min(186% × qualifying expenditure, unrelieved trading loss) (s1055, s1056). Intensity condition: relevant R&D expenditure ≥ **30%** of total relevant expenditure, including connected companies (s1045ZA). There is a one-year grace period if the company met the condition and claimed in its last 12-month AP. The company must make a trading loss before the additional deduction (CIRD121000, CIRD122000, CIRD123000) | Same PAYE cap (s1112B), shared with any merged-RDEC claim: L75 ≤ 3 × (L168 + L169) + £20,000 − L170 (rule 8039). Credit above the cap is **invalid**, not carried forward (CIRD140000) | Boxes 650 + **653**, 659 (= L166), 660, 670; CT600L L166–L180; L180 → 875 |

Additional points on the scheme map:

- An ERIS-eligible company may choose the merged RDEC instead, but cannot claim both on the same expenditure (merged-scheme guidance).
- Expenditure incurred before 1 Apr 2023 but claimed in a post-2024 AP: ERIS uses the old SME rates for the additional deduction with a 14.5% credit (CIRD127000).
- Overseas restriction (APs from 1 Apr 2024): payments to overseas contractors and externally provided workers generally do not qualify, subject to exceptions (CIRD150000). NI-registered ERIS claimants are exempt from this restriction.
- Qualifying cost heads (CIRD131000+): staffing, software, **data licences and cloud computing (from 1 Apr 2023)**, consumables, EPWs, contractor payments, clinical trial subjects.
- **Payment restrictions**:
  - Step 7 / ERIS credits are paid to the company only (nomination and assignment restriction, CTA09 s1142C/D; CIRD81805). The CT600 box 943 exceptions apply.
  - A going-concern condition applies (s1112F).
  - No payment while an enquiry is open or PAYE/VAT is unpaid (s1112H).

#### Filing prerequisites (both schemes)

- **Claim notification** (FA98 Sch 18 para 83E–83F; box 656), for APs beginning ≥ 1 Apr 2023:
  - Required if this is a first claim, or no claim was made in the 3 years before the last day of the notification window.
  - Also required if a previous claim was removed by HMRC, or was made by an amendment received on or after 1 Apr 2023 for an AP beginning before 1 Apr 2023.
  - The window runs from the first day of the **period of account** to **6 months after its end**.
  - Source: https://www.gov.uk/guidance/tell-hmrc-that-youre-planning-to-claim-research-and-development-rd-tax-relief
- **Additional information form (AIF)** (box 657): mandatory for **all** R&D relief and RDEC claims made on or after **8 Aug 2023**. It must be submitted before, or on the same day as, the return, otherwise the claim is removed. Source: https://www.gov.uk/guidance/submit-detailed-information-before-you-claim-research-and-development-rd-tax-relief
- **Claim deadline**: 2 years from the end of the AP. Put differently, 24 months from the end of a period of account of ≤ 18 months, or 42 months from the start of a longer one. Source: https://www.gov.uk/guidance/make-a-claim-for-rd-tax-relief-on-your-company-tax-return
- **Bank details** (920–940) are expected when 875 or 880 is completed (guide, Sept 2025 update).

#### Worked example R1 — merged RDEC, profit-making (AP 1 Apr 2024 – 31 Mar 2025, standalone company)

Profits before RDEC are £1,000,000 and qualifying expenditure is £500,000, so RDEC = 20% = £100,000. This is taxable, giving box 155/315 = £1,100,000.

- **Tax**: box 440/475 = 1,100,000 × 25% = £275,000.
- **CT600L**:
  - Step 1: L10 = 500,000; L15 = 100,000; L25 = 100,000; L30 = 275,000; L35 = 0; L40 = 275,000; L45 = min(100,000, 275,000) = 100,000 → L195.
  - L50 = 0, so Steps 2–7 are not needed.
  - L210 = 100,000.
- **CT600**:
  - 530 = 100,000; 545 = 100,000; 525 = 275,000.
  - 570 = 0 (545 < 525).
  - 600 = 275,000 − 100,000 − 595 = £175,000 outstanding if nothing has been paid.
- Net benefit = £100,000 − 25% tax = £75,000 (15% of spend).
- Ticks: 142, 656 (if required), 657, and 650 or 655 as applicable (see caveats).

#### Worked example R2 — merged RDEC, loss-making (AP 1 Jan 2025 – 31 Dec 2025)

Qualifying expenditure is £200,000, so L15 = £40,000. The trade is loss-making even after RDEC, so box 475 = 0. PAYE/NIC liabilities are £30,000.

- **Step 1**: L30 = 0; L40 = 0; L45 = 0.
- **Step 2**:
  - L50 = 40,000.
  - Applicable rate = small profits rate 19% (not a main-rate company), so L55 = 7,600 and L60 = 32,400.
  - L62 = L15 − L40 = 40,000; L65 = 40,000 − 32,400 = **7,600**, carried forward (→ L130, L140, L150).
- **Step 3**:
  - L70 = 32,400.
  - L72 = 30,000; L75 = 20,000 + 3 × 30,000 = 110,000.
  - L80 = 0.
- **Steps 4–6**: L85 = L95 = L105 = 32,400; nothing is offset, so L120 = 0.
- **Step 7**: L125 = **£32,400** → CT600 box **880**.
- **L210 = 0** (no set-off).

Under the old RDEC (AP beginning before 1 Apr 2024) step 2 would use the main rate: L55 = 25% × 40,000 = 10,000 and payable = 30,000. Old step 3 would cap at R&D workers' PAYE/NIC only.

#### Worked example R3 — ERIS (AP 1 Apr 2024 – 31 Mar 2025)

This is CIRD122000 Company A, with a PAYE cap added. The company is an R&D-intensive SME with qualifying expenditure of £100,000 and a trade loss before the additional deduction of £50,000.

- Additional deduction = 86,000, so the trade loss = £136,000.
- Surrenderable loss = min(186,000, 136,000) = 136,000.
- Credit = 14.5% × 136,000 = **£19,720**.
- PAYE/NIC = £10,000, so the cap = 20,000 + 30,000 = 50,000 and the credit is not capped.

| Form | Boxes |
|---|---|
| CT600 | 650 ✓, 653 ✓, 657 ✓, 659 = 100,000, 660 = 186,000, 670 = 186,000; trading loss per computations |
| CT600L | L166 = 100,000; L168 = 10,000 (+ L168A PAYE reference); L170 = 19,720; L175 = 0; L180 = **19,720** → box **875**; L210 = 0 |

If the company also had £136,000 of other income, the unrelieved loss would be nil (s1056, sideways relief available), so there would be no credit.

#### Worked example R4 — SME scheme, AP 1 Apr 2023 – 31 Mar 2024 (not R&D-intensive)

Qualifying expenditure is £100,000, so the additional deduction = £86,000. The loss before the additional deduction is £20,000, so the loss = £106,000.

- Surrenderable loss = min(186,000, 106,000) = 106,000.
- Credit = 10% = **£10,600**. If intensity were ≥ 40%, the credit would be 14.5% = £15,370 and box 653 would be ticked.
- Boxes: L166 = 100,000; L170 = 10,600; L180 = 10,600 → 875; 659 = 100,000; 660 = 186,000.

---

### s455 (loans to participators)

See the CT600A section for the full rules, rates and worked example. In summary:

- Rates: 25% (< 6 Apr 2016), 32.5% (to 5 Apr 2022), 33.75% (6 Apr 2022 – 5 Apr 2026), **35.75% (from 6 Apr 2026)**.
- s458 relief: repayment, release or write-off within 9 months of the period end gives immediate relief. Later repayments give relief from the due date of the AP of repayment.
- Arrangements (s464A): no relief for return payments on or after 30 Oct 2024.
- Flows: A80 → box 480; box 485 is ticked if A70 is completed.

### Caveats (reliefs)

- **Which size tick for merged-scheme RDEC claims** (APs from 1 Apr 2024) is not stated explicitly:
  - The schema only says 657 needs 650 or 655, and 659/660 need 653.
  - Box 650's 2026 label is "if an R&D claim is made by an SME", so an SME claiming merged RDEC presumably ticks 650, and a large company ticks 655. **Unverified.**
- **Loss boxes after surrender for a tax credit**: whether box 780 shows the loss before or after the ERIS/SME surrender is not stated. The guide says surrendered losses must not be included in the loss carried forward (computations). **Unverified.**
- **Merged-scheme step 2 rate test**: whether the company's profits are "chargeable at the main rate before RDEC" is a statutory test (s1042K). HMRC's schema only enforces L55 ≥ L15 × the lowest applicable rate.
- **Old-RDEC rate history** (11%/12%/13%): taken from HMRC policy papers (https://www.gov.uk/government/publications/corporation-tax-increasing-the-rate-of-research-and-development-expenditure-credit, https://www.gov.uk/government/publications/change-to-the-rate-of-research-and-development-expenditure-credit-for-corporation-tax) and CIRD89710. The 11% start date (1 Apr 2015) was not re-checked against the statute.
