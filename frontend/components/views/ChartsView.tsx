"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Maximize2,
  Minimize2,
  LogIn,
  User,
  ExternalLink
} from "lucide-react";
import { ChartsIcon, LoadingIcon, SignalsIcon, DashboardIcon } from "../ui/CustomIcons";
import { useI18nStore } from "../../lib/i18n/store";
import { NeonChart } from "../../components/NeonChart";

type ChartSymbol = {
  id: string;
  label: string;
  tradingViewSymbol: string;
  description: string;
};

const CHART_SYMBOLS: ChartSymbol[] = [
  {
    id: "nasdaq",
    label: "NASDAQ-100",
    tradingViewSymbol: "PEPPERSTONE:NAS100",
    description: "NASDAQ-100 Endeksi"
  },
  {
    id: "xauusd",
    label: "XAUUSD",
    tradingViewSymbol: "PEPPERSTONE:XAUUSD",
    description: "Altın/USD Paritesi"
  }
];

function TradingViewChart({
  symbol,
  containerId,
  height = 500,
  isFullscreen = false
}: {
  symbol: ChartSymbol;
  containerId: string;
  height?: number;
  isFullscreen?: boolean;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const widgetRef = useRef<any>(null);

  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/tv.js";
    script.async = true;
    script.onload = () => {
      if (window.TradingView && containerRef.current) {
        widgetRef.current = new window.TradingView.widget({
          autosize: true,
          symbol: symbol.tradingViewSymbol,
          interval: "60",
          timezone: "Europe/Istanbul",
          theme: "dark",
          style: "1",
          locale: "tr",
          toolbar_bg: "#0a0a0f",
          enable_publishing: false,
          allow_symbol_change: false,
          container_id: containerId,
          hide_side_toolbar: false,
          save_image: true,
          hide_top_toolbar: false,
          withdateranges: true,
          details: true,
          hotlist: false,
          calendar: false,
          show_popup_button: false,
          popup_width: "1000",
          popup_height: "650",
          no_referral_id: true,
          // localStorage çizim koruma parametreleri
          client_id: "forexsai_charts",
          user_id: "public",
          auto_save_delay: 5,
          load_last_chart: true,
          studies: [
            "MASimple@tv-basicstudies",
            "RSI@tv-basicstudies",
            "MACD@tv-basicstudies"
          ],
          overrides: {
            "paneProperties.background": "#0a0a0f",
            "paneProperties.backgroundType": "solid",
            "mainSeriesProperties.candleStyle.upColor": "#22c55e",
            "mainSeriesProperties.candleStyle.downColor": "#ef4444",
            "mainSeriesProperties.candleStyle.borderUpColor": "#22c55e",
            "mainSeriesProperties.candleStyle.borderDownColor": "#ef4444",
            "mainSeriesProperties.candleStyle.wickUpColor": "#22c55e",
            "mainSeriesProperties.candleStyle.wickDownColor": "#ef4444",
          }
        });
      }
    };
    document.head.appendChild(script);

    return () => {
      if (widgetRef.current) {
        try {
          widgetRef.current.remove?.();
        } catch (e) { }
      }
    };
  }, [symbol.tradingViewSymbol, containerId]);

  return (
    <div
      ref={containerRef}
      id={containerId}
      style={{ height: isFullscreen ? "calc(100vh - 120px)" : height }}
      className="w-full"
    />
  );
}

function ChartPanel({
  symbol,
  onFullscreen
}: {
  symbol: ChartSymbol;
  onFullscreen: (symbol: ChartSymbol) => void;
}) {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 2000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="glass-premium rounded-xl md:rounded-2xl overflow-hidden">
      <div className="flex items-center justify-between p-3 md:p-4 border-b border-white/10">
        <div className="flex items-center gap-2 md:gap-3">
          <div className="flex h-8 w-8 md:h-10 md:w-10 items-center justify-center rounded-lg md:rounded-xl bg-gradient-to-br from-accent/30 to-blue-500/30">
            <ChartsIcon size={20} className="text-accent" />
          </div>
          <div>
            <h3 className="font-bold text-base md:text-lg">{symbol.label}</h3>
            <p className="text-[10px] md:text-xs text-textSecondary">{symbol.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onFullscreen(symbol)}
            className="p-1.5 md:p-2 rounded-lg hover:bg-white/10 transition text-textSecondary hover:text-white"
            title="Tam Ekran"
          >
            <Maximize2 className="w-4 h-4 md:w-5 md:h-5" />
          </button>
        </div>
      </div>
      <div className="relative">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10">
            <LoadingIcon size={32} className="animate-spin text-accent" />
          </div>
        )}
        <TradingViewChart
          symbol={symbol}
          containerId={`tv_chart_${symbol.id}`}
          height={350}
        />
      </div>
    </div>
  );
}

