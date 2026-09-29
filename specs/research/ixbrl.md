# iXBRL for CT600 — research summary (2026-09-28)

Raw downloads: `downloads/` (MANIFEST.md). Validated skeletons: `examples/` (micro FRC 2025/2026, small
FRS 102 1A FRC 2026, computation ct-comp 2024). Validator wrapper: `scripts/validate.py`.

## Accepted taxonomies (gov.uk, updated 2026-04-17)
| Taxonomy | Periods ending | schemaRef |
|---|---|---|
| FRC 2023 | ≤ 31 Mar 2026 | https://xbrl.frc.org.uk/FRS-102/2023-01-01/FRS-102-2023-01-01.xsd |
| FRC 2024 | ≤ 31 Mar 2027 | https://xbrl.frc.org.uk/FRS-102/2024-01-01/FRS-102-2024-01-01.xsd |
| FRC 2025 | open | https://xbrl.frc.org.uk/FRS-102/2025-01-01/FRS-102-2025-01-01.xsd |
| FRC 2026 | open | https://xbrl.frc.org.uk/FRS-102/2026-01-01/FRS-102-2026-01-01.xsd |
| CT comp 2023 | ≤ 31 Mar 2025 | http://www.hmrc.gov.uk/schemas/ct/comp/2023-01-01/ct-comp-2023.xsd |
| CT comp 2024 | ≤ 31 Mar 2026 | http://www.hmrc.gov.uk/schemas/ct/comp/2024-01-01/ct-comp-2024.xsd |
| CT comp 2025 | open | NOT PUBLISHED (schema URL 404; ask sdsteam@hmrc.gov.uk) — BLOCKER for later periods |

FRS 105 and FRS 102 1A both use the FRS-102 entry point; standard chosen via
`bus:AccountingStandardsDimension` = `bus:Micro-entities` / `bus:SmallEntities`.
Namespaces (FRC 2026; swap date for 2025): core `http://xbrl.frc.org.uk/fr/2026-01-01/core`, bus
`http://xbrl.frc.org.uk/cd/2026-01-01/business`, direp `http://xbrl.frc.org.uk/reports/2026-01-01/direp`,
ct-comp `http://www.hmrc.gov.uk/schemas/ct/comp/2024-01-01`.
HMRC errors: 3317 taxonomy not accepted, 3318/3320 period end outside taxonomy window (accounts/comps),
3319 script, 1607 comps TaxReference/EndOfPeriodCoveredByReturn ≠ CT600, 1614 >25MB.

## Accounts — mandatory (JFCVC v4.4a, error 3312; FRC tagging guide 4.21.1)
Dates are INSTANT contexts at the balance sheet date.
| Item | Element | Context |
|---|---|---|
| Name | bus:EntityCurrentLegalOrRegisteredName | duration |
| CRN | bus:UKCompaniesHouseRegisteredNumber (= context identifier, 3316) | duration |
| Start / end | bus:StartDateForPeriodCoveredByReport / bus:EndDateForPeriodCoveredByReport | instant at end |
| Balance sheet date | bus:BalanceSheetDate | instant |
| Approval date | core:DateAuthorisationFinancialStatementsForIssue | instant |
| Director signing | core:DirectorSigningFinancialStatements (empty) + bus:NameEntityOfficer | bus:EntityOfficersDimension=bus:Director1 |
| Dormant | bus:EntityDormantTruefalse | duration |
| Trading status | bus:EntityTradingStatus (empty) | none if trading; bus:EntityHasNeverTraded / bus:EntityNoLongerTradingButTradedInPast |
| Standards | bus:AccountingStandardsApplied (empty) | bus:AccountingStandardsDimension |
| Accounts status | bus:AccountsStatusAuditedOrUnaudited (empty) | bus:AccountsStatusDimension=bus:AuditExempt-NoAccountantsReport |
| Accounts type | bus:AccountsType (empty) | bus:AccountsTypeDimension=bus:FullAccounts (no default) |
| Legal form | bus:LegalFormEntity (empty) | bus:LegalFormEntityDimension=bus:PrivateLimitedCompanyLtd |
| Principal activity | bus:DescriptionPrincipalActivities | duration |
| Avg employees | core:AverageNumberEmployeesDuringPeriod | duration, unit xbrli:pure |

