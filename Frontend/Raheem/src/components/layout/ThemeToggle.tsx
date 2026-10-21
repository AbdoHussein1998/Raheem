import { useTheme } from '../../hooks/useTheme';

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={isDark ? 'تفعيل الوضع الفاتح' : 'تفعيل الوضع الداكن'}
      aria-pressed={isDark}
      title={isDark ? 'الوضع الفاتح' : 'الوضع الداكن'}
      className="w-10 h-10 rounded-full flex items-center justify-center bg-surface-container-low text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface transition-colors border border-outline-variant/30"
    >
      <span className="material-symbols-outlined text-[20px]" aria-hidden="true">
        {isDark ? 'light_mode' : 'dark_mode'}
      </span>
    </button>
  );
}
