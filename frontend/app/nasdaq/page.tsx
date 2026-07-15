// Eski NASDAQ paneli Neural tasarıma taşındı.
// Yedek: .backup/legacy_panels_20260715/app/nasdaq/
import { redirect } from "next/navigation";

export default function NasdaqRedirect() {
  redirect("/neural/ndx");
}
