"use client";

import { RefreshCw, Newspaper, Radio, AlertCircle } from "lucide-react";
import NewsCard from "./NewsCard";
import NewsFilters from "./NewsFilters";
import { useNews } from "./useNews";
import { useI18nStore } from "../lib/i18n/store";

export default function NewsFeed() {
  const { data, isLoading, refetch, error, isFetching } = useNews();
  const { t, locale } = useI18nStore();

  const hasNews = data?.news && data.news.length > 0;

  return (
    <div className="glass-premium p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Newspaper className="w-5 h-5 text-amber-400" />
            {isFetching && (
              <span className="absolute -top-1 -right-1 w-2 h-2 bg-emerald-400 rounded-full animate-ping" />
            )}
          </div>
          <div>
            <p className="text-xs text-textSecondary uppercase tracking-wider">
              {locale === "en" ? "Live News Feed" : "Canlı Haber Akışı"}
            </p>
            <h2 className="text-base font-semibold flex items-center gap-2">
              {locale === "en" ? "Market News & Events" : "Piyasa Haberleri"}
              {isFetching && (
                <span className="flex items-center gap-1 text-xs text-emerald-400 font-normal">
                  <Radio className="w-3 h-3 animate-pulse" />
                  {locale === "en" ? "Live" : "Canlı"}
                </span>
              )}
            </h2>
          </div>
        </div>
        <button
          onClick={() => refetch()}
          className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition"
          aria-label="Refresh news"
          disabled={isFetching}
        >
          <RefreshCw className={`w-4 h-4 ${isFetching ? "animate-spin text-amber-400" : ""}`} />
        </button>
      </div>

      <NewsFilters />

      {isLoading ? (
        <div className="space-y-3">
          <div className="skeleton h-24 w-full rounded-xl animate-pulse" />
          <div className="skeleton h-24 w-full rounded-xl animate-pulse" style={{ animationDelay: "0.1s" }} />
          <div className="skeleton h-24 w-full rounded-xl animate-pulse" style={{ animationDelay: "0.2s" }} />
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <AlertCircle className="w-10 h-10 text-danger/50 mb-3" />
          <p className="text-sm text-danger mb-2">
            {locale === "en" ? "Failed to load news" : "Haberler yüklenemedi"}
          </p>
          <button
            onClick={() => refetch()}
            className="text-xs text-amber-400 hover:underline"
          >
            {locale === "en" ? "Try again" : "Tekrar dene"}
          </button>
        </div>
      ) : !hasNews ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="relative mb-4">
            <Newspaper className="w-12 h-12 text-textSecondary/30" />
            <div className="absolute inset-0 animate-ping">
              <Newspaper className="w-12 h-12 text-amber-400/20" />
            </div>
          </div>
          <p className="text-sm text-textSecondary mb-1">
            {locale === "en" ? "No news available" : "Haber bulunamadı"}
          </p>
          <p className="text-xs text-textSecondary/70">
            {locale === "en" ? "News will appear here when available" : "Haberler mevcut olduğunda burada görünecek"}
          </p>
          <button
            onClick={() => refetch()}
            className="mt-4 px-4 py-2 text-xs bg-white/10 hover:bg-white/20 rounded-lg transition flex items-center gap-2"
          >
            <RefreshCw className="w-3 h-3" />
            {locale === "en" ? "Refresh" : "Yenile"}
          </button>
        </div>
      ) : (
        <div className="space-y-3 max-h-[720px] overflow-y-auto pr-2">
          {data.news.map((item, index) => (
            <div
              key={item.id}
              className="animate-fadeIn"
              style={{ animationDelay: `${index * 0.05}s` }}
            >
              <NewsCard news={item} />
            </div>
          ))}
        </div>
      )}

      {hasNews && (
        <div className="flex items-center justify-between text-xs text-textSecondary pt-2 border-t border-white/10">
          <span className="flex items-center gap-2">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
            {locale === "en" ? "Auto-refreshes every minute" : "Her dakika otomatik yenilenir"}
          </span>
          <span>{data.news.length} {locale === "en" ? "items" : "haber"}</span>
        </div>
      )}
    </div>
  );
}
