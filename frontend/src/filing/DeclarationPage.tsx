import { type FormEvent, type ReactNode, useEffect, useState } from "react";
import { Navigate } from "react-router";

import {
  api,
  type CT600Return,
  type Declaration,
  type HmrcEnvironment,
  type SchemaPage,
  type SignatoryCapacity,
} from "@/api";
import { BackLink, TwoThirds, usePageTitle, WarningText } from "@/components/content";
import {
  Button,
  Checkbox,
  type ErrorItem,
  ErrorSummary,
  Radios,
  TextInput,
} from "@/components/forms";
import { useDraft } from "@/filing/draft";
import type { FieldErrors } from "@/filing/model";
import { CHECK_ANSWERS, CONFIRMATION, TASK_LIST } from "@/filing/paths";
import { Pending } from "@/filing/Pending";
import { type Failure, failure, rejected } from "@/filing/submission";
import { useReturn } from "@/filing/useReturn";

const CAPACITIES: { value: SignatoryCapacity; label: string }[] = [
  { value: "director", label: "Director" },
  { value: "company_secretary", label: "Company secretary" },
  { value: "authorised_agent", label: "Agent authorised by the company" },
];

type Method = HmrcEnvironment | "demo";

const FIELD_ORDER = [
  "name",
  "capacity",
  "method",
  "gateway_user_id",
  "gateway_password",
  "confirmed",
] as const;

type Answers = {
  name: string;
  capacity: SignatoryCapacity | "";
  method: Method | "";
  userId: string;
  confirmed: boolean;
};

function validate(answers: Answers, password: string): FieldErrors {
  const errors: FieldErrors = {};
  if (!answers.name.trim()) errors.name = "Enter your full name";
  if (!answers.capacity) errors.capacity = "Select the capacity in which you are signing";
  if (!answers.method) errors.method = "Select how you want to send your return";
  if (answers.method === "live" || answers.method === "test-in-live") {
    if (!answers.userId.trim()) errors.gateway_user_id = "Enter your Government Gateway user ID";
    if (!password) errors.gateway_password = "Enter your Government Gateway password";
  }
  if (!answers.confirmed) {
    errors.confirmed = "Confirm that the information you have given is correct and complete";
  }
  return errors;
}

type CredentialsProps = {
  userId: string;
  password: string;
  onUserId: (value: string) => void;
  onPassword: (value: string) => void;
  errors: FieldErrors;
};

/** The company's Government Gateway sign in: sent to HMRC with the return, never kept. */
function Credentials({ userId, password, onUserId, onPassword, errors }: CredentialsProps) {
  return (
    <>
      <p className="govuk-body">
        Enter the Government Gateway user ID and password the company uses for HMRC online services.
        We send them to HMRC with your return and do not keep them.
      </p>
      <TextInput
        id="gateway_user_id"
        label="Government Gateway user ID"
        value={userId}
        onChange={onUserId}
        error={errors.gateway_user_id}
        width="20"
        autoComplete="off"
        spellCheck={false}
      />
      <TextInput
        id="gateway_password"
        label="Password"
        type="password"
        value={password}
        onChange={onPassword}
        error={errors.gateway_password}
        width="20"
        autoComplete="off"
        spellCheck={false}
      />
    </>
  );
}

function PendingBanner({ correlationId }: { correlationId: string | null }) {
  return (
    <section className="govuk-notification-banner" aria-labelledby="pending-title">
      <div className="govuk-notification-banner__header">
        <h2 className="govuk-notification-banner__title" id="pending-title">
          Important
        </h2>
      </div>
      <div className="govuk-notification-banner__content">
        <p className="govuk-notification-banner__heading">HMRC is still processing your return</p>
        <p className="govuk-body">
          HMRC has not replied yet. Your return may still be accepted, so do not send it again
          straight away. Check your HMRC online services account later to see whether it arrived.
        </p>
        {correlationId ? (
          <p className="govuk-body">
            HMRC's reference for this submission (correlation ID) is{" "}
            <strong className="app-numeric">{correlationId}</strong>.
          </p>
        ) : null}
      </div>
    </section>
  );
}

