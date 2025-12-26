"use client";

import { useQuery } from "@tanstack/react-query";
import { fetcher } from "../lib/api";
import { useNewsStore } from "../lib/store";

export interface NewsItem {
  type: "economic_event" | "market_news";
  id: string;
  timestamp: string;
  title: string;
  impact?: string;
  sentiment?: string;
  actual?: string;
  expected?: string;
  previous?: string;
  market_reaction?: string;
  content?: string;
  link?: string;
  category?: string;
}

export interface NewsFeedResponse {
  total: number;
  news: NewsItem[];
}

export function useNews() {
  const { impactFilter, categoryFilter } = useNewsStore();
  const impact = impactFilter === "all" ? "" : `impact=${impactFilter}`;
  const category = categoryFilter === "all" ? "" : `category=${categoryFilter}`;
  const query = [impact, category].filter(Boolean).join("&");
  const endpoint = `/api/news/feed${query ? `?${query}` : ""}`;

  return useQuery({
    queryKey: ["news-feed", impactFilter, categoryFilter],
    queryFn: () => fetcher<NewsFeedResponse>(endpoint),
    refetchInterval: 60000,
    refetchIntervalInBackground: true
  });
}
