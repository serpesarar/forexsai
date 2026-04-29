import { notFound } from "next/navigation";
import { SYMBOL_CONFIGS, getSymbolBySlug, type SymbolSlug } from "../../../lib/symbolConfig";
import SymbolPage from "../../../components/layout/SymbolPage";

export function generateStaticParams() {
  return (Object.keys(SYMBOL_CONFIGS) as SymbolSlug[]).map((symbol) => ({ symbol }));
}

export default function DashboardSymbolRoute({ params }: { params: { symbol: string } }) {
  const config = getSymbolBySlug(params.symbol);
  if (!config) notFound();
  return <SymbolPage config={config} />;
}
