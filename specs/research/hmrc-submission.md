# HMRC CT600 online submission — technical research summary

Researched 2026-09-28. Raw sources in `downloads/` (see `downloads/MANIFEST.md`), tools in `tools/`
(`irmark.py` verified against HMRC's worked example and TPVS), probes in `probes/`, text extracts in
`text/` (`CT-2014-v1-995.outline.txt` full element tree; `CT-v1-995-box-map.tsv` box id → XPath).

## Key takeaways
1. Live schema: **CT600 V3 artefacts v1.994** (10 Oct 2025). v1.995 (25 Sep 2026) published, awaiting
   implementation. Both: namespace `http://www.govtalk.gov.uk/taxation/CT/5`, root `IRenvelope`.
2. Transport: GovTalk 2.0 envelope POSTed to the Transaction Engine.
   Live `https://transaction-engine.tax.service.gov.uk/submission`;
   ETS `https://test-transaction-engine.tax.service.gov.uk/submission` (poll `…/poll`).
   submit → acknowledgement (`CorrelationID`, `ResponseEndPoint@PollInterval`) → poll → response|error → delete.
3. Auth: only `Method=clear` (Gateway user ID + password; MD5 withdrawn → 1047).
   Class `HMRC-CT-CT600` (live) / `HMRC-CT-CT600-TIL` (Test in Live).
4. IRmark [verified]: SHA-1 of inclusive C14N 1.0 of the GovTalk `<Body>` (inheriting in-scope ns decls),
   with the `IRmark` element removed (surrounding whitespace kept); Base64 (28 chars) in
   `IRheader/IRmark[@Type="generic"]`; Base32 (32 chars) for display. HMRC hashes WITH comments —
   emit no comments / no pretty-printing inside `<Body>`.
5. Attachments: `AttachedFiles/XBRLsubmission/{Computation,Accounts}/Instance/EncodedInlineXBRLDocument`
   (base64, recommended). Computation BEFORE Accounts. ≤25 MB total (1614).
6. Without a vendor ID: **TPVS** `https://www.tpvs.hmrc.gov.uk/HMRC/CT600` (synchronous, no credentials)
   validates Body schema + schematron + IRmark + iXBRL + cross-doc checks and returns a signed receipt
   [verified]. Retry on transient Akamai HTML 403. Never send real customer data to TPVS/ETS/LTS.
   ETS needs SDST test credentials (placeholder creds → 1046). TIL/live need real Gateway creds.
   Vendor ID (4 digits, `ChannelRouting/Channel/URI`) from SDSTeam@hmrc.gov.uk.

## CT600 XML structure (v1.994/5)
IRenvelope > IRheader: `Keys>Key[@Type=UTR]`, `PeriodEnd`, `DefaultCurrency`=GBP, `Manifest>Contains>
Reference>{Namespace, SchemaVersion (pattern \d{4}-v\d+.\d+; TPVS accepted 2025-v1.994), TopElementName=
CompanyTaxReturn}`, `IRmark[@Type=generic]`, `Sender`=Company. Header Key UTR must equal GovTalk key (5005)
and `CompanyInformation/Reference` (N007).

`CompanyTaxReturn[@ReturnType=new|amended]` children in sequence:
CompanyInformation (CompanyName [1] 2-56 chars, RegistrationNumber? [2] `[A-Z0-9]{2,8}`, Reference [3] UTR,
CompanyType [4] 0-11, NorthernIreland?, PeriodCovered{From [30], To [35]}) → ReturnInfoSummary (Accounts,
Computations, SupplementaryPages? flags CT600A..CT600P=yes) → Turnover? {Total [145]} →
CompanyTaxCalculation → EnergyProfitsLevy? → CalculationOfTaxOutstandingOrOverpaid ([475],[510],
TaxPayable [525]) → TaxReconciliation? → IndicatorsAndInformation? → EnhancedExpenditure? →
LandRemediationEnhancedExpenditure? → AllowancesAndCharges? → NotIncluded? → QualifyingExpenditure? →
LossesDeficitsAndExcess? → NorthernIrelandInformation? → OverpaymentsAndRepayments? →
Declaration (AcceptDeclaration=yes, Name [975], Status [985]) → supplementary pages → WelshReturn? →
JointAccounts? → AttachedFiles?.

Supplementary page elements (after Declaration, flag must be yes): A LoansByCloseCompanies, B
ControlledForeignCompanies, C GroupAndConsortium, D Insurance, E Charity, F TonnageTax, G NorthernIreland,
H CrossBorderRoyalties, I RingFenceTrade, J TaxAvoidanceSchemes, K RestitutionTax, L
ResearchAndDevelopment, M Freeports, N ResidentialPropertyDeveloperTax, P CreativeIndustries. No CT600O.

Money: CTwholePoundStructure max 99999999999.00, written `100000.00`; CTpoundPenceStructure.
NoAccountsReason / NoComputationsReason enumerations: see XSD.

## GovTalk / Transaction Engine
Envelope ns `http://www.govtalk.gov.uk/CM/envelope` (XSD 2.0-HMRC in RIM zips). MessageDetails: Class,
Qualifier (request|acknowledgement|response|poll|error), Function (submit|delete|list), TransactionID,
CorrelationID (`[0-9A-F]{0,32}`, empty on submit → else 1020), ResponseEndPoint@PollInterval,
Transformation=XML, GatewayTest (1 ETS, 0/absent live/TIL). SenderDetails/IDAuthentication{SenderID,
Authentication{Method=clear, Role=principal, Value}}. GovTalkDetails{Keys, TargetDetails{Organisation=HMRC},
ChannelRouting{Channel{URI=vendor id, Product, Version}, Timestamp (test services only)}}.

Poll: Qualifier=poll, Function=submit, same Class + CorrelationID, empty Keys, no SenderDetails, no Body.
Success: Qualifier=response, Body `SuccessResponse` (ns `http://www.inlandrevenue.gov.uk/SuccessResponse`)
with IRmarkReceipt (dsig DigestValue = IRmark, Message quoting Base32) + AcceptedTime.
Error: Qualifier=error, Body `ErrorResponse` (ns `http://www.govtalk.gov.uk/CM/errorresponse`) with
Error{RaisedBy, Number, Type, Text, Location}. Delete: Qualifier=request, Function=delete + CorrelationID.

Error codes: 1000 system, 1001 schema/body, 1002 auth, 1020 CorrelationID on submit, 1035 bad
CorrelationID, 1042 empty body, 1046 creds invalid for service, 1047 MD5, 2000 CorrelationID not found,
2001 too large, 2005 no ack, 3000 fatal, 3001 business. CT: 1604/1605 attachment type, 1606 accounts CRN ≠
CT600, 1607 comps UTR/end date ≠ CT600, 1614 >25MB, 2021 IRmark incorrect, 2022 missing, 3303 iXBRL
malformed, 3312-3322 iXBRL mandatory facts, 4000-4999 schema, 5001 namespace, 5004/5005 keys, 7782 accounts
period overlap, 9100-9999 schematron, 9964 iXBRL+PDF accounts.

## Attachments
AttachedFiles: choice (a) Attachment+ (PDF) | (b) XBRLsubmission, Attachment*. XBRLsubmission: Accounts |
(Computation, Accounts?). Instance @Filename? choice EncodedInlineXBRLDocument+ (@Filename, @entryPoint) |
InlineXBRLDocument+ | RawXBRLDocument. Normal trading company needs both iXBRL accounts and computations
(absent NoAccountsReason / NoComputationsReason). XHTML only, no script, only the 5 XML entities.
Filenames: `[A-Za-z0-9 ,.()&'\-!%_+@?=;]`.

## Annotated skeleton
See `probes/skeleton-irmarked.xml` (schema-valid v1.994/v1.995 + envelope; IRmark accepted by TPVS).

## Unverified
Live poll URL literal; ETS poll/delete for CT; SchemaVersion literal (pattern only); vendor ID
enforcement on TIL; CompanyType meanings (in CT600 guide); TE size limit (2001); LTS CT path.
