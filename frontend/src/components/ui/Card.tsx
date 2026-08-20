import type { HTMLAttributes, ReactNode } from "react";

import "../../styles/components/ui/Card.css";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  interactive?: boolean;
  padding?: "sm" | "md" | "lg";
}

export default function Card({
  children,
  interactive = false,
  padding = "md",
  className = "",
  ...props
}: CardProps) {
  const classes = [
    "ui-card",
    `ui-card--${padding}`,
    interactive ? "ui-card--interactive" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
}