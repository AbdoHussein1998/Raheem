import { StatusPanel } from "../ui/StatusPanel";
import { WhatsAppContactButton } from "../ui/WhatsAppContactButton";
import { goBack } from "../../hooks/goBack";

export function UnauthorizedMessage() {
  return (
    <div className="flex flex-col items-center gap-4">
      <StatusPanel
        icon="lock"
        title="Unauthorized Access"
        message="You do not have permission to view this page. Please contact the campaign organizer for assistance."
        button={
          <div className="flex flex-wrap justify-center items-center gap-space-sm mt-2">
            <button type="button" onClick={goBack} className="rounded-lg bg-primary px-space-md py-space-sm font-title-sm text-on-primary">
              Go Back
            </button>
            <WhatsAppContactButton />
          </div>
        }
      />
    </div>
  );
}
