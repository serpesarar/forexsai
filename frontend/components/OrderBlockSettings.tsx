"use client";

import { useEffect, useState } from "react";

export type OrderBlockSettingsValue = {
  fractalPeriod: number;
  minDisplacementAtr: number;
  minScore: number;
  zoneType: "wick" | "body";
  maxTests: number;
};

const STORAGE_KEY = "order-block-settings";

const defaultSettings: OrderBlockSettingsValue = {
  fractalPeriod: 2,
  minDisplacementAtr: 1.0,
  minScore: 50,
  zoneType: "wick",
  maxTests: 2
};

type Props = {
  value: OrderBlockSettingsValue;
  onChange: (value: OrderBlockSettingsValue) => void;
};

export default function OrderBlockSettings({ value, onChange }: Props) {
  const [local, setLocal] = useState(value);

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved) as OrderBlockSettingsValue;
      setLocal(parsed);
      onChange(parsed);
    }
  }, [onChange]);

  const update = (patch: Partial<OrderBlockSettingsValue>) => {
    const next = { ...local, ...patch };
    setLocal(next);
    onChange(next);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  };

  return (
    <div className="space-y-4 text-sm">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <label className="space-y-2">
          <span className="text-textSecondary text-xs">Fractal Period</span>
          <input
            type="number"
            value={local.fractalPeriod}
            onChange={(event) => update({ fractalPeriod: Number(event.target.value) })}
            className="bg-white/5 rounded-lg px-3 py-2 w-full text-sm"
          />
        </label>
        <label className="space-y-2">
          <span className="text-textSecondary text-xs">Min Disp (ATR)</span>
          <input
            type="number"
            step={0.1}
            value={local.minDisplacementAtr}
            onChange={(event) => update({ minDisplacementAtr: Number(event.target.value) })}
            className="bg-white/5 rounded-lg px-3 py-2 w-full text-sm"
          />
        </label>
        <label className="space-y-2">
          <span className="text-textSecondary text-xs">Min Score</span>
          <input
            type="number"
            value={local.minScore}
            onChange={(event) => update({ minScore: Number(event.target.value) })}
            className="bg-white/5 rounded-lg px-3 py-2 w-full text-sm"
          />
        </label>
        <label className="space-y-2">
          <span className="text-textSecondary text-xs">Max Tests</span>
          <input
            type="number"
            value={local.maxTests}
            onChange={(event) => update({ maxTests: Number(event.target.value) })}
            className="bg-white/5 rounded-lg px-3 py-2 w-full text-sm"
          />
        </label>
      </div>
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="text-textSecondary text-xs">Zone Type:</span>
          <button
            className={`px-4 py-2 rounded-lg text-sm ${local.zoneType === "wick" ? "bg-white text-background font-medium" : "bg-white/10"}`}
            onClick={() => update({ zoneType: "wick" })}
          >
            Wick
          </button>
          <button
            className={`px-4 py-2 rounded-lg text-sm ${local.zoneType === "body" ? "bg-white text-background font-medium" : "bg-white/10"}`}
            onClick={() => update({ zoneType: "body" })}
          >
            Body
          </button>
        </div>
        <button
          className="px-4 py-2 rounded-lg bg-white/10 text-sm hover:bg-white/20 transition"
          onClick={() => update(defaultSettings)}
        >
          Reset to Default
        </button>
      </div>
    </div>
  );
}

export { defaultSettings };
