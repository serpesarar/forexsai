"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import NewsFeedPanel from "@/components/NewsFeedPanel";

export default function NewsFeedPage() {
  return (
    <main className="min-h-screen bg-slate-950 px-4 py-6 text-slate-100 sm:px-8">
      <div className="mx-auto max-w-7xl space-y-4">
        <Link href="/" className="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-slate-200">
          <ArrowLeft className="h-4 w-4" /> Ana sayfa
        </Link>
        <div>
          <h1 className="text-xl font-semibold">Haber Akışı</h1>
          <p className="max-w-3xl text-sm text-slate-400">
            Birden çok kaynak aynı anda izlenir. Bir haberi ilk getiren kazanır, diğerleri teyit olarak eklenir.
          </p>
        </div>
        <NewsFeedPanel />
      </div>
    </main>
  );
}
