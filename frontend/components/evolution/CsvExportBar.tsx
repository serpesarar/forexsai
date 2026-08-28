"use client";

/**
 * CSV İndir — tarih aralığı seç, bot işlemlerini (giriş/çıkış/TP-SL/net $/R/
 * hangi kurala göre açıldığı) tek dosyada indir.
 *
 * Gerçek bir `<a download>` linkidir — tarayıcı native indirmeyi yönetir,
 * blob/fetch juggling gerekmez (uç auth istemiyor, panelin geri kalanıyla
 * aynı erişim seviyesinde). `symbol` verilmezse tüm semboller indirilir.
 */

import { useState } from "react";
import { Download } from "lucide-react";

import { botTradesExportUrl } from "@/lib/api/evolution";
import { cx } from "./ui";

function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function daysAgo(n: number): string {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - n);
  return isoDate(d);
}

export default function CsvExportBar({
  symbol, compact = false,
}: {
  /** Belirli bir sembole daralt; boş bırakılırsa tüm semboller indirilir. */
  symbol?: string | null;
  compact?: boolean;
}) {
  const [start, setStart] = useState(() => daysAgo(30));
  const [end, setEnd] = useState(() => isoDate(new Date()));
  const invalid = start > end;

  return (
    <div
      className={cx(
        "flex flex-wrap items-center gap-1.5 rounded-xl border border-white/[0.07] bg-white/[0.02] px-2.5 py-1.5",
        compact && "text-[11px]",
      )}
    >
      <span className="text-[10.5px] text-slate-500">
        {symbol ? `${symbol} · CSV` : "Tüm işlemler · CSV"}
      </span>
      <input
        type="date"
        value={start}
        max={end}
        onChange={(e) => setStart(e.target.value)}
        className="rounded-lg border border-white/10 bg-white/[0.03] px-1.5 py-0.5 text-[10.5px] text-slate-300 [color-scheme:dark]"
        aria-label="başlangıç tarihi"
      />
      <span className="text-slate-600">–</span>
      <input
        type="date"
        value={end}
        min={start}
        max={isoDate(new Date())}
        onChange={(e) => setEnd(e.target.value)}
        className="rounded-lg border border-white/10 bg-white/[0.03] px-1.5 py-0.5 text-[10.5px] text-slate-300 [color-scheme:dark]"
        aria-label="bitiş tarihi"
      />
      <a
        href={invalid ? undefined : botTradesExportUrl({ symbol, start, end })}
        aria-disabled={invalid}
        title={
          invalid
            ? "Başlangıç tarihi bitişten sonra olamaz"
            : "Giriş/çıkış/TP-SL/net $/R + hangi kurala göre açıldığı bilgisiyle CSV indir"
        }
        className={cx(
          "flex items-center gap-1 rounded-full px-2.5 py-1 text-[10.5px] font-medium transition",
          invalid
            ? "cursor-not-allowed bg-white/[0.03] text-slate-600"
            : "bg-orange-500/15 text-orange-200 ring-1 ring-orange-400/25 hover:bg-orange-500/25",
        )}
      >
        <Download size={11} /> CSV indir
      </a>
    </div>
  );
}
