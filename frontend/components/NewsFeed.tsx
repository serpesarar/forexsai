"use client";

import { RefreshCw } from "lucide-react";
import NewsCard from "./NewsCard";
import NewsFilters from "./NewsFilters";
import { useNews } from "./useNews";

export default function NewsFeed() {
  const { data, isLoading, refetch, error } = useNews();

  return (
    <div className="glass-card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-textSecondary">Fundamental News</p>
          <h2 className="text-lg font-semibold">📰 News & Events</h2>
        </div>
        <button
          onClick={() => refetch()}
          className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition"
          aria-label="Refresh news"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <NewsFilters />

      {isLoading ? (
        <div className="space-y-3">
          <div className="skeleton h-24 w-full" />
          <div className="skeleton h-24 w-full" />
          <div className="skeleton h-24 w-full" />
        </div>
      ) : error ? (
        <div className="text-sm text-danger">News feed could not be loaded.</div>
      ) : (
        <div className="space-y-4 max-h-[720px] overflow-y-auto pr-2">
          {data?.news.map((item) => (
            <NewsCard key={item.id} news={item} />
          ))}
        </div>
      )}

      <button className="w-full text-xs text-textSecondary py-2 border border-white/10 rounded-lg hover:bg-white/5 transition">
        Load More News
      </button>
    </div>
  );
}
