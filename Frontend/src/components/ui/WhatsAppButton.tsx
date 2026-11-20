import { MaterialIcon } from "./MaterialIcon";

interface WhatsAppButtonProps {
  onClick?: () => void;
  className?: string;
}

export function WhatsAppButton({
  onClick,
  className = "",
}: WhatsAppButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2 font-semibold text-white transition-colors hover:bg-green-700 ${className}`}
    >
      <MaterialIcon name="chat" />

      <span>Chat on WhatsApp</span>
    </button>
  );
}
