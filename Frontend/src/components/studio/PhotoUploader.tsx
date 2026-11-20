import { useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";
import type { SourcePhoto } from "../../types/studio";
import { MaterialIcon } from "../ui/MaterialIcon";

interface Props {
  photo: SourcePhoto | null;
  loading: boolean;
  onSelect: (file?: File) => void;
  onRemove: () => void;
}

export function PhotoUploader({ photo, loading, onSelect, onRemove }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const chooseFile = () => {
    if (!inputRef.current) return;
    inputRef.current.value = "";
    inputRef.current.click();
  };
  const onFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    onSelect(event.target.files?.[0]);
  };
  const drop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);
    onSelect(event.dataTransfer.files?.[0]);
  };

  return (
    <div className="flex flex-col gap-space-sm">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <span className="flex items-center gap-space-xs text-title-sm font-title-sm text-on-surface">
          <span className="w-5 h-5 rounded-full bg-primary/20 text-primary flex items-center justify-center text-label-sm font-label-sm font-bold">1</span>
          Upload Travel or Portrait Photo
        </span>
        <span className="text-label-sm font-label-sm text-on-surface-variant">PNG, JPG, WebP • Max 25MB</span>
      </div>
      <div
        id="drop-zone"
        className={`relative group rounded-lg bg-surface-container-lowest p-space-md flex flex-col items-center justify-center text-center cursor-pointer transition-all hover:bg-surface-container-low border border-dashed border-outline-variant/60 hover:border-secondary ${dragging ? "is-dragging" : ""}`}
        onDragOver={event => { event.preventDefault(); setDragging(true); }}
        onDragLeave={event => { event.preventDefault(); setDragging(false); }}
        onDrop={drop}
      >
        <input
          id="photo-upload"
          ref={inputRef}
          aria-label="Upload a travel or portrait photo"
          accept="image/png,image/jpeg,image/webp"
          className="absolute inset-0 opacity-0 cursor-pointer w-full h-full z-10"
          type="file"
          disabled={loading}
          onChange={onFileChange}
        />
        <div className="w-12 h-12 rounded-full bg-surface-container-high flex items-center justify-center mb-space-xs group-hover:scale-110 transition-transform">
          <MaterialIcon className={`text-headline-sm ${photo ? "text-secondary" : "text-primary"}`} name={photo ? "task_alt" : "cloud_upload"} />
        </div>
        <p className="font-title-sm text-title-sm text-on-surface break-all">{loading ? "Reading photo..." : (photo?.file.name || "Drag & drop photo or browse device")}</p>
        <p className="font-body-sm text-body-sm text-on-surface-variant mt-0.5">Memories from Giza, Nile, Luxor or portraits work best</p>
        {loading && (
          <div className="w-full mt-space-sm flex flex-col gap-1">
            <div className="w-full h-1.5 rounded-full bg-surface-container overflow-hidden">
              <div className="h-full bg-secondary animate-pulse w-2/3" />
            </div>
            <span className="text-label-sm font-label-sm text-secondary">Reading local photo...</span>
          </div>
        )}
      </div>
      <button
        type="button"
        disabled={loading}
        onClick={chooseFile}
        className={`w-full py-space-xs px-space-md rounded-lg font-title-sm text-title-sm flex items-center justify-center gap-space-xs transition-colors shadow-sm disabled:opacity-50 ${photo ? "bg-emerald-600 text-white" : "bg-surface-container-high text-on-surface hover:bg-surface-bright"}`}
      >
        <MaterialIcon name={photo ? "check_circle" : loading ? "sync" : "add_photo_alternate"} className="text-title-md" />
        {photo ? "Photo Uploaded Successfully" : loading ? "Reading photo..." : "Choose File"}
      </button>
      {photo && (
        <div className="flex items-center justify-between gap-2 p-space-xs rounded-lg bg-surface-container-low text-label-sm font-label-sm text-on-surface-variant">
          <div className="flex items-center gap-space-xs min-w-0 flex-wrap">
            <MaterialIcon name="image" className="text-secondary text-title-sm" />
            <span className="text-on-surface truncate max-w-[140px]" title={photo.file.name}>{photo.file.name}</span>
            <span className="text-outline">{photo.dimensions}</span>
            <span className="px-1.5 py-0.5 rounded bg-surface-container">{photo.sizeLabel}</span>
          </div>
          <button type="button" onClick={onRemove} className="shrink-0 text-error hover:text-on-surface transition-colors flex items-center gap-0.5">
            <MaterialIcon name="close" className="text-label-md" /> Remove
          </button>
        </div>
      )}
    </div>
  );
}
