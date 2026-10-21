import { Outlet } from "react-router-dom";
import Header from "./Header";
import MobileNavigation from "./MobileNavigation";
import Footer from "./Footer";
import raheem from "../../assets/raheem.png";

/** Consistent chrome for all public-facing routes. */
export default function MainLayout() {
  return (
    <div className="relative min-h-screen flex flex-col overflow-hidden bg-surface font-body-md text-body-md text-on-surface antialiased selection:bg-secondary-fixed selection:text-on-secondary-fixed">
      {/* Background Logo Watermark */}
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 z-0 flex items-center justify-center"
      >
        <img
          src={raheem}
          alt=""
          className="w-[350px] max-w-[70vw] object-contain opacity-[0.04] grayscale"
        />
      </div>

      {/* Page Content */}
      <div className="relative z-10 flex min-h-screen flex-col">
        <Header />

        <main className="flex-1">
          <Outlet />
        </main>

        <Footer />

        <MobileNavigation />
      </div>
    </div>
  );
}
