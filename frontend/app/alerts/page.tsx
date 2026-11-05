"use client";

/**
 * Fiyat Alarmları — /api/alerts (backend price_alert_service; 60 sn'de bir taze MT5 fiyatıyla değerlendirilir,
 * tetikte Telegram). Yönetici oturumu gerekir.
 */

import { AlertTriangle, Bell, CheckCircle2, Clock, Loader2, Pause, Play, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import {
  type AlertKind,
  type PriceAlert,
  useAlerts,
  useCreateAlert,
  useDeleteAlert,
  useSetAlertStatus,
} from "@/lib/api/alerts";
import { cn } from "@/lib/utils";

const SYMBOLS = [
  { key: "NDX", label: "NASDAQ 100" },
  { key: "DAX", label: "DAX 40" },
  { key: "XAUUSD", label: "Altın" },
  { key: "USOIL", label: "Petrol" },
];
const KIND_LABELS: Record<AlertKind, string> = {
  above: "Üstüne çıkarsa",
  below: "Altına inerse",
  pct_move: "% hareket ederse",
  time: "Zamanı gelince",
  stop: "Stop seviyesi",
  target: "Hedef seviyesi",
};
const FORM_KINDS: AlertKind[] = ["above", "below", "pct_move", "time"];
type Filter = "all" | "active" | "triggered" | "disabled";
const FILTERS: { key: Filter; label: string }[] = [
  { key: "all", label: "Tümü" },
  { key: "active", label: "Aktif" },
  { key: "triggered", label: "Tetiklenen" },
  { key: "disabled", label: "Kapalı" },
];

function fmtTime(iso: string | null): string {
  return iso ? new Date(iso).toLocaleString("tr-TR", { dateStyle: "short", timeStyle: "short" }) : "—";
}

function describe(a: PriceAlert): string {
  if (a.kind === "time") return `${fmtTime(a.at_utc)}`;
  if (a.kind === "pct_move") return `%${a.pct} (ref ${a.ref_price})`;
  return `${a.price}${a.ref_price ? ` (kurulum ${a.ref_price})` : ""}`;
}

function CreateForm({ onDone }: { onDone: () => void }) {
  const create = useCreateAlert();
  const [symbol, setSymbol] = useState("NDX");
  const [kind, setKind] = useState<AlertKind>("above");
  const [value, setValue] = useState("");
  const [label, setLabel] = useState("");
  const [repeat, setRepeat] = useState(false);

  const submit = () => {
    const body: Parameters<typeof create.mutate>[0] = { symbol, kind, label: label || undefined, one_shot: !repeat };
    if (kind === "time") body.at_utc = value ? new Date(value).toISOString() : undefined;
    else if (kind === "pct_move") body.pct = Number(value);
    else body.price = Number(value);
    create.mutate(body, { onSuccess: onDone });
  };

  const input = "rounded-lg border border-gray-800 bg-gray-950 px-3 py-2 text-sm text-white outline-none focus:border-purple-500";
  return (
    <div className="mb-6 rounded-xl border border-purple-500/30 bg-purple-500/5 p-4">
      <div className="grid gap-3 sm:grid-cols-5">
        <select className={input} value={symbol} onChange={(e) => setSymbol(e.target.value)}>
          {SYMBOLS.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}
        </select>
        <select className={input} value={kind} onChange={(e) => { setKind(e.target.value as AlertKind); setValue(""); }}>
          {FORM_KINDS.map((k) => <option key={k} value={k}>{KIND_LABELS[k]}</option>)}
        </select>
        <input
          className={input}
          type={kind === "time" ? "datetime-local" : "number"}
          step="any"
          placeholder={kind === "pct_move" ? "% (ör. 0.5)" : "fiyat"}
          value={value}
          onChange={(e) => setValue(e.target.value)}
        />
        <input className={input} placeholder="not (isteğe bağlı)" value={label} onChange={(e) => setLabel(e.target.value)} />
        <button
          onClick={submit}
          disabled={!value || create.isPending}
          className="rounded-lg bg-purple-500 px-4 py-2 text-sm font-medium hover:bg-purple-600 disabled:opacity-50"
        >
          {create.isPending ? "Kaydediliyor…" : "Kaydet"}
        </button>
      </div>
      <label className="mt-3 flex items-center gap-2 text-xs text-gray-400">
        <input type="checkbox" checked={repeat} onChange={(e) => setRepeat(e.target.checked)} />
        Tekrarlı (en fazla saatte bir bildirir; kapalıysa bir kez tetiklenip kapanır)
      </label>
      {kind === "pct_move" && <p className="mt-2 text-xs text-gray-500">Referans: kayıt anındaki canlı fiyat.</p>}
      {create.error && <p className="mt-2 text-xs text-red-400">{(create.error as Error).message}</p>}
    </div>
  );
}

function AlertRow({ a }: { a: PriceAlert }) {
  const setStatus = useSetAlertStatus();
  const del = useDeleteAlert();
  return (
    <div
      className={cn(
        "flex items-center justify-between gap-3 rounded-xl border p-4",
        a.status === "active" && "border-gray-800 bg-gray-900/50",
        a.status === "triggered" && "border-yellow-500/30 bg-yellow-500/5",
        a.status === "disabled" && "border-gray-800 bg-gray-900/30 opacity-60",
      )}
    >
      <div className="flex min-w-0 items-center gap-4">
        <div className={cn(
          "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg",
          a.status === "active" ? "bg-green-500/10 text-green-400" : "bg-yellow-500/10 text-yellow-400",
        )}>
          {a.status === "triggered" ? <CheckCircle2 className="h-5 w-5" /> : <Bell className="h-5 w-5" />}
        </div>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-semibold">{a.symbol}</span>
            <span className="text-sm text-gray-400">{KIND_LABELS[a.kind]}</span>
            <span className="font-mono text-sm text-purple-400">{describe(a)}</span>
            {a.source !== "manual" && <span className="rounded-full bg-indigo-500/10 px-2 py-0.5 text-[10px] text-indigo-300">{a.source}</span>}
            {!a.one_shot && <span className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] text-gray-400">tekrarlı</span>}
          </div>
          {a.label && <p className="mt-0.5 truncate text-xs text-gray-400">{a.label}</p>}
          <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-gray-500">
            <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {fmtTime(a.created_at)}</span>
            {a.triggered_at && <span className="text-yellow-400">tetik {fmtTime(a.triggered_at)}{a.triggered_price ? ` @ ${a.triggered_price}` : ""}</span>}
          </div>
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {a.status !== "triggered" && (
          <button
            title={a.status === "active" ? "Durdur" : "Etkinleştir"}
            onClick={() => setStatus.mutate({ id: a.id, status: a.status === "active" ? "disabled" : "active" })}
            className="rounded-lg p-2 text-gray-400 hover:bg-gray-800 hover:text-white"
          >
            {a.status === "active" ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </button>
        )}
        <button
          title="Sil"
          onClick={() => del.mutate(a.id)}
          className="rounded-lg p-2 text-gray-400 hover:bg-red-500/10 hover:text-red-400"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

export default function AlertsPage() {
  const { data, isLoading, error } = useAlerts();
  const [filter, setFilter] = useState<Filter>("all");
  const [showForm, setShowForm] = useState(false);
  const alerts = data?.alerts ?? [];
  const shown = alerts.filter((a) => filter === "all" || a.status === filter);
  const last = data?.service.last_run;

  return (
    <div className="min-h-screen bg-[#0a0a0a] p-4 text-white sm:p-6">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="flex items-center gap-3 text-2xl font-bold">
              <Bell className="h-6 w-6 text-purple-400" /> Fiyat Alarmları
            </h1>
            <p className="mt-1 text-sm text-gray-500">
              Koşul gerçekleşince Telegram'a bildirim. Fiyat yalnız taze MT5 beslemesinden okunur.
            </p>
          </div>
          <button
            onClick={() => setShowForm((v) => !v)}
            className="flex items-center gap-2 rounded-lg bg-purple-500 px-4 py-2 hover:bg-purple-600"
          >
            <Plus className="h-4 w-4" /> Alarm kur
          </button>
        </div>

        {showForm && <CreateForm onDone={() => setShowForm(false)} />}

        <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[
            { label: "Aktif", value: alerts.filter((a) => a.status === "active").length, color: "text-green-400" },
            { label: "Tetiklenen", value: alerts.filter((a) => a.status === "triggered").length, color: "text-yellow-400" },
            { label: "Toplam", value: alerts.length, color: "text-white" },
            {
              label: "Son tarama",
              value: last?.at ? new Date(last.at).toLocaleTimeString("tr-TR", { timeStyle: "short" }) : "—",
              color: data?.service.enabled ? "text-purple-400" : "text-red-400",
            },
          ].map((s) => (
            <div key={s.label} className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
              <p className="text-sm text-gray-500">{s.label}</p>
              <p className={cn("mt-1 text-2xl font-bold", s.color)}>{s.value}</p>
            </div>
          ))}
        </div>
        {last?.error && <p className="-mt-6 mb-6 text-xs text-red-400">Son tur hatası: {last.error}</p>}

        <div className="mb-6 flex w-fit items-center gap-1 rounded-lg bg-gray-900 p-1">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={cn(
                "rounded-lg px-4 py-2 text-sm font-medium transition-all",
                filter === f.key ? "bg-gray-700 text-white" : "text-gray-400 hover:text-white",
              )}
            >
              {f.label}
            </button>
          ))}
        </div>

        {isLoading && (
          <div className="flex h-32 items-center justify-center text-gray-400">
            <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Yükleniyor…
          </div>
        )}
        {error && (
          <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
            <AlertTriangle className="h-4 w-4" /> {(error as Error).message} — alarmlar yönetici oturumu ister.
          </div>
        )}
        {!isLoading && !error && shown.length === 0 && (
          <div className="rounded-xl border border-dashed border-gray-800 p-10 text-center text-sm text-gray-500">
            Bu filtrede alarm yok. Zaman Makinesi panelinden bir planın stop/hedef alarmını tek tıkla kurabilirsin.
          </div>
        )}
        <div className="space-y-3">
          {shown.map((a) => <AlertRow key={a.id} a={a} />)}
        </div>
      </div>
    </div>
  );
}
