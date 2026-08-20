import type { InputHTMLAttributes, ReactNode } from "react";

import "../../styles/components/ui/Input.css";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  startIcon?: ReactNode;
  endIcon?: ReactNode;
}

export default function Input({
  label,
  error,
  helperText,
  startIcon,
  endIcon,
  id,
  className = "",
  ...props
}: InputProps) {
  const inputId = id ?? props.name;

  const classes = [
    "ui-input",
    startIcon ? "ui-input--with-start-icon" : "",
    endIcon ? "ui-input--with-end-icon" : "",
    error ? "ui-input--error" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="ui-input-field">
      {label && (
        <label className="ui-input-label" htmlFor={inputId}>
          {label}
        </label>
      )}

      <div className="ui-input-wrapper">
        {startIcon && (
          <span className="ui-input-icon ui-input-icon--start">
            {startIcon}
          </span>
        )}

        <input
          id={inputId}
          className={classes}
          aria-invalid={Boolean(error)}
          aria-describedby={
            error
              ? `${inputId}-error`
              : helperText
                ? `${inputId}-helper`
                : undefined
          }
          {...props}
        />

        {endIcon && (
          <span className="ui-input-icon ui-input-icon--end">
            {endIcon}
          </span>
        )}
      </div>

      {error ? (
        <span
          id={`${inputId}-error`}
          className="ui-input-message ui-input-message--error"
        >
          {error}
        </span>
      ) : helperText ? (
        <span id={`${inputId}-helper`} className="ui-input-message">
          {helperText}
        </span>
      ) : null}
    </div>
  );
}