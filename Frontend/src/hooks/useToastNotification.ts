import { useCallback, useState } from "react";
import type { ToastMessage } from "../types/studio";

/** One place for the ephemeral feedback shared by all studio actions. */
export function useToastNotification() {
  const [toast, setToast] = useState<ToastMessage | null>(null);

  const notify = useCallback((message: string, isError = false) => {
    setToast({ id: Date.now(), message, error: isError });
  }, []);

  return { toast, notify };
}
