/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_IMAGE_API_URL?: string;
  readonly VITE_WHATSAPP_PHONE_NUMBER?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