Statements (Arelle checks wording, case-insensitive):
- s477: direp:StatementThatCompanyEntitledToExemptionFromAuditUnderSection477CompaniesAct2006RelatingToSmallCompanies — "Exempt"/"Exemption" + "section 477 of the Companies Act 2006"
- s476: direp:StatementThatMembersHaveNotRequiredCompanyToObtainAnAudit — "Members have" + "not required the company to obtain an audit"
- directors: direp:StatementThatDirectorsAcknowledgeTheirResponsibilitiesUnderCompaniesAct — "Directors acknowledge" + "responsibilities" + "Companies Act 2006"
- regime: direp:StatementThatAccountsHaveBeenPreparedInAccordanceWithProvisionsSmallCompaniesRegime — "Prepared", "in accordance with", "provisions", "micro" (or "small companies")
- s480 dormant: direp:StatementThatCompanyEntitledToExemptionFromAuditUnderSection480CompaniesAct2006RelatingToDormantCompanies

Micro P&L: core:TurnoverRevenue, core:OtherOperatingIncomeFormat2 (conv.), core:RawMaterialsConsumablesUsed,
core:StaffCostsEmployeeBenefitsExpense, core:DepreciationAmortisationImpairmentExpense (conv.),
core:OtherOperatingExpensesFormat2 (conv.), core:TaxTaxCreditOnProfitOrLossOnOrdinaryActivities,
core:ProfitLoss, core:ProfitLossOnOrdinaryActivitiesBeforeTax.
Micro balance sheet (instant): core:CalledUpShareCapitalNotPaidNotExpressedAsCurrentAsset, core:FixedAssets,
core:CurrentAssets, core:PrepaymentsAccruedIncomeNotExpressedWithinCurrentAssetSubtotal, core:Creditors
[core:MaturitiesOrExpirationPeriodsDimension=core:WithinOneYear | core:AfterOneYear],
core:NetCurrentAssetsLiabilities, core:TotalAssetsLessCurrentLiabilities,
core:ProvisionsForLiabilitiesBalanceSheetSubtotal, core:AccruedLiabilitiesNotExpressedWithinCreditorsSubtotal,
core:NetAssetsLiabilities, core:Equity [core:EquityClassesDimension=core:ShareCapital |
core:RetainedEarningsAccumulatedLosses | none=total].
Small 1A: core:CostSales, core:GrossProfitLoss, core:AdministrativeExpenses, core:OtherOperatingIncomeFormat1,
core:OperatingProfitLoss.

## Document rules
XHTML, only XML entities (&#163; for £). iXBRL 1.1 (http://www.xbrl.org/2013/inlineXBRL). Transformations:
http://www.xbrl.org/inlineXBRL/transformation/2011-07-31 (num-dot-decimal, zerodash, nocontent,
datedaymonthyearen, booleantrue/false). sign="-" only for genuine negatives; decimals required; no precision;
scale="-2" for percentages shown as 19. Context identifier scheme "http://www.companieshouse.gov.uk/" (trailing
slash) = CRN. No script; images as data: URIs; embedded CSS; minimal ix:hidden. Full tagging expected.
HMRC checks 3312 mandatory, 3314 inconsistent duplicates, 3315 Director members need names, 3316 identifier.

## Computations (ct-comp 2024)
Mandatory (instant dates at period end): ct-comp:CompanyName, ct-comp:TaxReference (10 digits),
ct-comp:PeriodOfAccountStartDate, ct-comp:PeriodOfAccountEndDate, ct-comp:StartOfPeriodCoveredByReturn,
ct-comp:EndOfPeriodCoveredByReturn (= CT600 end, 1607), ct-comp:CompanyIsAPartnerInAFirm (duration boolean).
Every fact needs ct-comp:BusinessTypeDimension (no default): ct-comp:Company or ct-comp:Trade. Trade facts also
need ct-comp:TerritoryDimension=ct-comp:UK (explicit) and typed ct-comp:BusinessNameDimension
(<ct-comp:BusinessNameDomain>name</ct-comp:BusinessNameDomain>). ct-comp:LossReformDimension optional.
Loans to participators need typed ct-comp:ParticipatorDimension (ct-comp:ParticipatorDomain).