export default function ChartsView() {
  const router = useRouter();
  const { t } = useI18nStore();
  const [fullscreenSymbol, setFullscreenSymbol] = useState<ChartSymbol | null>(null);

  const handleFullscreen = (symbol: ChartSymbol) => {
    setFullscreenSymbol(symbol);
  };

  const exitFullscreen = () => {
    setFullscreenSymbol(null);
  };

  if (fullscreenSymbol) {
    return (
      <div className="fixed inset-0 bg-background z-50">
        <div className="flex items-center justify-between p-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-accent/30 to-blue-500/30">
              <ChartsIcon size={24} className="text-accent" />
            </div>
            <div>
              <h2 className="font-bold text-xl">{fullscreenSymbol.label}</h2>
              <p className="text-xs text-textSecondary">{fullscreenSymbol.description}</p>
            </div>
          </div>
          <button
            onClick={exitFullscreen}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 transition"
          >
            <Minimize2 className="w-5 h-5" />
            <span>{t("common.minimize") || "Minimize"}</span>
          </button>
        </div>
        <TradingViewChart
          symbol={fullscreenSymbol}
          containerId={`tv_fullscreen_${fullscreenSymbol.id}`}
          isFullscreen={true}
        />
      </div>
    );
  }

  return (
    <div className="w-full text-white animate-in fade-in duration-300">
      <div className="max-w-[1600px] mx-auto p-3 md:p-6 space-y-4 md:space-y-6">
        {/* TradingView Login Info Banner */}
        <div className="glass-premium p-4 md:p-5 rounded-xl md:rounded-2xl border border-blue-500/30 bg-gradient-to-r from-blue-500/10 to-purple-500/10">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-xl bg-blue-500/20 flex-shrink-0">
                <SignalsIcon size={20} className="text-blue-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white mb-1">{t("chartsPage.tradingViewTitle")}</h3>
                <p className="text-sm text-textSecondary">
                  {t("chartsPage.tradingViewDesc")}
                </p>
              </div>
            </div>
            <a
              href="https://www.tradingview.com/accounts/signin/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-blue-500 hover:bg-blue-600 text-white font-semibold transition whitespace-nowrap"
            >
              <ExternalLink className="w-4 h-4" />
              {t("chartsPage.goToTradingView")}
            </a>
          </div>
          <div className="mt-3 pt-3 border-t border-white/10 flex flex-wrap gap-4 text-xs text-textSecondary">
            <span className="flex items-center gap-1">✏️ {t("chartsPage.drawingTools")}</span>
            <span className="flex items-center gap-1">📊 {t("chartsPage.indicators")}</span>
            <span className="flex items-center gap-1">💾 {t("chartsPage.autoSave")}</span>
            <span className="flex items-center gap-1">🔄 {t("chartsPage.liveData")}</span>
          </div>
        </div>

        {/* Neon EMA Charts */}
        <div className="space-y-6">
          <NeonChart
            symbol="NDX.INDX"
            symbolLabel="NASDAQ-100"
            initialTimeframe="1h"
            height={480}
          />
          <NeonChart
            symbol="XAUUSD.FOREX"
            symbolLabel="XAUUSD"
            initialTimeframe="1h"
            height={480}
          />
        </div>

        {/* TradingView Charts */}
        <div className="space-y-6">
          {CHART_SYMBOLS.map((symbol) => (
            <ChartPanel
              key={symbol.id}
              symbol={symbol}
              onFullscreen={handleFullscreen}
            />
          ))}
        </div>

        {/* Footer Info */}
        <div className="text-center text-xs text-textSecondary py-4">
          {t("chartsPage.footer")}
        </div>
      </div>
    </div>
  );
}
