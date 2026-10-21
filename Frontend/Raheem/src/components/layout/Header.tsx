import ThemeToggle from "./ThemeToggle";
import { NavLink, Link } from "react-router-dom";
import logo from "../../assets/raheem-logo.ico";

const links = [
  { to: "/", label: "الرئيسية", end: true },
  { to: "/news", label: "اخر الاخبار" },
  { to: "/ask-raheem", label: "اسأل رحيم" },
  { to: "/consultations", label: "الاستشارات" },
  { to: "/endowment", label: "الوقف والدعم" },
];
export default function Header() {
  return (
    <header className="fixed top-0 w-full z-50 bg-surface/90 backdrop-blur-xl border-b border-surface-container-high/60 shadow-[0_1px_8px_rgba(0,0,0,0.03)]">
      <div className="h-20 max-w-7xl mx-auto px-margin-mobile lg:px-margin flex items-center justify-between gap-space-md">
        <Link className="flex items-center gap-space-sm group" to="/">
          <img
            alt="شعار من حب الله دل عليه"
            className="w-10 h-10 rounded-full object-cover ring-2 ring-primary/10 group-hover:ring-surface-tint transition-all"
            src={logo}
          />
          <div className="flex flex-col text-right">
            <span className="font-headline-sm text-headline-sm text-primary font-bold tracking-tight">
              من حب الله دل عليه
            </span>
            <span className="font-label-sm text-label-sm text-secondary hidden sm:inline-block">
              اجعل لك مشروع دعوة
            </span>
          </div>
        </Link>
        <nav
          aria-label="التنقل الرئيسي"
          className="hidden lg:flex items-center gap-1.5"
        >
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) =>
                `px-space-sm py-space-xs rounded-lg text-body-sm transition-all ${isActive ? "bg-primary-container text-on-primary font-semibold shadow-sm" : "text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface"}`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="flex items-center gap-space-xs">
          <span
            className="flex items-center gap-space-xs h-10 px-3.5 rounded-full bg-surface-container-low text-on-surface-variant border border-outline-variant/30"
            aria-label="البحث غير متاح بعد"
            title="البحث قريباً"
          >
            <span
              className="material-symbols-outlined text-[19px]"
              aria-hidden="true"
            >
              search
            </span>
            <span className="hidden md:inline font-label-sm text-label-sm bg-surface-container-lowest px-1.5 py-0.5 rounded text-outline border border-outline-variant/40">
              قريباً
            </span>
          </span>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
