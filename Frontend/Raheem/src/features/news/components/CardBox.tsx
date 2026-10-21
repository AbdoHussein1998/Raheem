interface NewsCardProps {
  id: string;
  category: string;
  title: string;
  description: string;
  audience: string;
  publishedAt: string;
  detailsUrl: string;
}

export default function NewsCard(props: NewsCardProps) {
  return (
    <article
      className="group flex flex-col justify-between bg-surface-container-lowest rounded-xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300"
      data-category="programs"
      data-page-id={props.id}
    >
      {/* Card Content */}
      <div className="p-space-md">
        {/* Category and ID */}
        <div className="flex items-center justify-between mb-space-xs">
          <span className="px-2.5 py-0.5 rounded-full bg-secondary-container/40 text-on-secondary-fixed-variant font-label-sm text-label-sm font-semibold">
            {props.category}
          </span>

          <span className="font-mono text-xs text-outline">
            ID: #{props.id}
          </span>
        </div>

        {/* Title */}
        <a
          className="block group-hover:text-secondary transition-colors"
          data-page-id={props.id}
          href={props.detailsUrl}
        >
          <h3 className="font-headline-sm text-headline-sm text-primary font-bold mb-space-xs leading-snug">
            {props.title}
          </h3>
        </a>

        {/* Description */}
        <p className="font-body-sm text-body-sm text-on-surface-variant line-clamp-3 leading-relaxed mb-space-sm">
          {props.description}
        </p>

        {/* Audience Information */}
        <div className="flex items-center gap-3 p-2 bg-surface-container-low rounded-lg mt-2">
          <span className="material-symbols-outlined text-primary text-[20px]">
            groups
          </span>

          <span className="font-label-sm text-label-sm text-on-surface-variant">
            {props.audience}
          </span>
        </div>
      </div>

      {/* Card Footer */}
      <div className="p-space-md pt-0">
        <div className="pt-space-sm border-t border-surface-container flex items-center justify-between gap-3">
          <span className="font-label-sm text-label-sm text-outline shrink-0">
            {props.publishedAt}
          </span>

          <a
            className="inline-flex items-center gap-1 text-primary hover:text-secondary font-label-md text-label-md font-semibold transition-colors"
            data-page-id={props.id}
            href={props.detailsUrl}
          >
            <span>فتح صفحة الفعالية </span>

            <span className="material-symbols-outlined text-[16px]">
              arrow_back
            </span>
          </a>
        </div>
      </div>
    </article>
  );
}
