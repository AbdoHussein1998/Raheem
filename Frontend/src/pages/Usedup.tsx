import { Hero } from "../components/layout/Hero";
import { StatusPanel } from "../components/ui/StatusPanel";
import { WhatsAppContactButton } from "../components/ui/WhatsAppContactButton";
import { goBack } from "../hooks/goBack";

export function Usedup() {
  return (
    <main className="w-full pt-20 sm:pt-24 bg-background min-h-screen flex flex-col flex-1">
      <Hero />
      <StatusPanel
        icon="hourglass_empty"
        title="Campaign Limit Reached"
        message="This access link has reached its permitted usage limit. Contact the campaign organizer for assistance."
        button={
          <div className="flex flex-wrap justify-center items-center gap-space-sm mt-2">
            <button type="button" onClick={goBack} className="rounded-lg bg-primary px-space-md py-space-sm font-title-sm text-on-primary">
              Go Back
            </button>
            <WhatsAppContactButton />
          </div>
        }
      />
    </main>
  );
}
