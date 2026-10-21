import { Link } from 'react-router-dom';
import type { Gateway } from '../types/gateway';

type Props = { gateway: Gateway };

export default function GatewayCard({ gateway }: Props) {
  return (
    <article id={gateway.id} className={`group relative bg-surface-container-lowest rounded-2xl p-space-md lg:p-space-lg shadow-[0_4px_24px_-4px_rgba(15,56,44,0.06)] hover:shadow-2xl hover:-translate-y-1.5 transition-all duration-300 border border-surface-container-high/80 flex flex-col justify-between overflow-hidden ${gateway.id === 'raheem' ? 'bg-gradient-to-br from-surface-container-lowest via-surface-container-lowest to-surface-container-low/70' : ''}`}>
      <div className={`absolute top-0 right-0 left-0 h-1.5 ${gateway.accent}`} />
      <div>
        <div className="flex items-start justify-between gap-space-sm mb-space-md">
          <div className={`w-14 h-14 rounded-xl flex items-center justify-center shadow-md group-hover:scale-105 transition-all ${gateway.iconBackground}`}>
            <span className="material-symbols-outlined text-[30px]" aria-hidden="true">{gateway.icon}</span>
          </div>
          <div className="flex items-center gap-1.5 flex-wrap justify-end">
            <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full font-label-sm text-label-sm font-semibold ${gateway.badgeBackground}`}>
              {gateway.badgePulse && <span className="w-2 h-2 rounded-full bg-secondary animate-pulse" />}
              {gateway.badgeIcon && <span className="material-symbols-outlined text-[15px]" aria-hidden="true">{gateway.badgeIcon}</span>}
              {gateway.badge}
            </span>
            <span className="px-2.5 py-1 rounded-full bg-surface-container-low text-outline font-label-sm text-label-sm font-bold">بوابة {gateway.number}</span>
          </div>
        </div>
        <h2 className="font-headline-lg text-headline-lg text-primary mb-space-xs font-bold group-hover:text-surface-tint transition-colors">{gateway.title}</h2>
        <p className="font-body-md text-body-md text-on-surface-variant mb-space-md leading-relaxed">{gateway.description}</p>
        {gateway.features && <div className="grid grid-cols-2 gap-space-xs mb-space-lg">
          {gateway.features.map(feature => <div key={feature.icon} className="bg-surface-container-low p-space-sm rounded-xl flex items-center gap-space-xs">
            <span className={`material-symbols-outlined text-[22px] ${feature.color === 'gold' ? 'text-secondary' : 'text-surface-tint'}`} aria-hidden="true">{feature.icon}</span>
            <div className="flex flex-col">
              {feature.title && <span className="font-headline-sm text-headline-sm text-primary font-bold">{feature.title}</span>}
              <span className="font-label-sm text-label-sm text-outline">{feature.subtitle}</span>
            </div>
          </div>)}
        </div>}
        {gateway.suggestions && <div className="flex flex-col gap-1.5 mb-space-lg">
          <span className="font-label-sm text-label-sm text-outline">تساؤلات شائعة يمكنك طرحها:</span>
          <div className="flex items-center gap-1.5 flex-wrap">
            {gateway.suggestions.map(suggestion => <span key={suggestion} className="px-2.5 py-1 rounded-lg bg-surface-container text-primary text-body-sm font-medium">{suggestion}</span>)}
          </div>
        </div>}
      </div>
      <div className="pt-space-xs border-t border-surface-container-high/60">
        <Link className={`w-full py-3.5 px-space-md rounded-xl font-headline-sm text-headline-sm flex items-center justify-center gap-2 shadow-md hover:shadow-lg transition-all group-hover:translate-x-0.5 ${gateway.buttonBackground}`} to={gateway.route}>
          <span>{gateway.buttonLabel}</span>
          <span className="material-symbols-outlined text-[22px]" aria-hidden="true">{gateway.buttonIcon}</span>
        </Link>
      </div>
    </article>
  );
}
