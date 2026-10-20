"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { ArrowLeft } from "lucide-react";

import CandleSimilarityPanel from "@/components/CandleSimilarityPanel";

function Inner() {
  const sp = useSearchParams();
  const symbol = (sp.get("symbol") ?? "NDX").toUpperCase();
  return (
    <main className="min-h-screen bg-slate-950 px-4 py-6 text-slate-100 sm:px-8">
      <div className="mx-auto max-w-7xl space-y-4">
        <Link href="/" className="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-white">
          <ArrowLeft className="h-4 w-4" /> Ana sayfa
        </Link>
        <p className="max-w-3xl text-sm text-slate-400">
          Son N mum, geçmişteki tüm N mumluk pencerelerle <b className="text-slate-200">grafikte göründüğü gibi</b> karşılaştırılır:
          her pencere kendi en düşük–en yüksek aralığına sığdırılır, her mumun gövde ve fitil konumu tek tek eşlenir.
          Fiyat düzeyi ve hareketin büyüklüğü fark etmez; yalnız şekil önemlidir.
        </p>
        <CandleSimilarityPanel initialSymbol={symbol} />
      </div>
    </main>
  );
}

export default function CandleSimilarityPage() {
  return (
    <Suspense fallback={null}>
      <Inner />
    </Suspense>
  );
}
