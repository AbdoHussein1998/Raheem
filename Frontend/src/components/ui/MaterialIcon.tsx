import type { HTMLAttributes } from "react";

type MaterialIconProps = HTMLAttributes<HTMLSpanElement> & { name: string };

export function MaterialIcon({ name, className = "", ...props }: MaterialIconProps) {
  return <span aria-hidden="true" className={`material-symbols-outlined ${className}`} {...props}>{name}</span>;
}
