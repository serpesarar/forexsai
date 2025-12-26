"use client";

import clsx from "clsx";

interface NewsItem {
  type: "economic_event" | "market_news";
  id: string;
  timestamp: string;
  title: string;
  impact?: string | null;
  sentiment?: string | null;
  actual?: string | null;
  expected?: string | null;
  previous?: string | null;
  market_reaction?: string | null;
  content?: string | null;
  link?: string | null;
}

function formatTime(value: string) {
  const date = new Date(value);
  return date.toLocaleString([], { hour: "2-digit", minute: "2-digit", month: "short", day: "numeric" });
}

const impactStyles: Record<string, string> = {
  High: "bg-red-500/20 text-red-200 border-red-500/40",
  Medium: "bg-yellow-500/20 text-yellow-200 border-yellow-500/40",
  Low: "bg-green-500/20 text-green-200 border-green-500/40",
};

const sentimentIcon: Record<string, string> = {
  bullish: "📈",
  bearish: "📉",
  neutral: "↔️",
};

export default function NewsCard({ news }: { news: NewsItem }) {
  const impactLabel = news.impact ?? "Medium";
  const sentiment = news.sentiment ?? "neutral";

  return (
    <article className="border border-white/10 rounded-xl p-4 bg-white/5 space-y-3">
      <div className="flex items-center justify-between gap-2 text-xs text-textSecondary">
        <span
          className={clsx(
            "px-2 py-1 rounded-full border text-[10px] font-semibold uppercase",
            impactStyles[impactLabel] ?? "bg-white/10 text-white/80 border-white/10"
          )}
        >
          {impactLabel} IMPACT
        </span>
        <span>{formatTime(news.timestamp)}</span>
      </div>
      <h3 className="text-sm font-semibold text-white">{news.title}</h3>
      {news.type === "economic_event" && (
        <div className="grid grid-cols-3 gap-2 text-xs text-textSecondary">
          <div>
            <p className="uppercase text-[10px]">Actual</p>
            <p className="text-white">{news.actual ?? "--"}</p>
          </div>
          <div>
            <p className="uppercase text-[10px]">Expected</p>
            <p className="text-white">{news.expected ?? "--"}</p>
          </div>
          <div>
            <p className="uppercase text-[10px]">Previous</p>
            <p className="text-white">{news.previous ?? "--"}</p>
          </div>
        </div>
      )}
      {news.content && <p className="text-xs text-textSecondary">{news.content}</p>}
      <div className="flex items-center justify-between text-xs">
        <span className="text-textSecondary">
          Impact: {sentiment.toUpperCase()} {sentimentIcon[sentiment] ?? ""}
        </span>
        {news.link && (
          <a href={news.link} target="_blank" rel="noreferrer" className="text-warning">
            Read More →
          </a>
        )}
      </div>
      {news.market_reaction && <p className="text-[11px] text-textSecondary">{news.market_reaction}</p>}
    </article>
  );
}
