import type { Gateway } from '../types/gateway';

// Classes are complete literals so Tailwind includes them in the production build.
export const gateways: Gateway[] = [
  {
    id: 'news', number: '١', route: '/news', icon: 'newspaper',
    title: 'آخر الأخبار والمستجدات', description: 'اخر الشبهات المردود عليهاو اهم الاعلانات',
    badge: 'تغطيات وبيانات', badgePulse: true,
    accent: 'bg-gradient-to-l from-primary via-surface-tint to-primary-fixed-dim',
    iconBackground: 'bg-primary-container text-on-primary',
    badgeBackground: 'bg-secondary-fixed/70 text-on-secondary-fixed',
    buttonBackground: 'bg-primary-container hover:bg-primary text-on-primary',
    buttonLabel: 'تصفح آخر الأخبار والمستجدات', buttonIcon: 'arrow_left_alt',
    features: [
      {icon: 'campaign', subtitle: 'تغطيات  لاهم الشبهات', color: 'gold'},
      {icon: 'event_available', title: 'تحديث أسبوعي', subtitle: 'جدول الفعاليات والمجالس', color: 'green'},
    ],
  },
  {
    id: 'raheem', number: '٢', route: '/ask-raheem', icon: 'psychology',
    title: 'اسأل رحيم (المرشد الذكي المؤصل)',
    description: 'مساعد رقمي فوري مدرب بدقة على أمهات المصادر المعتمدة والتراث العلمي الأصيل، يمنحك تدبراً عميقاً وإجابات واضحة لتساؤلاتك الإيمانية والفكرية على مدار الساعة.',
    badge: 'ذكاء اصطناعي موثق', badgeIcon: 'auto_awesome',
    accent: 'bg-gradient-to-l from-surface-tint via-primary-fixed to-secondary',
    iconBackground: 'bg-surface-tint text-on-primary',
    badgeBackground: 'bg-primary-fixed text-on-primary-fixed-variant',
    buttonBackground: 'bg-surface-tint hover:bg-primary text-on-primary',
    buttonLabel: 'بدء المحادثة مع رحيم', buttonIcon: 'chat',
    suggestions: ['هل ظلم الاسلام المراءة ؟', 'كيف تتعارض نظرية التطور مع الاسلام ؟', 'لماذا يعتبر العلاج بالطاقة نوع من الالحاد ؟'],
  },
  {
    id: 'consultation', number: '٣', route: '/consultations', icon: 'support_agent',
    title: 'الاستشارات الشرعية والتربوية',
    description: 'قناة تواصل خاصة ومباشرة مع نخبة من العلماء والمستشارين التربويين الموثوقين. اطرح نازلتك أو تساؤلك الفردي تلقي ما يشفي قلبك ان شاء الله أو توجيهاً مدروساً بسرية كاملة.',
    badge: 'سرية تامة وتشفير', badgeIcon: 'verified_user',
    accent: 'bg-gradient-to-l from-secondary via-secondary-fixed-dim to-tertiary-fixed-dim',
    iconBackground: 'bg-secondary text-on-secondary',
    badgeBackground: 'bg-surface-container-high text-on-surface',
    buttonBackground: 'bg-primary-container hover:bg-primary text-on-primary',
    buttonLabel: 'طلب استشارة خاصة', buttonIcon: 'send',
    features: [
      {icon: 'timer', title: 'خلال ٢٤ ساعة', subtitle: 'متوسط زمن الرد المعتمد', color: 'gold'},
      {icon: 'lock', title: 'مشفر بالكامل', subtitle: 'أمان وخصوصية وقفية', color: 'green'},
    ],
  },
  {
    id: 'endowment', number: '٤', route: '/endowment', icon: 'volunteer_activism',
    title: 'الوقف ودعم المنصة',
    description: 'مساهمتك تضمن استمرار البوابات التعليمية والتقنية وإتاحتها مجاناً للمسلمين حول العالم، سهم وقفي وأجر جارٍ مستمر.',
    badge: 'صدقة جارية', badgeIcon: 'favorite',
    accent: 'bg-gradient-to-l from-secondary via-secondary-fixed-dim to-secondary-fixed',
    iconBackground: 'bg-secondary text-on-secondary',
    badgeBackground: 'bg-secondary-fixed/70 text-on-secondary-fixed',
    buttonBackground: 'bg-secondary hover:bg-secondary-fixed hover:text-on-secondary-fixed text-on-secondary',
    buttonLabel: 'المساهمة في الوقف ودعم المنصة', buttonIcon: 'arrow_left_alt',
    features: [
      {icon: 'all_inclusive', title: 'أسهم متجددة', subtitle: 'أثر علمي ممتد', color: 'gold'},
      {icon: 'credit_card', title: 'دفع آمن', subtitle: 'مدى، أبل باي وفيزا', color: 'green'},
    ],
  },
];
