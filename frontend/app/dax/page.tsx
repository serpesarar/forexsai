import { SYMBOL_CONFIGS } from "@/lib/symbolConfig";
import SymbolPage from "@/components/layout/SymbolPage";

export default function DaxPage() {
  return <SymbolPage config={SYMBOL_CONFIGS.dax} />;
}
