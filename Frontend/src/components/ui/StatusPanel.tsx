import { MaterialIcon } from "./MaterialIcon";
import type { ReactNode } from "react";

interface StatusPanelProps {
  icon: string;
  title: string;
  message: string;
  button?: ReactNode;
}

/** Shared, presentational empty/error state used by route-level pages. */
export function StatusPanel({
  icon,
  title,
  message,
  button,
}: StatusPanelProps) {
  return (
    <section className="w-full px-margin py-space-xl flex-1 flex items-center justify-center">
      <div
        className="w-full max-w-xl rounded-xl bg-surface-container border border-surface-container-high p-space-lg text-center shadow-xl flex flex-col items-center gap-space-md"
        role="status"
      >
        <MaterialIcon name={icon} className="text-display-lg text-primary" />

        <h2 className="text-headline-md font-headline-md text-on-surface font-bold">
          {title}
        </h2>

        <p className="text-body-md text-on-surface-variant">{message}</p>

        {button && button}
      </div>
    </section>
  );
}
