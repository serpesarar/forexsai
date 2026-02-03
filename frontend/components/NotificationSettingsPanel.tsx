"use client";

import { useState, useEffect } from "react";
import { Bell, Send, Check, X, Settings, MessageCircle } from "lucide-react";

interface NotificationSettings {
  telegram_chat_id: string | null;
  telegram_enabled: boolean;
  notify_ultra_safe: boolean;
  notify_balanced: boolean;
  notify_full_power: boolean;
  notify_aggressive: boolean;
  notify_new_signal: boolean;
  notify_tp1: boolean;
  notify_tp2: boolean;
  notify_tp3: boolean;
  notify_sl: boolean;
  min_confidence: number;
  symbols: string[];
}

const DEFAULT_SETTINGS: NotificationSettings = {
  telegram_chat_id: null,
  telegram_enabled: false,
  notify_ultra_safe: true,
  notify_balanced: true,
  notify_full_power: false,
  notify_aggressive: false,
  notify_new_signal: true,
  notify_tp1: true,
  notify_tp2: true,
  notify_tp3: false,
  notify_sl: true,
  min_confidence: 0.6,
  symbols: ["XAUUSD", "NDX.INDX"],
};

export default function NotificationSettingsPanel() {
  const [settings, setSettings] = useState<NotificationSettings>(DEFAULT_SETTINGS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const res = await fetch("/api/learning/notifications/settings");
      const data = await res.json();
      if (!data.error) {
        setSettings({ ...DEFAULT_SETTINGS, ...data });
      }
    } catch (e) {
      console.error("Failed to fetch settings:", e);
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      const params = new URLSearchParams();
      Object.entries(settings).forEach(([key, value]) => {
        if (Array.isArray(value)) {
          value.forEach((v) => params.append(key, v));
        } else if (value !== null) {
          params.append(key, String(value));
        }
      });

      const res = await fetch(`/api/learning/notifications/settings?${params}`, {
        method: "PUT",
      });
      const data = await res.json();
      if (data.success) {
        setTestResult({ ok: true, message: "Settings saved!" });
        setTimeout(() => setTestResult(null), 3000);
      }
    } catch (e) {
      console.error("Failed to save settings:", e);
      setTestResult({ ok: false, message: "Failed to save" });
    } finally {
      setSaving(false);
    }
  };

  const testTelegram = async () => {
    if (!settings.telegram_chat_id) {
      setTestResult({ ok: false, message: "Please enter Chat ID first" });
      return;
    }
    setTesting(true);
    try {
      const res = await fetch(
        `/api/learning/notifications/test?chat_id=${settings.telegram_chat_id}`,
        { method: "POST" }
      );
      const data = await res.json();
      setTestResult({
        ok: data.ok,
        message: data.ok ? "Test message sent!" : data.error || "Failed",
      });
    } catch (e) {
      setTestResult({ ok: false, message: "Connection failed" });
    } finally {
      setTesting(false);
      setTimeout(() => setTestResult(null), 5000);
    }
  };

  const toggleSymbol = (symbol: string) => {
    setSettings((prev) => ({
      ...prev,
      symbols: prev.symbols.includes(symbol)
        ? prev.symbols.filter((s) => s !== symbol)
        : [...prev.symbols, symbol],
    }));
  };

  if (loading) {
    return (
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 animate-pulse">
        <div className="h-6 bg-gray-800 rounded w-1/3 mb-4" />
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 bg-gray-800 rounded" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
      <div className="flex items-center gap-2 mb-6">
        <Bell className="w-5 h-5 text-yellow-400" />
        <h2 className="text-lg font-semibold text-white">Notification Settings</h2>
      </div>

      {/* Telegram Connection */}
      <div className="mb-6 p-4 bg-gray-800 rounded-lg">
        <div className="flex items-center gap-2 mb-3">
          <MessageCircle className="w-4 h-4 text-blue-400" />
          <span className="text-white font-medium">Telegram Connection</span>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Chat ID (e.g., -100123456789)"
            value={settings.telegram_chat_id || ""}
            onChange={(e) => setSettings({ ...settings, telegram_chat_id: e.target.value })}
            className="flex-1 bg-gray-700 text-white px-3 py-2 rounded-lg border border-gray-600 text-sm"
          />
          <button
            onClick={testTelegram}
            disabled={testing}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm disabled:opacity-50"
          >
            {testing ? "Testing..." : "Test"}
          </button>
        </div>
        <label className="flex items-center gap-2 mt-3 cursor-pointer">
          <input
            type="checkbox"
            checked={settings.telegram_enabled}
            onChange={(e) => setSettings({ ...settings, telegram_enabled: e.target.checked })}
            className="w-4 h-4 rounded"
          />
          <span className="text-gray-300 text-sm">Enable Telegram notifications</span>
        </label>
      </div>

      {/* Strategy Filters */}
      <div className="mb-6">
        <h3 className="text-white font-medium mb-3">Strategy Filters</h3>
        <div className="grid grid-cols-2 gap-2">
          {[
            { key: "notify_ultra_safe", label: "Ultra Safe", desc: "Safest signals" },
            { key: "notify_balanced", label: "Balanced", desc: "Recommended" },
            { key: "notify_full_power", label: "Full Power", desc: "More aggressive" },
            { key: "notify_aggressive", label: "Aggressive", desc: "High risk" },
          ].map(({ key, label, desc }) => (
            <label
              key={key}
              className="flex items-center gap-2 p-3 bg-gray-800 rounded-lg cursor-pointer hover:bg-gray-750"
            >
              <input
                type="checkbox"
                checked={settings[key as keyof NotificationSettings] as boolean}
                onChange={(e) => setSettings({ ...settings, [key]: e.target.checked })}
                className="w-4 h-4 rounded"
              />
              <div>
                <span className="text-white text-sm">{label}</span>
                <p className="text-gray-500 text-xs">{desc}</p>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Min Confidence Slider */}
      <div className="mb-6">
        <div className="flex justify-between mb-2">
          <span className="text-white font-medium">Minimum Confidence</span>
          <span className="text-blue-400">{Math.round(settings.min_confidence * 100)}%</span>
        </div>
        <input
          type="range"
          min="40"
          max="80"
          value={settings.min_confidence * 100}
          onChange={(e) => setSettings({ ...settings, min_confidence: Number(e.target.value) / 100 })}
          className="w-full"
        />
        <p className="text-gray-500 text-xs mt-1">
          Signals below this confidence will not trigger notifications
        </p>
      </div>

      {/* Symbols */}
      <div className="mb-6">
        <h3 className="text-white font-medium mb-3">Symbols</h3>
        <div className="flex gap-2">
          {["XAUUSD", "NDX.INDX"].map((symbol) => (
            <button
              key={symbol}
              onClick={() => toggleSymbol(symbol)}
              className={`px-4 py-2 rounded-lg text-sm ${
                settings.symbols.includes(symbol)
                  ? "bg-blue-600 text-white"
                  : "bg-gray-800 text-gray-400"
              }`}
            >
              {symbol === "XAUUSD" ? "🥇 XAUUSD" : "📈 NASDAQ"}
            </button>
          ))}
        </div>
      </div>

      {/* Target Notifications */}
      <div className="mb-6">
        <h3 className="text-white font-medium mb-3">Target Notifications</h3>
        <div className="flex flex-wrap gap-2">
          {[
            { key: "notify_new_signal", label: "New Signal" },
            { key: "notify_tp1", label: "TP1 Hit" },
            { key: "notify_tp2", label: "TP2 Hit" },
            { key: "notify_tp3", label: "TP3 Hit" },
            { key: "notify_sl", label: "Stop Loss" },
          ].map(({ key, label }) => (
            <label
              key={key}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer ${
                settings[key as keyof NotificationSettings]
                  ? key === "notify_sl"
                    ? "bg-red-600/20 border border-red-600"
                    : "bg-green-600/20 border border-green-600"
                  : "bg-gray-800 border border-gray-700"
              }`}
            >
              <input
                type="checkbox"
                checked={settings[key as keyof NotificationSettings] as boolean}
                onChange={(e) => setSettings({ ...settings, [key]: e.target.checked })}
                className="hidden"
              />
              <span className={`text-sm ${settings[key as keyof NotificationSettings] ? "text-white" : "text-gray-400"}`}>
                {label}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Result Message */}
      {testResult && (
        <div
          className={`mb-4 p-3 rounded-lg flex items-center gap-2 ${
            testResult.ok ? "bg-green-600/20 text-green-400" : "bg-red-600/20 text-red-400"
          }`}
        >
          {testResult.ok ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />}
          <span>{testResult.message}</span>
        </div>
      )}

      {/* Save Button */}
      <button
        onClick={saveSettings}
        disabled={saving}
        className="w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg font-medium disabled:opacity-50"
      >
        {saving ? "Saving..." : "Save Settings"}
      </button>
    </div>
  );
}