const METHODS: Record<Method, { label: string; hint: string }> = {
  "test-in-live": {
    label: "Send a test submission to HMRC (Test in Live)",
    hint: "HMRC checks your return as it would a real one, but does not file it.",
  },
  live: { label: "Submit to HMRC", hint: "HMRC files your return for the company." },
  demo: { label: "Do not send it: get a demonstration receipt", hint: "Nothing is sent to HMRC." },
};

/** The HMRC services this deployment allows, with the Gateway sign in, then the receipt only. */
function methodOptions(environments: HmrcEnvironment[], credentials: ReactNode) {
  return [
    ...(["test-in-live", "live"] as const)
      .filter((environment) => environments.includes(environment))
      .map((environment) => ({
        value: environment,
        ...METHODS[environment],
        conditional: credentials,
      })),
    { value: "demo" as const, ...METHODS.demo },
  ];
}

/** Why there is no choice of how to send: the service is checking, or it cannot submit. */
function CannotSend({ checking }: { checking: boolean }) {
  if (checking) {
    return <p className="govuk-body">Checking whether this service can send returns to HMRC…</p>;
  }
  return (
    <div className="govuk-inset-text">
      This service cannot send returns to HMRC: whoever runs it has not switched submission on. When
      you submit, you get a demonstration receipt and nothing is sent to HMRC. To file for real,
      download your return from check your answers and use HMRC-recognised software or an
      accountant.
    </div>
  );
}

const WARNINGS: Record<Method, ReactNode> = {
  demo:
    "Your return will not be sent to HMRC. Giving false information in a real return can lead " +
    "to a penalty or prosecution.",
  "test-in-live": "HMRC will check your return but will not file it.",
  live: "Giving false information in a return can lead to a penalty or prosecution.",
};

type DeclareProps = {
  ct600: CT600Return;
  pages: SchemaPage[];
  /** The HMRC services this deployment can send to: none if it cannot; ``null`` while checking. */
  environments: HmrcEnvironment[] | null;
};

