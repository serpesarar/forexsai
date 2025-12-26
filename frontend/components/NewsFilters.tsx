"use client";

import { useNewsStore } from "../lib/store";

const impactOptions = [
  { label: "All", value: "all" },
  { label: "High Impact", value: "high" },
  { label: "Medium Impact", value: "medium" },
  { label: "Low Impact", value: "low" },
] as const;

const categoryOptions = [
  { label: "All", value: "all" },
  { label: "Fed", value: "fed" },
  { label: "Inflation", value: "inflation" },
  { label: "Jobs", value: "jobs" },
] as const;

export default function NewsFilters() {
  const { impactFilter, categoryFilter, setImpactFilter, setCategoryFilter } = useNewsStore();

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {impactOptions.map((option) => (
          <button
            key={option.value}
            onClick={() => setImpactFilter(option.value)}
            className={`px-3 py-1 rounded-full text-xs font-semibold transition ${
              impactFilter === option.value ? "bg-white text-background" : "bg-white/10 text-white"
            }`}
            aria-pressed={impactFilter === option.value}
          >
            {option.label}
          </button>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        {categoryOptions.map((option) => (
          <button
            key={option.value}
            onClick={() => setCategoryFilter(option.value)}
            className={`px-3 py-1 rounded-full text-xs font-semibold transition ${
              categoryFilter === option.value ? "bg-white text-background" : "bg-white/10 text-white"
            }`}
            aria-pressed={categoryFilter === option.value}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}
