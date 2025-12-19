"use client";

import { useState } from "react";
import { Download } from "lucide-react";
import { usePatternEngine } from "../lib/api";

export default function PatternEnginePanel() {
  const [topPercent, setTopPercent] = useState(0.3);
  const [minSuccess, setMinSuccess] = useState(0.65);
  const [search, setSearch] = useState("");

  const { data, isLoading, error } = usePatternEngine({
    last_n: 500,
    select_top: topPercent,
    output_selected_only: true
  });

  const rows = (data?.patterns ?? []).filter((pattern: any) => {
    const matchSearch = pattern.pattern_id.toLowerCase().includes(search.toLowerCase());
    return matchSearch && pattern.p_success >= minSuccess;
  });

  return (
    <div className="glass-card p-6 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm text-textSecondary">Pattern Engine - Top Candidates</p>
          <h3 className="text-lg font-semibold">Top 30% Filter</h3>
        </div>
        <button className="flex items-center gap-2 text-sm px-3 py-2 rounded-full bg-white/10 hover:bg-white/20 transition">
          <Download className="w-4 h-4" /> Export CSV
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <label className="space-y-2">
          <span className="text-textSecondary">Top %</span>
          <input
            type="range"
            min={0.1}
            max={0.5}
            step={0.1}
            value={topPercent}
            onChange={(event) => setTopPercent(Number(event.target.value))}
            className="w-full"
          />
          <div className="text-xs">{Math.round(topPercent * 100)}%</div>
        </label>
        <label className="space-y-2">
          <span className="text-textSecondary">Min p_success</span>
          <input
            type="number"
            value={minSuccess}
            min={0.5}
            max={1}
            step={0.05}
            onChange={(event) => setMinSuccess(Number(event.target.value))}
            className="bg-white/5 rounded-lg px-3 py-2 w-full"
          />
        </label>
        <label className="space-y-2">
          <span className="text-textSecondary">Search</span>
          <input
            type="text"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="pattern_id"
            className="bg-white/5 rounded-lg px-3 py-2 w-full"
          />
        </label>
      </div>
      {isLoading ? (
        <div className="space-y-3">
          <div className="skeleton h-6 w-full" />
          <div className="skeleton h-6 w-full" />
          <div className="skeleton h-6 w-full" />
        </div>
      ) : error ? (
        <div className="text-sm text-danger">Pattern Engine verisi alınamadı.</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="text-textSecondary">
              <tr>
                <th className="text-left py-2">Timestamp</th>
                <th className="text-left py-2">Pattern</th>
                <th className="text-left py-2">Route</th>
                <th className="text-left py-2">p_success</th>
                <th className="text-left py-2">Trade OK</th>
                <th className="text-left py-2">Stage</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row: any) => (
                <tr key={row.timestamp} className="border-t border-white/10">
                  <td className="py-2 pr-2 whitespace-nowrap">{row.timestamp}</td>
                  <td className="py-2 pr-2">{row.pattern_id}</td>
                  <td className="py-2 pr-2">{row.route}</td>
                  <td className="py-2 pr-2">{row.p_success}</td>
                  <td className={`py-2 pr-2 ${row.trade_ok ? "text-success" : "text-danger"}`}>
                    {row.trade_ok ? "true" : "false"}
                  </td>
                  <td className="py-2">{row.stage}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {data?.model_status && (
        <p className="text-xs text-warning">{data.model_status}</p>
      )}
    </div>
  );
}
