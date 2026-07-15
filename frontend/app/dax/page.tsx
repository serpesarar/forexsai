// Eski DAX paneli Neural tasarıma taşındı.
// Yedek: .backup/legacy_panels_20260715/app/dax/
import { redirect } from "next/navigation";

export default function DaxRedirect() {
  redirect("/neural/dax");
}
