import { gateways } from '../config/gateways';
import GatewayCard from './GatewayCard';

export default function GatewayGrid() {
  return <section className="grid grid-cols-1 md:grid-cols-2 gap-gutter lg:gap-space-lg mb-space-xl items-stretch" id="gateways">
    {gateways.map(gateway => <GatewayCard key={gateway.id} gateway={gateway} />)}
  </section>;
}
