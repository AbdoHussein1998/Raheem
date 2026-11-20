import { StatusPanel } from "../components/ui/StatusPanel";
import { WhatsAppContactButton } from "../components/ui/WhatsAppContactButton";

export function NotFoundPage() {
  return (
    <main className="w-full pt-20 sm:pt-24 min-h-screen flex flex-col flex-1">
      <StatusPanel
        icon="explore_off"
        title="Page Not Found"
        message="The page you requested does not exist or the link is no longer valid."
        button={<WhatsAppContactButton className="mt-2" />}
      />
    </main>
  );
}