function Declare({ ct600, pages, environments }: DeclareProps) {
  const { recordSubmission } = useDraft();
  const [answers, setAnswers] = useState<Answers>({
    name: "",
    capacity: "",
    method: "",
    userId: "",
    confirmed: false,
  });
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [outcome, setOutcome] = useState<Failure | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const set = (change: Partial<Answers>) => setAnswers({ ...answers, ...change });
  const canSend = environments !== null && environments.length > 0;
  // Without HMRC services on offer, the only way to finish is a demonstration receipt.
  const method: Method | "" = canSend ? answers.method : "demo";

  const general = outcome?.kind === "errors" ? outcome.general : [];
  const summary: ErrorItem[] = [
    ...FIELD_ORDER.filter((field) => errors[field]).map((field) => ({
      href: `#${field}`,
      text: errors[field] ?? "",
    })),
    ...general,
  ];
  usePageTitle("Declaration", summary.length > 0);

  /** Send the return; on success the draft is replaced by the receipt. */
  async function send(declaration: Declaration, via: Method): Promise<Failure | null> {
    if (via === "demo") {
      const receipt = await api.submitReturn(ct600, declaration);
      recordSubmission({ kind: "demo", ...receipt });
      return null;
    }
    const credentials = { gateway_user_id: answers.userId.trim(), gateway_password: password };
    setPassword("");
    const result = await api.submitToHmrc({
      ct600,
      declaration,
      environment: via,
      ...credentials,
    });
    if (result.status === "rejected") {
      const description =
        "HMRC did not accept your return. Correct these problems and submit it again.";
      return rejected(result.problems, pages, description);
    }
    const { status: _accepted, ...receipt } = result;
    recordSubmission({
      kind: "hmrc",
      ...receipt,
      company: ct600.company,
      period: ct600.period,
      signatory: declaration.name,
    });
    return null;
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const found = validate({ ...answers, method }, password);
    setErrors(found);
    setOutcome(null);
    setAttempt(attempt + 1);
    const { capacity } = answers;
    if (Object.keys(found).length > 0 || !capacity || !method) return;
    setSubmitting(true);
    let sorted: Failure | null;
    try {
      sorted = await send({ name: answers.name.trim(), capacity, confirmed: true }, method);
    } catch (error) {
      sorted = failure(error, pages);
    }
    if (sorted === null) return;
    setPassword("");
    setOutcome(sorted);
    if (sorted.kind === "errors") setErrors(sorted.fields);
    setSubmitting(false);
  }

  const credentials = (
    <Credentials
      userId={answers.userId}
      password={password}
      onUserId={(userId) => set({ userId })}
      onPassword={setPassword}
      errors={errors}
    />
  );

  return (
    <>
      <BackLink to={CHECK_ANSWERS} />
      <TwoThirds>
        <ErrorSummary
          key={attempt}
          errors={summary}
          description={outcome?.kind === "errors" ? outcome.description : undefined}
        />
        {outcome?.kind === "pending" ? (
          <PendingBanner correlationId={outcome.correlationId} />
        ) : null}
        <span className="govuk-caption-l">{ct600.company.name}</span>
        <h1 className="govuk-heading-l">Declaration</h1>
        <p className="govuk-body">
          The return must be signed by a director, the company secretary or an agent the company has
          authorised.
        </p>
        <form onSubmit={submit} noValidate>
          <TextInput
            id="name"
            label="Full name"
            value={answers.name}
            onChange={(name) => set({ name })}
            error={errors.name}
            autoComplete="name"
          />
          <Radios
            name="capacity"
            legend="In what capacity are you signing?"
            options={CAPACITIES}
            value={answers.capacity}
            onChange={(capacity) => set({ capacity })}
            error={errors.capacity}
          />
          {canSend ? (
            <Radios
              name="method"
              legend="How do you want to send your return?"
              options={methodOptions(environments, credentials)}
              value={answers.method}
              onChange={(chosen) => set({ method: chosen })}
              error={errors.method}
            />
          ) : (
            <CannotSend checking={environments === null} />
          )}
          <Checkbox
            id="confirmed"
            label="The information I have given in this Company Tax Return is correct and complete to the best of my knowledge and belief."
            checked={answers.confirmed}
            onChange={(confirmed) => set({ confirmed })}
            error={errors.confirmed}
          />
          {method ? <WarningText>{WARNINGS[method]}</WarningText> : null}
          <Button
            disabled={submitting || environments === null}
            aria-disabled={submitting || environments === null}
          >
            {method === "test-in-live" ? "Send test submission" : "Submit return"}
          </Button>
        </form>
      </TwoThirds>
    </>
  );
}

/** The HMRC services this deployment can send to; none if it cannot say. ``null`` until known. */
function useSubmissionEnvironments(): HmrcEnvironment[] | null {
  const [environments, setEnvironments] = useState<HmrcEnvironment[] | null>(null);
  useEffect(() => {
    let current = true;
    api.submissionStatus().then(
      (status) => current && setEnvironments(status.enabled ? status.environments : []),
      () => current && setEnvironments([]),
    );
    return () => {
      current = false;
    };
  }, []);
  return environments;
}

export function DeclarationPage() {
  const { receipt } = useDraft();
  const built = useReturn();
  const environments = useSubmissionEnvironments();
  // Submitting clears the draft, so a submitted return has no draft left to show.
  if (built.status === "incomplete") {
    return <Navigate to={receipt ? CONFIRMATION : TASK_LIST} replace />;
  }
  if (built.status === "ready") {
    return <Declare ct600={built.ct600} pages={built.pages} environments={environments} />;
  }
  return <Pending title="Declaration" failure={built.status === "failed" ? built.message : null} />;
}
