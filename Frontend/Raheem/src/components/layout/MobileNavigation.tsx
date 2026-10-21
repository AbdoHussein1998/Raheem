import { NavLink } from 'react-router-dom';
const links = [
  {to:'/', icon:'grid_view',label:'البوابات'},
  {to:'/ask-raheem',icon:'smart_toy',label:'اسأل رحيم'},
  {to:'/consultations',icon:'support_agent',label:'استشارة'},
  {to:'/endowment',icon:'volunteer_activism',label:'الوقف'},
];
export default function MobileNavigation() {
  return <nav aria-label="التنقل للجوال" className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-surface/95 backdrop-blur-xl border-t border-surface-container-high h-16 flex items-center justify-around px-space-xs shadow-[0_-2px_12px_rgba(0,0,0,0.06)]">
    {links.map(link => <NavLink key={link.to} to={link.to} end={link.to === '/'} className={({isActive}) => `flex flex-col items-center gap-0.5 ${isActive ? 'text-primary font-bold' : 'text-on-surface-variant hover:text-on-surface'}`}>
      <span className="material-symbols-outlined text-[20px]" aria-hidden="true">{link.icon}</span>
      <span className="font-label-sm text-label-sm">{link.label}</span>
    </NavLink>)}
  </nav>;
}
