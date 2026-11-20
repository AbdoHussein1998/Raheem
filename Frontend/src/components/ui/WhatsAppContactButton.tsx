import { WhatsAppButton } from "./WhatsAppButton";

interface WhatsAppContactButtonProps {
  className?: string;
}

/** Route pages share one validated contact action and one Vite environment key. */
export function WhatsAppContactButton({ className }: WhatsAppContactButtonProps) {
  const number = import.meta.env.VITE_WHATSAPP_PHONE_NUMBER?.replace(/\D/g, "");
  if (!number) return null;

  return (
    <WhatsAppButton
      className={className}
      onClick={() => window.open(`https://wa.me/${number}`, "_blank", "noopener,noreferrer")}
    />
  );
}
