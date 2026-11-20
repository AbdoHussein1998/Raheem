import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Visual progress estimate for an API that does not report generation progress.
 *
 * The estimate reaches 90% after 80 seconds and waits there until the
 * generated image has been successfully received and decoded.
 * It never finishes a generation or imposes a request timeout.
 */
const ESTIMATED_DURATION_MS = 80_000;
const MAX_PENDING_PROGRESS = 90;
const UPDATE_INTERVAL_MS = 200;

type ProgressStatus = "idle" | "running" | "complete";

export function useGenerationProgress() {
  const [progress, setProgress] = useState(0);
  const [progressStatus, setProgressStatus] = useState<ProgressStatus>("idle");
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const resetProgress = useCallback(() => {
    clearTimer();
    setProgress(0);
    setProgressStatus("idle");
  }, [clearTimer]);

  const startProgress = useCallback(() => {
    clearTimer();
    setProgress(0);
    setProgressStatus("running");

    const startedAt = performance.now();
    timerRef.current = setInterval(() => {
      const elapsed = performance.now() - startedAt;
      const estimated = Math.floor(
        (elapsed / ESTIMATED_DURATION_MS) * MAX_PENDING_PROGRESS,
      );
      const nextProgress = Math.min(MAX_PENDING_PROGRESS, estimated);
      setProgress((current) =>
        current === nextProgress ? current : nextProgress,
      );

      if (nextProgress === MAX_PENDING_PROGRESS) clearTimer();
    }, UPDATE_INTERVAL_MS);
  }, [clearTimer]);

  const completeProgress = useCallback(() => {
    clearTimer();
    setProgress(100);
    setProgressStatus("complete");
  }, [clearTimer]);

  // Prevent the timer from updating an unmounted component.
  useEffect(() => clearTimer, [clearTimer]);

  return {
    progress,
    progressStatus,
    startProgress,
    completeProgress,
    resetProgress,
  };
}
