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
    <div className="space-y-3 text-sm">
      <div className="grid grid-cols-2 gap-3">
        <label className="space-y-1">
          <span className="text-textSecondary">Fractal Period</span>
          <input
            type="number"
            value={local.fractalPeriod}
            onChange={(event) => update({ fractalPeriod: Number(event.target.value) })}
            className="bg-white/5 rounded-lg px-3 py-2 w-full"
          />
        </label>
        <label className="space-y-1">
          <span className="text-textSecondary">Min Displacement (ATR)</span>
          <input
            type="number"
            step={0.1}
            value={local.minDisplacementAtr}
            onChange={(event) => update({ minDisplacementAtr: Number(event.target.value) })}
            className="bg-white/5 rounded-lg px-3 py-2 w-full"
          />
        </label>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <label className="space-y-1">
          <span className="text-textSecondary">Min Score</span>
          <input
            type="number"
            value={local.minScore}
            onChange={(event) => update({ minScore: Number(event.target.value) })}
            className="bg-white/5 rounded-lg px-3 py-2 w-full"
          />
        </label>
        <label className="space-y-1">
          <span className="text-textSecondary">Max Tests</span>
          <input
            type="number"
            value={local.maxTests}
            onChange={(event) => update({ maxTests: Number(event.target.value) })}
            className="bg-white/5 rounded-lg px-3 py-2 w-full"
          />
        </label>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-textSecondary">Zone Type</span>
        <button
          className={`px-3 py-1 rounded-full ${local.zoneType === "wick" ? "bg-white text-background" : "bg-white/10"}`}
          onClick={() => update({ zoneType: "wick" })}
        >
          Wick
        </button>
        <button
          className={`px-3 py-1 rounded-full ${local.zoneType === "body" ? "bg-white text-background" : "bg-white/10"}`}
          onClick={() => update({ zoneType: "body" })}
        >
          Body
        </button>
      </div>
      <div className="flex gap-2">
        <button
          className="px-3 py-2 rounded-full bg-white/10"
          onClick={() => update(defaultSettings)}
        >
          Reset to Default
        </button>
      </div>
    </div>
  );
}

export { defaultSettings };
