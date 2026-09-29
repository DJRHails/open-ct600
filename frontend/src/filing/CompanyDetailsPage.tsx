import { useState } from "react";
import { useNavigate } from "react-router";

import { Radios, TextInput } from "@/components/forms";
import { useDraft } from "@/filing/draft";
import {
  COMPANY_TYPES,
  EMPTY_COMPANY,
  type FieldErrors,
  SECTION_TITLES,
  validateCompany,
} from "@/filing/model";
import { useNextPage } from "@/filing/paths";
import { SectionFrame } from "@/filing/SectionFrame";

export function CompanyDetailsPage() {
  const { draft, saveSection } = useDraft();
  const { next } = useNextPage();
  const navigate = useNavigate();
  const [values, setValues] = useState({ ...EMPTY_COMPANY, ...draft.company });
  const [errors, setErrors] = useState<FieldErrors>({});

  function save() {
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
      fieldOrder={["name", "registration_number", "utr", "principal_activity", "company_type"]}
      onSubmit={save}
    >
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
    </SectionFrame>
  );
}
