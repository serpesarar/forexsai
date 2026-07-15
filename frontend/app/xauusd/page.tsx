// Eski XAUUSD paneli Neural tasarıma taşındı.
// Yedek: .backup/legacy_panels_20260715/app/xauusd/
import { redirect } from "next/navigation";

export default function XauusdRedirect() {
  redirect("/neural/xauusd");
}
