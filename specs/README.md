# Specifications

Official material this project is built against. HMRC documents and schemas are Crown copyright,
published under the Open Government Licence v3.0.

| Path | What it is | Source |
| --- | --- | --- |
| `hmrc/ct600-v1.994/` | CT600 XML schema (v1.994, live), HMRC schematron business rules, GovTalk envelope and xmldsig schemas | HMRC Local Test Service artefacts `ct_ct600_v1-994.zip`, identical to the RIM artefacts on gov.uk |
| `hmrc/box-map-v1.995.tsv` | CT600 box id → XML path, cardinality and description for every element and attribute, parsed from HMRC's v1.995 specification document (full paths and descriptions; type and choice rows left out) | [CT600 RIM artefacts](https://www.gov.uk/government/publications/corporation-tax-technical-specifications-ct600-rim-artefacts) |
| `hmrc/rules-v1.995.tsv` | Business rules with HMRC error codes and messages | as above |
| `hmrc/samples/` | HMRC's valid CT600 XML samples | [valid XML samples](https://www.gov.uk/government/publications/corporation-tax-technical-specifications-ct600-valid-xml-samples) |
| `hmrc/irmark/` | HMRC's IRmark worked example | [IRmark support](https://www.gov.uk/government/collections/hmrcirmark-support-for-software-developers) |
| `hmrc/SuccessResponse-v1-1.xsd` | Transaction Engine success response schema | as above |
| `hmrc/guidance/` | HMRC's gov.uk guides to the CT600 and supplementary pages A–P, saved as markdown from the gov.uk content API (a `Source:` and `Updated:` line under each title). `frontend/scripts/extract-hmrc-guidance.ts` (`pnpm guidance:extract`) takes each box's guidance from them for the help panels. Other gov.uk guides quoted in help are saved here too; one not published by HMRC has a `Publisher:` line | [Company Tax Return guide](https://www.gov.uk/guidance/the-company-tax-return-guide) and each page's guide, linked from it |
| `ixbrl/taxonomies.tsv` | FRC and HMRC computational taxonomy packages, fetched by URL and checked by SHA-256 (not redistributed) | FRC, HMRC |
| `ixbrl/examples/` | Minimal iXBRL accounts and computations that pass Arelle offline validation | written for this project |
| `companies-house/SIC07_CH_condensed_list_en.csv` | Companies House's condensed list of SIC 2007 codes and descriptions (nature of business) | [SIC list](https://www.gov.uk/government/publications/standard-industrial-classification-of-economic-activities-sic), file `https://assets.publishing.service.gov.uk/media/5a7f8639e5274a2e87db65e1/SIC07_CH_condensed_list_en.csv`, fetched 2026-09-29 |
| `companies-house/api/` | Swagger 2.0 specs of the public data API (company profile, officers, filing history, search) and the Document API, used to check the test fixtures' shapes | [Companies House developer specs](https://developer-specs.company-information.service.gov.uk), fetched 2026-09-29 |
| `research/` | Research notes: submission protocol, iXBRL tagging, CT600 main return and supplementary pages A–P, group relief, R&D and s455 rules | compiled 2026-09-28 from gov.uk and HMRC manuals |
