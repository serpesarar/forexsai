"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { ArrowLeft } from "lucide-react";

import ProbabilityEnginePanel from "@/components/nom/ProbabilityEnginePanel";

function Inner() {
  const asof = useSearchParams().get("asof");
  return (
    <main className="min-h-screen bg-slate-950 px-4 py-6 text-slate-100 sm:px-8">
      <div className="mx-auto max-w-7xl space-y-4">
        <Link href="/" className="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-white">
          <ArrowLeft className="h-4 w-4" /> Ana sayfa
        </Link>
        <h1 className="text-xl font-semibold">NASDAQ Olasılık Motoru</h1>
        <p className="max-w-3xl text-sm text-slate-400">
          Şu an açılacak varsayımsal bir LONG ve SHORT işlem için fiyatın önce hedefe mi yoksa stopa mı gideceğinin
          <b className="text-slate-200"> kalibre edilmiş olasılığı</b>. Bariyerler ATR katı, giriş gerçek spread ve kaymayla;
          olasılıklar 2021-2026 NDX 1m verisinde walk-forward ile sınandı. Karar destek aracıdır, işlem açmaz.
        </p>
        <ProbabilityEnginePanel asof={asof} />
      </div>
    </main>
  );
}

export default function ProbabilityEnginePage() {
  return (
    <Suspense fallback={null}>
      <Inner />
    </Suspense>
  );
}
