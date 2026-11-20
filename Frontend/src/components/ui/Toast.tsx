import { useEffect, useState } from "react";
import type { ToastMessage } from "../../types/studio";
import { MaterialIcon } from "./MaterialIcon";

interface Props { toast: ToastMessage | null }

export function Toast({ toast }: Props) {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    if (!toast) return;
    setVisible(true);
    const timer = window.setTimeout(() => setVisible(false), 3200);
    return () => window.clearTimeout(timer);
  }, [toast]);
  return (
    <div role="status" aria-live="polite" className={`fixed bottom-6 right-6 z-[70] flex items-center gap-space-sm px-space-md py-space-sm rounded-lg bg-surface-container-highest shadow-xl text-on-surface text-body-md font-body-md transition-all duration-300 ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-3 pointer-events-none"}`}>
      <MaterialIcon name={toast?.error ? "error" : "check_circle"} className={toast?.error ? "text-error" : "text-secondary"} />
      <span>{toast?.message ?? ""}</span>
    </div>
  );
}
