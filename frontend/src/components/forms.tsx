import { type ButtonHTMLAttributes, Fragment, type ReactNode, useEffect, useRef } from "react";
import { Link } from "react-router";

/** An error to list in the summary: ``#field-id`` on this page, or ``/path`` to another page. */
export type ErrorItem = { href: string; text: string };

type ErrorSummaryProps = { errors: ErrorItem[]; description?: ReactNode };

/** GOV.UK error summary. Takes focus whenever the list of errors changes. */
export function ErrorSummary({ errors, description }: ErrorSummaryProps) {
  const root = useRef<HTMLDivElement>(null);
  const signature = errors.map((error) => error.href + error.text).join("|");

  useEffect(() => {
    if (signature) root.current?.focus();
  }, [signature]);

  if (errors.length === 0) return null;
  return (
    <div className="govuk-error-summary" ref={root} tabIndex={-1} role="alert">
      <h2 className="govuk-error-summary__title">There is a problem</h2>
      <div className="govuk-error-summary__body">
        {description ? <p>{description}</p> : null}
        <ul className="govuk-list govuk-error-summary__list">
          {errors.map((error, index) => (
            <li key={`${index}:${error.href}:${error.text}`}>
              {error.href.startsWith("/") ? (
                <Link to={error.href}>{error.text}</Link>
              ) : (
                <a
                  href={error.href}
                  onClick={(event) => {
                    const target = document.getElementById(error.href.slice(1));
                    if (!target) return;
                    event.preventDefault();
                    target.scrollIntoView({ block: "center" });
                    target.focus();
                  }}
                >
                  {error.text}
                </a>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function ErrorMessage({ id, children }: { id: string; children: ReactNode }) {
  return (
    <p id={id} className="govuk-error-message">
      <span className="govuk-visually-hidden">Error:</span> {children}
    </p>
  );
}

function Hint({ id, children }: { id: string; children: ReactNode }) {
  return (
    <div id={id} className="govuk-hint">
      {children}
    </div>
  );
}

function describedBy(id: string, hint: ReactNode, error: string | undefined) {
  const ids = [hint ? `${id}-hint` : "", error ? `${id}-error` : ""].filter(Boolean);
  return ids.length > 0 ? ids.join(" ") : undefined;
}

function groupClass(error: string | undefined) {
  return error ? "govuk-form-group govuk-form-group--error" : "govuk-form-group";
}

type TextInputProps = {
  id: string;
  label: ReactNode;
  value: string;
  onChange: (value: string) => void;
  hint?: ReactNode;
  error?: string | undefined;
  width?: "2" | "3" | "4" | "5" | "10" | "20" | "30" | undefined;
  type?: "text" | "email" | "password";
  inputMode?: "numeric" | "decimal" | "text" | "email";
  autoComplete?: string;
  spellCheck?: boolean;
  prefix?: string;
  suffix?: string;
  /** Help about the question, like a details component, shown after the input. */
  help?: ReactNode;
};

export function TextInput(props: TextInputProps) {
  const { id, label, value, onChange, hint, error, width, prefix, suffix } = props;
  const classes = [
    "govuk-input",
    width ? `govuk-input--width-${width}` : "",
    error ? "govuk-input--error" : "",
  ].filter(Boolean);
  const input = (
    <input
      className={classes.join(" ")}
      id={id}
      name={id}
      type={props.type ?? "text"}
      value={value}
      onChange={(event) => onChange(event.target.value)}
      inputMode={props.inputMode}
      autoComplete={props.autoComplete}
      spellCheck={props.spellCheck}
      aria-describedby={describedBy(id, hint, error)}
    />
  );

  return (
    <div className={groupClass(error)}>
      <label className="govuk-label" htmlFor={id}>
        {label}
      </label>
      {hint ? <Hint id={`${id}-hint`}>{hint}</Hint> : null}
      {error ? <ErrorMessage id={`${id}-error`}>{error}</ErrorMessage> : null}
      {prefix || suffix ? (
        <div className="govuk-input__wrapper">
          {prefix ? (
            <div className="govuk-input__prefix" aria-hidden="true">
              {prefix}
            </div>
          ) : null}
          {input}
          {suffix ? (
            <div className="govuk-input__suffix" aria-hidden="true">
              {suffix}
            </div>
          ) : null}
        </div>
      ) : (
        input
      )}
      {props.help}
    </div>
  );
}

type SelectProps = {
  id: string;
  label: ReactNode;
  options: { value: string; label: string }[];
  value: string;
  onChange: (value: string) => void;
  hint?: ReactNode;
  error?: string | undefined;
  help?: ReactNode;
};

/** A GOV.UK select, for choosing one of more options than radios can comfortably show. */
export function Select(props: SelectProps) {
  const { id, label, options, value, onChange, hint, error, help } = props;
  return (
    <div className={groupClass(error)}>
      <label className="govuk-label" htmlFor={id}>
        {label}
      </label>
      {hint ? <Hint id={`${id}-hint`}>{hint}</Hint> : null}
      {error ? <ErrorMessage id={`${id}-error`}>{error}</ErrorMessage> : null}
      <select
        className={error ? "govuk-select govuk-select--error" : "govuk-select"}
        id={id}
        name={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        aria-describedby={describedBy(id, hint, error)}
      >
        <option value="">Choose an option</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {help}
    </div>
  );
}

type MoneyInputProps = Omit<TextInputProps, "prefix" | "inputMode" | "width" | "type">;

/** A whole-pounds amount, with a £ prefix and a numeric keyboard on mobile. */
export function MoneyInput(props: MoneyInputProps) {
  return <TextInput {...props} prefix="£" inputMode="numeric" width="10" spellCheck={false} />;
}

export type DateParts = { day: string; month: string; year: string };

type DateInputProps = {
  id: string;
  legend: ReactNode;
  value: DateParts;
  onChange: (value: DateParts) => void;
  hint?: ReactNode;
  error?: string | undefined;
  help?: ReactNode;
};

export function DateInput(props: DateInputProps) {
  const { id, legend, value, onChange, hint, error, help } = props;
  const parts = [
    { key: "day", label: "Day", width: "2" },
    { key: "month", label: "Month", width: "2" },
    { key: "year", label: "Year", width: "4" },
  ] as const;

  return (
    <div className={groupClass(error)}>
      <fieldset
        className="govuk-fieldset"

        aria-describedby={describedBy(id, hint, error)}
      >
        <legend className="govuk-fieldset__legend govuk-fieldset__legend--s">{legend}</legend>
        {hint ? <Hint id={`${id}-hint`}>{hint}</Hint> : null}
        {error ? <ErrorMessage id={`${id}-error`}>{error}</ErrorMessage> : null}
        <div className="govuk-date-input" id={id}>
          {parts.map((part) => {
            const inputId = `${id}-${part.key}`;
            const classes = [
              "govuk-input",
              "govuk-date-input__input",
              `govuk-input--width-${part.width}`,
              error ? "govuk-input--error" : "",
            ].filter(Boolean);
            return (
              <div className="govuk-date-input__item" key={part.key}>
                <div className="govuk-form-group">
                  <label className="govuk-label govuk-date-input__label" htmlFor={inputId}>
                    {part.label}
                  </label>
                  <input
                    className={classes.join(" ")}
                    id={inputId}
                    name={inputId}
                    type="text"
                    inputMode="numeric"
                    value={value[part.key]}
                    onChange={(event) => onChange({ ...value, [part.key]: event.target.value })}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </fieldset>
      {help}
    </div>
  );
}

type RadioOption<T extends string> = {
  value: T;
  label: string;
  hint?: string | undefined;
  /** Questions revealed under the option while it is selected. */
  conditional?: ReactNode;
};

type RadiosProps<T extends string> = {
  name: string;
  legend: ReactNode;
  options: RadioOption<T>[];
  value: T | "";
  onChange: (value: T) => void;
  hint?: ReactNode;
  error?: string | undefined;
  inline?: boolean;
  help?: ReactNode;
};

export function Radios<T extends string>(props: RadiosProps<T>) {
  const { name, legend, options, value, onChange, hint, error } = props;

  return (
    <div className={groupClass(error)}>
      <fieldset className="govuk-fieldset" aria-describedby={describedBy(name, hint, error)}>
        <legend className="govuk-fieldset__legend govuk-fieldset__legend--s">{legend}</legend>
        {hint ? <Hint id={`${name}-hint`}>{hint}</Hint> : null}
        {error ? <ErrorMessage id={`${name}-error`}>{error}</ErrorMessage> : null}
        <div className={props.inline ? "govuk-radios govuk-radios--inline" : "govuk-radios"}>
          {options.map((option, index) => {
            const inputId = index === 0 ? name : `${name}-${option.value}`;
            const checked = value === option.value;
            const revealed = checked && option.conditional;
            return (
              <Fragment key={option.value}>
                <div className="govuk-radios__item">
                  <input
                    className="govuk-radios__input"
                    id={inputId}
                    name={name}
                    type="radio"
                    value={option.value}
                    checked={checked}
                    onChange={() => onChange(option.value)}
                    aria-describedby={option.hint ? `${inputId}-item-hint` : undefined}
                    aria-controls={option.conditional ? `${inputId}-conditional` : undefined}
                  />
                  <label className="govuk-label govuk-radios__label" htmlFor={inputId}>
                    {option.label}
                  </label>
                  {option.hint ? (
                    <div id={`${inputId}-item-hint`} className="govuk-hint govuk-radios__hint">
                      {option.hint}
                    </div>
                  ) : null}
                </div>
                {option.conditional ? (
                  <div
                    className={
                      revealed
                        ? "govuk-radios__conditional"
                        : "govuk-radios__conditional govuk-radios__conditional--hidden"
                    }
                    id={`${inputId}-conditional`}
                  >
                    {revealed ? option.conditional : null}
                  </div>
                ) : null}
              </Fragment>
            );
          })}
        </div>
      </fieldset>
      {props.help}
    </div>
  );
}

type CheckboxProps = {
  id: string;
  label: ReactNode;
  checked: boolean;
  onChange: (checked: boolean) => void;
  hint?: ReactNode;
  error?: string | undefined;
  help?: ReactNode;
};

export function Checkbox(props: CheckboxProps) {
  const { id, label, checked, onChange, hint, error, help } = props;
  return (
    <div className={groupClass(error)}>
      {error ? <ErrorMessage id={`${id}-error`}>{error}</ErrorMessage> : null}
      <div className="govuk-checkboxes">
        <div className="govuk-checkboxes__item">
          <input
            className="govuk-checkboxes__input"
            id={id}
            name={id}
            type="checkbox"
            checked={checked}
            onChange={(event) => onChange(event.target.checked)}
            aria-describedby={describedBy(id, hint, error)}
          />
          <label className="govuk-label govuk-checkboxes__label" htmlFor={id}>
            {label}
          </label>
          {hint ? (
            <div id={`${id}-hint`} className="govuk-hint govuk-checkboxes__hint">
              {hint}
            </div>
          ) : null}
        </div>
      </div>
      {help}
    </div>
  );
}

type CheckboxesProps<T extends string> = {
  name: string;
  legend: ReactNode;
  options: { value: T; label: string; hint?: string | undefined }[];
  /** An answer that excludes every other option, like "None of these", shown after "or". */
  exclusive?: { value: T; label: string };
  /** The legend's size: ``m`` for a page's main question, ``s`` for one of several. */
  legendSize?: "m" | "s";
  value: T[];
  onChange: (value: T[]) => void;
  hint?: ReactNode;
  error?: string | undefined;
};

/** GOV.UK checkboxes with an exclusive "none" option: choosing one clears the others. */
export function Checkboxes<T extends string>(props: CheckboxesProps<T>) {
  const { name, legend, options, exclusive, value, onChange, hint, error } = props;

  function toggle(option: T, checked: boolean) {
    if (option === exclusive?.value) onChange(checked ? [option] : []);
    else {
      const others = value.filter((chosen) => chosen !== option && chosen !== exclusive?.value);
      onChange(checked ? [...others, option] : others);
    }
  }

  function item(option: { value: T; label: string; hint?: string | undefined }, index: number) {
    const inputId = index === 0 ? name : `${name}-${option.value}`;
    return (
      <div className="govuk-checkboxes__item" key={option.value}>
        <input
          className="govuk-checkboxes__input"
          id={inputId}
          name={name}
          type="checkbox"
          value={option.value}
          checked={value.includes(option.value)}
          onChange={(event) => toggle(option.value, event.target.checked)}
          aria-describedby={option.hint ? `${inputId}-item-hint` : undefined}
        />
        <label className="govuk-label govuk-checkboxes__label" htmlFor={inputId}>
          {option.label}
        </label>
        {option.hint ? (
          <div id={`${inputId}-item-hint`} className="govuk-hint govuk-checkboxes__hint">
            {option.hint}
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <div className={groupClass(error)}>
      <fieldset className="govuk-fieldset" aria-describedby={describedBy(name, hint, error)}>
        <legend
          className={`govuk-fieldset__legend govuk-fieldset__legend--${props.legendSize ?? "m"}`}
        >
          {legend}
        </legend>
        {hint ? <Hint id={`${name}-hint`}>{hint}</Hint> : null}
        {error ? <ErrorMessage id={`${name}-error`}>{error}</ErrorMessage> : null}
        <div className="govuk-checkboxes">
          {options.map(item)}
          {exclusive ? (
            <>
              <div className="govuk-checkboxes__divider">or</div>
              {item(exclusive, options.length)}
            </>
          ) : null}
        </div>
      </fieldset>
    </div>
  );
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "warning";
};

export function Button({ variant = "primary", className, ...rest }: ButtonProps) {
  const classes = [
    "govuk-button",
    variant === "primary" ? "" : `govuk-button--${variant}`,
    className ?? "",
  ];
  return (
    <button
      type="submit"
      className={classes.filter(Boolean).join(" ")}
      data-module="govuk-button"
      {...rest}
    />
  );
}

/** A GOV.UK start button: a link styled as a button, with an arrow. */
export function StartButton({ to, children = "Start now" }: { to: string; children?: ReactNode }) {
  return (
    <Link
      to={to}
      draggable={false}
      className="govuk-button govuk-button--start"
      data-module="govuk-button"
    >
      {children}
      <StartButtonArrow />
    </Link>
  );
}

function StartButtonArrow() {
  return (
    <svg
      className="govuk-button__start-icon"
      xmlns="http://www.w3.org/2000/svg"
      width="17.5"
      height="19"
      viewBox="0 0 33 40"
      aria-hidden="true"
      focusable="false"
    >
      <path fill="currentColor" d="M0 0h13l20 20-20 20H0l20-20z" />
    </svg>
  );
}
