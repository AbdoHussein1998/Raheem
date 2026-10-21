import { Link, useParams } from "react-router-dom";
import { gateways } from "../features/gateways/config/gateways";
import NotFoundPage from "./NotFoundPage";

/** The homepage advertises gateways whose functional pages are not yet included. */
export default function GatewayPage() {
  const { slug } = useParams<{ slug: string }>();
  const gateway = gateways.find((item) => item.route === `/${slug}`);

  if (!gateway) {
    return <NotFoundPage />;
  }

  return (
    <main className="flex-grow w-full pt-28 pb-space-xl px-margin-mobile lg:px-margin">
      <section className="max-w-3xl mx-auto rounded-2xl border border-surface-container-high/80 bg-surface-container-lowest p-space-lg text-center shadow-[0_4px_24px_-4px_rgba(15,56,44,0.06)]">
        <span
          className="material-symbols-outlined text-[44px] text-secondary"
          aria-hidden="true"
        >
          {gateway.icon}
        </span>
        <h1 className="text-headline-lg font-headline-lg font-bold text-primary mt-space-sm mb-space-sm">
          {gateway.title}
        </h1>
        <p className="text-on-surface-variant mb-space-md">
          {gateway.description}
        </p>
        <p className="text-on-surface-variant mb-space-lg">
          هذه الصفحة قيد التطوير.
        </p>
        <Link
          to="/"
          className="inline-flex items-center justify-center rounded-xl bg-primary-container text-on-primary px-space-lg py-space-sm hover:bg-primary transition-colors"
        >
          العودة للرئيسية
        </Link>
      </section>
    </main>
  );
}
