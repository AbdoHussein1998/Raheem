import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { generateImage } from "../services/imageProcessing";
import { ImageApiError, type GeneratedImage } from "../services/imageGeneration.api";
import { useGenerationProgress } from "./useGenerationProgress";
import type { SourcePhoto, StyleId } from "../types/studio";

interface GenerationSettings {
  photo: SourcePhoto | null;
  style: StyleId;
}

/** Owns generation state, authorization navigation, and generated object URL cleanup. */
export function useImageGeneration(
  notify: (message: string, isError?: boolean) => void,
  setError: (message: string) => void,
) {
  const navigate = useNavigate();
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [generatedImage, setGeneratedImage] = useState<GeneratedImage | null>(null);
  const [generating, setGenerating] = useState(false);
  const {
    progress, progressStatus, startProgress, completeProgress, resetProgress,
  } = useGenerationProgress();
  const resultUrlRef = useRef<string | null>(null);
  const generationRevision = useRef(0);
  const abortRef = useRef<AbortController | null>(null);
  const inFlightRef = useRef(false);

  const invalidateResult = useCallback(() => {
    generationRevision.current += 1;
    abortRef.current?.abort();
    inFlightRef.current = false;
    abortRef.current = null;
    if (resultUrlRef.current) URL.revokeObjectURL(resultUrlRef.current);
    resultUrlRef.current = null;
    setResultUrl(null);
    setGeneratedImage(null);
    setGenerating(false);
    resetProgress();
  }, [resetProgress]);

  const generate = useCallback(async ({ photo, style }: GenerationSettings) => {
    if (!photo) {
      setError("Please upload a photo first.");
      return;
    }
    if (inFlightRef.current) return;

    setError("");
    inFlightRef.current = true;
    setGenerating(true);
    startProgress();
    const revision = ++generationRevision.current;
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const image = await generateImage({ file: photo.file, style, signal: controller.signal });
      if (revision !== generationRevision.current) return;

      if (resultUrlRef.current) URL.revokeObjectURL(resultUrlRef.current);
      const nextUrl = URL.createObjectURL(image.blob);
      resultUrlRef.current = nextUrl;
      setResultUrl(nextUrl);
      setGeneratedImage(image);
      completeProgress();
      notify(image.storageStatus === "stored"
        ? "Your photo is ready to share."
        : "Your photo is ready for device sharing. Facebook sharing is temporarily unavailable.");
    } catch (caught) {
      if (revision !== generationRevision.current) return;
      resetProgress();
      if (caught instanceof DOMException && caught.name === "AbortError") return;
      if (caught instanceof ImageApiError) {
        if (caught.status === 401 || (caught.status === 400 && /uuid|visitor/i.test(caught.message))) {
          navigate("/unauthorized");
          return;
        }
        if (caught.status === 403) {
          navigate("/usedup");
          return;
        }
      }
      const message = caught instanceof Error ? caught.message : "Could not process the photo.";
      setError(message);
      notify(message, true);
    } finally {
      if (revision === generationRevision.current) {
        inFlightRef.current = false;
        setGenerating(false);
        abortRef.current = null;
      }
    }
  }, [navigate, notify, setError, startProgress, completeProgress, resetProgress]);

  useEffect(() => () => {
    abortRef.current?.abort();
    generationRevision.current += 1;
    if (resultUrlRef.current) URL.revokeObjectURL(resultUrlRef.current);
  }, []);

  return { resultUrl, generatedImage, generating, progress, progressStatus, invalidateResult, generate };
}
