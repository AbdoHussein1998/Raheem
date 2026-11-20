import { StatusPanel } from "../components/ui/StatusPanel";

/** Shown by React Router when a route fails to render. */
export function RouteErrorPage() {
  return (
    <main className="min-h-screen flex flex-col bg-background text-on-surface">
      <StatusPanel
        icon="error_outline"
        title="Something went wrong"
        message="This page couldn't be displayed. Please reload the page and try again."
        button={
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-2 rounded-lg bg-primary px-space-md py-space-sm font-title-sm text-on-primary"
          >
            Reload page
          </button>
        }
      />
    </main>
  );
}