| Item | Element | Type |
|---|---|---|
| Profit per accounts | ct-comp:ProfitLossPerAccounts | Trade |
| Depreciation add-back | ct-comp:AdjustmentsDepreciation | Trade |
| Disallowables | ct-comp:AdjustmentsEntertaining, …PenaltiesAndFines, …CapitalExpenditure, ct-comp:AdjustmentsOtherExpenditureNotWhollyAndExclusivelyForPurposesOfTradeOrBusiness | Trade |
| Adjusted result | ct-comp:AdjustedProfitForThePeriod / ct-comp:AdjustedLossOfPeriod | Trade |
| Capital allowances | ct-comp:TotalCapitalAllowances, ct-comp:MainPoolAnnualInvestmentAllowance, …WritingDownAllowances, …TotalFullExpensingAllowance, ct-comp:MainPoolWrittenDownValue (instant) | Trade |
| Losses per trade | ct-comp:BalanceOfLossesBroughtForwardCarriedForward (instant), ct-comp:LossesUsedAgainstTradingProfits | Trade |
| Net trading profits | ct-comp:NetTradingProfits | Company |
| Losses b/f used | ct-comp:TradingLossesBroughtForwardSetAgainstTradingProfits | Company |
| NTLR | ct-comp:ProfitsAndGainsFromNon-tradingLoanRelationships | Company |
| Gains | ct-comp:NetChargeableGains | Company |
| Donations | ct-comp:QualifyingDonations | Company |
| Group relief | ct-comp:GroupReliefClaimed | Company |
| Profits chargeable | ct-comp:TotalProfitsChargeableToCorporationTax | Company |
| Tax at rates | ct-comp:FY1AmountOfProfitChargeableAtFirstRate, ct-comp:FY1FirstRateOfTax, ct-comp:FY1TaxAtFirstRate (+ second/third, FY2) | Company |
| Tax | ct-comp:CorporationTaxChargeable, ct-comp:TaxChargeable, ct-comp:TaxPayable | Company |
| R&D | ct-comp:AdjustmentsAdditionalDeductionForQualifyingRDExpenditureSME, ct-comp:AmountOfRDExpenditureCredit | Trade |
| s455 | ct-comp:TaxPayableOnLoansToParticipators; per participator ct-comp:LoanToParticipatorAmountTaxable, ct-comp:LoanToParticipatorTaxPayable | Company (+participator) |
Turnover: no computation element. Gaps: no marginal relief element; no merged-scheme RDEC / ERIS elements.

## Arelle offline validation
`uv pip install arelle-release==2.45.3 tinycss2` (tinycss2 needed by validate/UK; missing → plugin silently
not loaded, exit 0).
Accounts: `arelleCmdLine --internetConnectivity=offline --packages downloads/FRC-2026-Taxonomy-v1.0.0.zip
--plugins validate/UK --disclosureSystem hmrc --calc=xbrl21 -v -f FILE --logFile x.log --logFileMode=w`
Computation: `arelleCmdLine --internetConnectivity=offline --packages downloads/CT2024-v1.0.0.zip
--calc=xbrl21 -v -f FILE`
Exit code always 0 → parse the log (scripts/validate.py fails on any warning/error). --calc=xbrl21 needed to
catch missing mandatory comp items. Arelle stricter than CH (HMRC.5.3 negative equity rule).

## Unverified
ct-comp 2025 source; tagging for marginal relief and merged RDEC/ERIS; micro P&L conventions (other income,
other charges, depreciation); newer transformation registries; live enforcement of negative-value/wording
rules; comp context identifier scheme (style guide: CRN; HMRC sample: example.com).
