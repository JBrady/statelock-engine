import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
};

export function Button({
  className,
  variant = "primary",
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-full px-4 py-2 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-clay disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary" &&
          "bg-gradient-to-r from-moss to-teal text-white shadow-product hover:brightness-105",
        variant === "secondary" &&
          "border border-black/10 bg-white/80 text-ink hover:bg-white",
        variant === "ghost" && "text-ink hover:bg-black/5",
        className,
      )}
      type={type}
      {...props}
    />
  );
}
