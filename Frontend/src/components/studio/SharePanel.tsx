import { MaterialIcon } from "../ui/MaterialIcon";

interface Props {
  enabled: boolean;
  facebookEnabled: boolean;
  facebookLoading: boolean;
  onNativeShare: () => void;
  onFacebookShare: () => void;
}

/** Presentation-only actions; native app sharing and Facebook use different flows. */
export function SharePanel({
  enabled, facebookEnabled, facebookLoading, onNativeShare, onFacebookShare,
}: Props) {
  return (
    <div className="theme-card flex flex-col gap-space-sm bg-surface-container rounded-xl p-space-md shadow-lg border border-surface-container-high">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-space-xs">
          <MaterialIcon name="share" className="text-secondary text-title-md" />
          <span className="font-headline-sm text-headline-sm text-on-surface font-semibold">Share Your Celebration Photo</span>
        </div>
        <span className={`text-label-sm font-label-sm ${enabled ? "text-secondary font-semibold" : "text-on-surface-variant"}`}>
          {enabled ? "Your branded photo is ready" : "Generate a photo to unlock sharing"}
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-xs">
        <button type="button" disabled={!enabled} onClick={onNativeShare}
          className="theme-download-action w-full py-space-sm px-space-md rounded-lg bg-gradient-to-r from-primary to-primary-container text-on-primary-container hover:shadow-[0_0_24px_rgba(245,158,11,0.5)] shadow-md transition-all flex items-center justify-center gap-space-xs disabled:opacity-40 disabled:cursor-not-allowed font-semibold">
          <MaterialIcon name="ios_share" className="text-headline-sm" />
          <span className="font-title-sm text-title-sm">Share to Apps</span>
        </button>
        <button type="button" disabled={!facebookEnabled || facebookLoading} onClick={onFacebookShare}
          className="w-full py-space-sm px-space-md rounded-lg bg-secondary text-on-secondary hover:bg-secondary-container shadow-md transition-all flex items-center justify-center gap-space-xs disabled:opacity-40 disabled:cursor-not-allowed font-semibold">
          <MaterialIcon name="share" className="text-headline-sm" />
          <span className="font-title-sm text-title-sm">{facebookLoading ? "Opening Facebook..." : "Share to Facebook"}</span>
        </button>
      </div>
      {enabled && !facebookEnabled && (
        <p className="text-label-sm text-on-surface-variant" role="status">
          Facebook sharing is unavailable for this photo because its public preview was not stored.
          You can still try Share to Apps.
        </p>
      )}
    </div>
  );
}
