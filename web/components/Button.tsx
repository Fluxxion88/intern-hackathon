"use client";

import React from "react";

type Variant = "primary" | "secondary" | "quiet";

export function Button({
  variant = "primary",
  children,
  onClick,
  disabled = false,
  type = "button",
  full = false,
  className = "",
  ariaLabel,
}: {
  variant?: Variant;
  children: React.ReactNode;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  disabled?: boolean;
  type?: "button" | "submit";
  full?: boolean;
  className?: string;
  ariaLabel?: string;
}) {
  const cls =
    variant === "primary" ? "btn-primary" : variant === "secondary" ? "btn-secondary" : "btn-quiet";
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
      className={`${cls} ${full ? "btn-full" : ""} ${className}`}
    >
      {children}
    </button>
  );
}
