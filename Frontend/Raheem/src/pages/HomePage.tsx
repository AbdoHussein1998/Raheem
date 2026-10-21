import Hero from '../features/home/components/Hero';
import GatewayGrid from '../features/gateways/components/GatewayGrid';

export default function HomePage() {
  return (
    <main className="w-full pt-20 flex-grow">
      <div className="relative w-full overflow-hidden">
        <div className="absolute -top-32 right-1/4 w-[500px] h-[500px] bg-primary-fixed/35 rounded-full blur-3xl pointer-events-none -z-10" />
        <div className="absolute top-96 left-10 w-[420px] h-[420px] bg-secondary-container/40 rounded-full blur-3xl pointer-events-none -z-10" />
        <div className="max-w-7xl mx-auto px-margin-mobile lg:px-margin py-space-md lg:py-space-lg">
          <Hero />
          <GatewayGrid />
        </div>
      </div>
    </main>
  );
}
