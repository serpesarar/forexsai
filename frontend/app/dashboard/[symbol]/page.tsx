// Eski sembol dashboard'u Neural tasarıma taşındı.
// Yedek: .backup/legacy_panels_20260715/app/dashboard/
import { redirect } from "next/navigation";

const SLUG_MAP: Record<string, string> = {
  nasdaq: "ndx",
  ndx: "ndx",
  dax: "dax",
  xauusd: "xauusd",
  gold: "xauusd",
  oil: "usoil",
  usoil: "usoil",
};

export default function DashboardSymbolRedirect({ params }: { params: { symbol: string } }) {
  redirect(`/neural/${SLUG_MAP[params.symbol.toLowerCase()] ?? "ndx"}`);
}
