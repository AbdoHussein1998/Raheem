export type GatewayId = 'news' | 'raheem' | 'consultation' | 'endowment';
export type GatewayFeature = { icon: string; title?: string; subtitle: string; color: 'gold' | 'green' };
export type Gateway = {
  id: GatewayId; number: string; route: string; icon: string; title: string;
  description: string; badge: string; badgeIcon?: string; badgePulse?: boolean;
  accent: string; iconBackground: string; badgeBackground: string;
  buttonBackground: string; buttonIcon: string; buttonLabel: string;
  features?: GatewayFeature[]; suggestions?: string[];
};
