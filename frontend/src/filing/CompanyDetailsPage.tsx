import { lazy, Suspense, useState } from "react";
import { useNavigate } from "react-router";

import { api, ApiError, type CompanyRecord, type CompanySearchResult } from "@/api";
import { PrefilledBanner } from "@/components/content";
import { Radios, TextInput } from "@/components/forms";
import { useCompaniesHouseLookup } from "@/filing/companiesHouse";
import { useDraft } from "@/filing/draft";
import {
  type CompanyAnswers,
  COMPANY_TYPES,
  EMPTY_COMPANY,
  type FieldErrors,
  SECTION_TITLES,
  validateCompany,
} from "@/filing/model";
import { useNextPage } from "@/filing/paths";
import { SectionFrame } from "@/filing/SectionFrame";

const SEARCH_ID = "company-search";

// The search (with its autocomplete and bundled Preact) loads only when lookup is switched on.
const CompanySearch = lazy(async () => ({
  default: (await import("@/components/CompanySearch")).CompanySearch,
}));

/** What to tell the user when Companies House cannot give a company's details. */
export function companiesHouseError(error: unknown): string {
  if (error instanceof ApiError && error.status === 404) {
    return "Companies House has no company with that number. Search again, or enter the company’s details yourself";
  }
  const reason = error instanceof Error ? error.message : String(error);
  return `We could not get the company’s details from Companies House: ${reason}. Try again, or enter them yourself`;
}

type CompanyFieldsProps = {
  values: CompanyAnswers;
  setValues: (values: CompanyAnswers) => void;
  errors: FieldErrors;
};

function CompanyFields({ values, setValues, errors }: CompanyFieldsProps) {
  return (
    <>
      <TextInput
        id="name"
        label="Company name"
        hint="As it appears on the Companies House register."
        value={values.name}
        onChange={(name) => setValues({ ...values, name })}
        error={errors.name}
        autoComplete="organization"
      />
      <TextInput
        id="registration_number"
        label="Company registration number"
        hint="8 characters, like 01234567 or SC123456. It's on your certificate of incorporation."
        value={values.registration_number}
        onChange={(registrationNumber) =>
          setValues({ ...values, registration_number: registrationNumber })
        }
        error={errors.registration_number}
        width="10"
        spellCheck={false}
      />
      <TextInput
        id="utr"
        label="Corporation Tax Unique Taxpayer Reference (UTR)"
        hint="10 digits, like 1234567890. HMRC sent it to your registered office after the company was set up."
        value={values.utr}
        onChange={(utr) => setValues({ ...values, utr })}
        error={errors.utr}
        width="10"
        inputMode="numeric"
        spellCheck={false}
      />
      <TextInput
        id="principal_activity"
        label="What does the company do?"
        hint="Its principal activity, as stated in its accounts. For example, software development."
        value={values.principal_activity}
        onChange={(principalActivity) =>
          setValues({ ...values, principal_activity: principalActivity })
        }
        error={errors.principal_activity}
      />
      <Radios
        name="company_type"
        legend="Type of company"
        hint="Box 4 on the CT600."
        options={COMPANY_TYPES}
        value={values.company_type}
        onChange={(companyType) => setValues({ ...values, company_type: companyType })}
        error={errors.company_type}
      />
    </>
  );
}

/** The company's answers once it has been chosen from Companies House. */
function fromRecord(values: CompanyAnswers, record: CompanyRecord): CompanyAnswers {
  return {
    ...values,
    name: record.name,
    registration_number: record.number,
    principal_activity: record.principal_activity ?? values.principal_activity,
  };
}

/**
 * The company's details: found with a Companies House search where lookup is switched on, and
 * typed in otherwise, or when the user cannot find the company.
 */
export function CompanyDetailsPage() {
  const { draft, saveSection } = useDraft();
  const { next } = useNextPage();
  const navigate = useNavigate();
  const lookup = useCompaniesHouseLookup();
  const [values, setValues] = useState({ ...EMPTY_COMPANY, ...draft.company });
  const [errors, setErrors] = useState<FieldErrors>({});
  const [manual, setManual] = useState(draft.company !== undefined);
  const [prefilled, setPrefilled] = useState(false);
  const [fetching, setFetching] = useState(false);
  const searching = lookup === "enabled" && !manual && !prefilled;

  async function choose(company: CompanySearchResult) {
    setFetching(true);
    setErrors({});
    try {
      const record = await api.company(company.number);
      saveSection("companies_house", record);
      setValues((current) => fromRecord(current, record));
      setPrefilled(true);
    } catch (error) {
      setErrors({ [SEARCH_ID]: companiesHouseError(error) });
    } finally {
      setFetching(false);
    }
  }

  function save() {
    if (searching) {
      setErrors({
        [SEARCH_ID]:
          errors[SEARCH_ID] ??
          "Search for the company by its name or number, or select ‘I can’t find the company’",
      });
      return;
    }
    const result = validateCompany(values);
    if (!result.ok) {
      setErrors(result.errors);
      return;
    }
    saveSection("company", values);
    navigate(next);
  }

  return (
    <SectionFrame
      title={SECTION_TITLES.company}
      errors={errors}
      fieldOrder={[
        SEARCH_ID,
        "name",
        "registration_number",
        "utr",
        "principal_activity",
        "company_type",
      ]}
      onSubmit={save}
      banner={prefilled ? <PrefilledBanner /> : null}
    >
      {lookup === "checking" && !manual ? (
        <p className="govuk-body">Checking whether we can search Companies House…</p>
      ) : null}
      {searching ? (
        <>
          <Suspense fallback={<p className="govuk-body">Loading the company search…</p>}>
            <CompanySearch
              id={SEARCH_ID}
              label="Find the company"
              hint="Search Companies House by the company’s name or its 8-character company number, like 01234567."
              error={errors[SEARCH_ID]}
              search={api.searchCompanies}
              onChoose={(company) => void choose(company)}
              onSearchError={(error) => setErrors({ [SEARCH_ID]: companiesHouseError(error) })}
            />
          </Suspense>
          {fetching ? (
            <output className="govuk-body govuk-!-display-block">
              Getting the company’s details from Companies House…
            </output>
          ) : null}
          <p className="govuk-body">
            <button
              type="button"
              className="govuk-link app-link-button"
              onClick={() => {
                setManual(true);
                setErrors({});
              }}
            >
              I can’t find the company
            </button>
          </p>
        </>
      ) : null}
      {!searching && (manual || lookup !== "checking") ? (
        <CompanyFields values={values} setValues={setValues} errors={errors} />
      ) : null}
    </SectionFrame>
  );
}
