import { type FormEvent, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router";

import { api, ApiError, type SignupReceipt } from "@/api";
import { Panel, TwoThirds, usePageTitle } from "@/components/content";
import { Button, Checkbox, type ErrorItem, ErrorSummary, TextInput } from "@/components/forms";

type Field = "full_name" | "email" | "company_name" | "accept_terms";
type Errors = Partial<Record<Field, string>>;

const FIELD_ORDER: Field[] = ["full_name", "email", "company_name", "accept_terms"];
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type Details = { fullName: string; email: string; companyName: string; acceptTerms: boolean };

function validate(details: Details): Errors {
  const errors: Errors = {};
  if (!details.fullName.trim()) errors.full_name = "Enter your full name";
  if (!details.email.trim()) errors.email = "Enter your email address";
  else if (!EMAIL.test(details.email.trim())) {
    errors.email = "Enter an email address in the correct format, like name@example.com";
  }
  if (!details.companyName.trim()) errors.company_name = "Enter your company name";
  if (!details.acceptTerms) {
    errors.accept_terms = "You must agree to the terms and conditions and privacy notice";
  }
  return errors;
}

function serverErrors(error: unknown): { fields: Errors; general: ErrorItem[] } {
  if (error instanceof ApiError && error.problems.length > 0) {
    const fields: Errors = {};
    for (const problem of error.problems) {
      const field = FIELD_ORDER.find((name) => name === problem.path[0]);
      if (field) fields[field] ??= problem.message;
    }
    return { fields, general: [] };
  }
  const message = error instanceof Error ? error.message : String(error);
  return { fields: {}, general: [{ href: "#full_name", text: message }] };
}

export function SignUpPage() {
  const navigate = useNavigate();
  const [details, setDetails] = useState<Details>({
    fullName: "",
    email: "",
    companyName: "",
    acceptTerms: false,
  });
  const [errors, setErrors] = useState<Errors>({});
  const [general, setGeneral] = useState<ErrorItem[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const summary = [
    ...FIELD_ORDER.filter((field) => errors[field]).map((field) => ({
      href: `#${field}`,
      text: errors[field] ?? "",
    })),
    ...general,
  ];
  usePageTitle("Create an account", summary.length > 0);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAttempt(attempt + 1);
    const found = validate(details);
    setErrors(found);
    setGeneral([]);
    if (Object.keys(found).length > 0) return;
    setSubmitting(true);
    try {
      const receipt = await api.signUp({
        full_name: details.fullName.trim(),
        email: details.email.trim(),
        company_name: details.companyName.trim(),
        accept_terms: true,
      });
      navigate("/sign-up/confirmation", { state: receipt });
    } catch (error) {
      const problems = serverErrors(error);
      setErrors(problems.fields);
      setGeneral(problems.general);
      setSubmitting(false);
    }
  }

  return (
    <TwoThirds>
      <ErrorSummary key={attempt} errors={summary} />
      <h1 className="govuk-heading-xl">Create an account</h1>
      <p className="govuk-body-l">Register to hear about new features and filing deadlines.</p>
      <p className="govuk-body">
        You do not need an account to prepare a return.{" "}
        <Link className="govuk-link" to="/file">
          Start your Company Tax Return
        </Link>{" "}
        straight away.
      </p>
      <form onSubmit={submit} noValidate>
        <TextInput
          id="full_name"
          label="Full name"
          value={details.fullName}
          onChange={(fullName) => setDetails({ ...details, fullName })}
          error={errors.full_name}
          autoComplete="name"
        />
        <TextInput
          id="email"
          label="Email address"
          hint="We'll only use this to contact you about Open CT600."
          type="email"
          value={details.email}
          onChange={(email) => setDetails({ ...details, email })}
          error={errors.email}
          autoComplete="email"
          spellCheck={false}
        />
        <TextInput
          id="company_name"
          label="Company name"
          value={details.companyName}
          onChange={(companyName) => setDetails({ ...details, companyName })}
          error={errors.company_name}
          autoComplete="organization"
        />
        <Checkbox
          id="accept_terms"
          label={
            <>
              I agree to the{" "}
              <Link className="govuk-link" to="/terms">
                terms and conditions
              </Link>{" "}
              and{" "}
              <Link className="govuk-link" to="/privacy">
                privacy notice
              </Link>
            </>
          }
          checked={details.acceptTerms}
          onChange={(acceptTerms) => setDetails({ ...details, acceptTerms })}
          error={errors.accept_terms}
        />
        <Button disabled={submitting} aria-disabled={submitting}>
          Create account
        </Button>
      </form>
    </TwoThirds>
  );
}

export function SignUpConfirmationPage() {
  usePageTitle("Account created");
  const receipt = useLocation().state as SignupReceipt | null;

  if (!receipt) return <Navigate to="/sign-up" replace />;
  return (
    <TwoThirds>
      <Panel title="Account created">
        Your reference is
        <br />
        <strong>{receipt.reference}</strong>
      </Panel>
      <p className="govuk-body">
        We've registered <strong>{receipt.email}</strong>. We'll use it to tell you about new
        features and filing deadlines.
      </p>
      <h2 className="govuk-heading-m">What you can do now</h2>
      <ul className="govuk-list govuk-list--bullet">
        <li>
          <Link className="govuk-link" to="/file">
            Start your Company Tax Return
          </Link>
        </li>
        <li>
          <Link className="govuk-link" to="/calculator">
            Estimate your Corporation Tax
          </Link>
        </li>
      </ul>
    </TwoThirds>
  );
}
