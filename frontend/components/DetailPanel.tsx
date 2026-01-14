"use client";

import { X, Info, TrendingUp, TrendingDown, Target, AlertTriangle, CheckCircle, BookOpen } from "lucide-react";
import CircularProgress from "./CircularProgress";
import { useI18nStore } from "../lib/i18n/store";

type DetailType = "support_resistance" | "ema_distance" | "trend_channel";

interface DetailPanelProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  symbol: string;
  type: DetailType | null;
  data: Record<string, any> | null;
}

// Guide content generator based on metric type and values
function useGuideContent(type: DetailType | null, data: Record<string, any> | null, symbol: string) {
  const { t } = useI18nStore();
  
  if (!type || !data) return null;

  const formatPrice = (v: number) => v?.toLocaleString(undefined, { maximumFractionDigits: 2 }) ?? "--";
  
  if (type === "ema_distance") {
    const period = data.period || 20;
    const emaValue = data.emaValue;
    const currentPrice = data.currentPrice;
    const distance = data.distance;
    const distancePct = data.distancePct;
    const isAbove = distance > 0;
    const isClose = Math.abs(distancePct) < 0.5;
    const isFar = Math.abs(distancePct) > 2;

    return {
      title: t("guide.ema.title").replace("{period}", String(period)),
      description: t("guide.ema.description").replace("{period}", String(period)),
      whatItIs: t("guide.ema.whatItIs").replace("{period}", String(period)),
      currentStatus: {
        icon: isAbove ? TrendingUp : TrendingDown,
        color: isAbove ? "text-success" : "text-danger",
        text: isAbove 
          ? t("guide.ema.aboveEma").replace("{distance}", formatPrice(Math.abs(distance))).replace("{pct}", Math.abs(distancePct).toFixed(2))
          : t("guide.ema.belowEma").replace("{distance}", formatPrice(Math.abs(distance))).replace("{pct}", Math.abs(distancePct).toFixed(2)),
      },
      expectations: [
        {
          condition: t("guide.ema.touchCondition"),
          reaction: isAbove ? t("guide.ema.touchReactionBullish") : t("guide.ema.touchReactionBearish"),
          probability: isAbove ? "70-75%" : "65-70%",
          icon: Target,
        },
        {
          condition: t("guide.ema.breakCondition"),
          reaction: isAbove ? t("guide.ema.breakReactionBearish") : t("guide.ema.breakReactionBullish"),
          probability: "25-30%",
          icon: AlertTriangle,
        },
      ],
      tradingTips: [
        period === 20 ? t("guide.ema.tip20") : period === 50 ? t("guide.ema.tip50") : t("guide.ema.tip200"),
        isClose ? t("guide.ema.tipClose") : isFar ? t("guide.ema.tipFar") : t("guide.ema.tipMid"),
        t("guide.ema.tipGeneral"),
      ],
      keyLevels: [
        { label: t("guide.ema.emaLevel"), value: formatPrice(emaValue), importance: "high" },
        { label: t("guide.ema.currentPrice"), value: formatPrice(currentPrice), importance: "medium" },
        { label: t("guide.ema.distance"), value: `${formatPrice(Math.abs(distance))} (${Math.abs(distancePct).toFixed(2)}%)`, importance: isClose ? "high" : "low" },
      ],
    };
  }

  if (type === "trend_channel") {
    const trendStrength = data.trendStrength || 0;
    const channelWidth = data.channelWidth || 0;
    const distanceToUpper = data.distanceToUpper || 0;
    const distanceToLower = data.distanceToLower || 0;
    const slope = data.slope || 0;
    const rSquared = data.rSquared || 0;
    const isUpperHalf = Math.abs(distanceToUpper) < Math.abs(distanceToLower);
    const isStrong = trendStrength > 0.7;
    const isUptrend = slope > 0;

    return {
      title: t("guide.channel.title"),
      description: t("guide.channel.description"),
      whatItIs: t("guide.channel.whatItIs"),
      currentStatus: {
        icon: isUptrend ? TrendingUp : TrendingDown,
        color: isStrong ? (isUptrend ? "text-success" : "text-danger") : "text-accent",
        text: isUptrend 
          ? t("guide.channel.uptrendStatus").replace("{strength}", Math.round(trendStrength * 100).toString())
          : t("guide.channel.downtrendStatus").replace("{strength}", Math.round(trendStrength * 100).toString()),
      },
      expectations: [
        {
          condition: t("guide.channel.upperCondition"),
          reaction: t("guide.channel.upperReaction"),
          probability: rSquared > 0.7 ? "75-80%" : "60-65%",
          icon: TrendingDown,
        },
        {
          condition: t("guide.channel.lowerCondition"),
          reaction: t("guide.channel.lowerReaction"),
          probability: rSquared > 0.7 ? "75-80%" : "60-65%",
          icon: TrendingUp,
        },
        {
          condition: t("guide.channel.breakoutCondition"),
          reaction: isUptrend ? t("guide.channel.breakoutReactionUp") : t("guide.channel.breakoutReactionDown"),
          probability: "20-25%",
          icon: AlertTriangle,
        },
      ],
      tradingTips: [
        isUpperHalf ? t("guide.channel.tipUpperHalf") : t("guide.channel.tipLowerHalf"),
        isStrong ? t("guide.channel.tipStrong") : t("guide.channel.tipWeak"),
        t("guide.channel.tipGeneral"),
      ],
      keyLevels: [
        { label: t("guide.channel.upperBand"), value: formatPrice(distanceToUpper), importance: isUpperHalf ? "high" : "medium" },
        { label: t("guide.channel.lowerBand"), value: formatPrice(Math.abs(distanceToLower)), importance: !isUpperHalf ? "high" : "medium" },
        { label: t("guide.channel.width"), value: formatPrice(channelWidth), importance: "low" },
      ],
    };
  }

  if (type === "support_resistance") {
    const price = data.price || 0;
    const strength = data.strength || 0;
    const hits = data.hits || 0;
    const reliability = data.reliability || 0;
    const distance = data.distance || 0;
    const distancePct = data.distancePct || 0;
    const isSupport = data.type === "support" || distance > 0;
    const isStrong = strength > 0.7;
    const isClose = Math.abs(distancePct) < 1;

    return {
      title: isSupport ? t("guide.sr.titleSupport") : t("guide.sr.titleResistance"),
      description: isSupport ? t("guide.sr.descSupport") : t("guide.sr.descResistance"),
      whatItIs: isSupport ? t("guide.sr.whatIsSupport") : t("guide.sr.whatIsResistance"),
      currentStatus: {
        icon: isSupport ? TrendingUp : TrendingDown,
        color: isStrong ? "text-success" : "text-accent",
        text: t("guide.sr.status")
          .replace("{level}", formatPrice(price))
          .replace("{distance}", formatPrice(Math.abs(distance)))
          .replace("{pct}", Math.abs(distancePct).toFixed(2)),
      },
      expectations: [
        {
          condition: isSupport ? t("guide.sr.touchSupportCondition") : t("guide.sr.touchResistanceCondition"),
          reaction: isSupport ? t("guide.sr.touchSupportReaction") : t("guide.sr.touchResistanceReaction"),
          probability: isStrong ? "70-80%" : "55-65%",
          icon: isSupport ? TrendingUp : TrendingDown,
        },
        {
          condition: isSupport ? t("guide.sr.breakSupportCondition") : t("guide.sr.breakResistanceCondition"),
          reaction: isSupport ? t("guide.sr.breakSupportReaction") : t("guide.sr.breakResistanceReaction"),
          probability: isStrong ? "20-30%" : "35-45%",
          icon: AlertTriangle,
        },
      ],
      tradingTips: [
        t("guide.sr.tip1").replace("{hits}", String(hits)),
        isClose ? t("guide.sr.tipClose") : t("guide.sr.tipFar"),
        isStrong ? t("guide.sr.tipStrong") : t("guide.sr.tipWeak"),
      ],
      keyLevels: [
        { label: isSupport ? t("guide.sr.supportLevel") : t("guide.sr.resistanceLevel"), value: formatPrice(price), importance: "high" },
        { label: t("guide.sr.strength"), value: `${Math.round(strength * 100)}%`, importance: isStrong ? "high" : "medium" },
        { label: t("guide.sr.touches"), value: String(hits), importance: hits > 3 ? "high" : "low" },
      ],
    };
  }

  return null;
}

export default function DetailPanel({ isOpen, onClose, title, symbol, type, data }: DetailPanelProps) {
  const { t } = useI18nStore();
  const guide = useGuideContent(type, data, symbol);
  
  if (!isOpen || !type || !data) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center p-6 md:items-center">
      <div className="detail-panel-overlay absolute inset-0" onClick={onClose} />
      <div className="detail-panel-content relative z-10 w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-2xl border border-white/10 bg-background p-6">
        <div className="flex items-center justify-between sticky top-0 bg-background pb-4 border-b border-white/10">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">{symbol}</p>
            <h3 className="mt-2 text-lg font-semibold">{title}</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-9 w-9 items-center justify-center rounded-full border border-white/10 text-textSecondary hover:border-white/30 transition"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Guide Section */}
        {guide && (
          <div className="mt-6 space-y-6">
            {/* What is this metric */}
            <div className="rounded-xl border border-accent/30 bg-accent/5 p-4">
              <div className="flex items-center gap-2 text-accent mb-2">
                <BookOpen className="h-4 w-4" />
                <span className="text-sm font-semibold">{t("guide.whatIsThis")}</span>
              </div>
              <p className="text-sm text-textSecondary leading-relaxed">{guide.whatItIs}</p>
            </div>

            {/* Current Status */}
            <div className="rounded-xl border border-white/10 bg-white/5 p-4">
              <div className="flex items-center gap-2 mb-3">
                <Info className="h-4 w-4 text-textSecondary" />
                <span className="text-sm font-semibold">{t("guide.currentStatus")}</span>
              </div>
              <div className={`flex items-center gap-3 ${guide.currentStatus.color}`}>
                <guide.currentStatus.icon className="h-5 w-5" />
                <span className="text-sm">{guide.currentStatus.text}</span>
              </div>
            </div>

            {/* Key Levels */}
            <div className="grid grid-cols-3 gap-3">
              {guide.keyLevels.map((level) => (
                <div 
                  key={level.label} 
                  className={`rounded-xl border p-3 ${
                    level.importance === "high" 
                      ? "border-accent/50 bg-accent/10" 
                      : "border-white/10 bg-white/5"
                  }`}
                >
                  <p className="text-[10px] uppercase tracking-[0.2em] text-textSecondary">{level.label}</p>
                  <p className="mt-1 text-lg font-mono">{level.value}</p>
                </div>
              ))}
            </div>

            {/* Expected Reactions */}
            <div className="rounded-xl border border-white/10 bg-white/5 p-4">
              <div className="flex items-center gap-2 mb-4">
                <Target className="h-4 w-4 text-accent" />
                <span className="text-sm font-semibold">{t("guide.expectedReactions")}</span>
              </div>
              <div className="space-y-3">
                {guide.expectations.map((exp, idx) => (
                  <div key={idx} className="rounded-lg border border-white/5 bg-white/5 p-3">
                    <div className="flex items-start gap-3">
                      <exp.icon className="h-4 w-4 mt-0.5 text-textSecondary flex-shrink-0" />
                      <div className="flex-1">
                        <p className="text-xs text-accent font-medium">{exp.condition}</p>
                        <p className="text-sm text-textPrimary mt-1">{exp.reaction}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-[10px] uppercase tracking-wider text-textSecondary">{t("guide.probability")}</span>
                          <span className="text-xs font-mono text-success">{exp.probability}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Trading Tips */}
            <div className="rounded-xl border border-success/30 bg-success/5 p-4">
              <div className="flex items-center gap-2 text-success mb-3">
                <CheckCircle className="h-4 w-4" />
                <span className="text-sm font-semibold">{t("guide.tradingTips")}</span>
              </div>
              <ul className="space-y-2">
                {guide.tradingTips.map((tip, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-textSecondary">
                    <span className="text-success mt-0.5">•</span>
                    <span>{tip}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Original Data Display */}
        <div className="mt-6 pt-6 border-t border-white/10">
          <p className="text-xs uppercase tracking-[0.2em] text-textSecondary mb-4">{t("guide.technicalData")}</p>
        
        {type === "support_resistance" && (
          <div className="mt-6 space-y-6">
            <CircularProgress
              value={data.reliability * 100}
              size={180}
              label="Reliability Score"
              sublabel={`${Math.round(data.reliability * 100)}%`}
              colorClassName={data.reliability > 0.8 ? "text-success" : "text-accent"}
            />
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="text-textSecondary uppercase tracking-[0.2em]">Distance (pts)</p>
                <p className="mt-2 text-lg font-mono text-success">+{data.distance}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="text-textSecondary uppercase tracking-[0.2em]">Distance (%)</p>
                <p className={`mt-2 text-lg font-mono ${data.distancePct > 0 ? "text-success" : "text-danger"}`}>
                  {data.distancePct.toFixed(2)}%
                </p>
              </div>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-xs text-textSecondary space-y-2">
              <div className="flex items-center justify-between">
                <span>Strength</span>
                <span className="font-mono">{data.strength}/10</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Touches</span>
                <span className="font-mono">{data.hits}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Last Touched</span>
                <span className="font-mono">{data.lastTouched}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Price Level</span>
                <span className="font-mono">${data.price}</span>
              </div>
            </div>
            <div className="rounded-xl border border-white/10 bg-gradient-to-br from-white/5 to-transparent p-4 text-xs text-textSecondary">
              Mini context chart placeholder
            </div>
          </div>
        )}

        {type === "ema_distance" && (
          <div className="mt-6 space-y-6">
            <CircularProgress
              value={Math.min(Math.abs(data.distancePct), 100)}
              size={180}
              label="Distance from EMA"
              sublabel={`${data.distancePct.toFixed(2)}%`}
              colorClassName={Math.abs(data.distancePct) > 2 ? "text-accent" : "text-textSecondary"}
            />
            <div className="grid grid-cols-2 gap-4 text-xs">
              {[
                { label: "EMA Value", value: data.emaValue },
                { label: "Current Price", value: data.currentPrice },
                { label: "Absolute Distance", value: data.distance },
                { label: "Distance %", value: `${data.distancePct.toFixed(2)}%` },
              ].map((item) => (
                <div key={item.label} className="rounded-xl border border-white/10 bg-white/5 p-4">
                  <p className="text-textSecondary uppercase tracking-[0.2em]">{item.label}</p>
                  <p className="mt-2 text-lg font-mono">{item.value}</p>
                </div>
              ))}
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-xs text-textSecondary space-y-2">
              <div className="flex items-center justify-between">
                <span>Signal Interpretation</span>
                <span className="font-mono">
                  {data.distancePct > 1
                    ? "Above EMA (Bullish)"
                    : data.distancePct < -1
                      ? "Below EMA (Bearish)"
                      : "Near EMA (Neutral)"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>EMA Period</span>
                <span className="font-mono">{data.period} periods</span>
              </div>
            </div>
          </div>
        )}

        {type === "trend_channel" && (
          <div className="mt-6 space-y-6">
            <CircularProgress
              value={data.trendStrength * 100}
              size={180}
              label="Trend Strength"
              sublabel={`${Math.round(data.trendStrength * 100)}%`}
              colorClassName={data.trendStrength > 0.7 ? "text-success" : "text-accent"}
            />
            <div className="grid grid-cols-2 gap-4 text-xs">
              {[
                { label: "Channel Width", value: data.channelWidth },
                { label: "Distance to Upper", value: data.distanceToUpper },
                { label: "Distance to Lower", value: data.distanceToLower },
                { label: "R² Correlation", value: data.rSquared.toFixed(2) },
              ].map((item) => (
                <div key={item.label} className="rounded-xl border border-white/10 bg-white/5 p-4">
                  <p className="text-textSecondary uppercase tracking-[0.2em]">{item.label}</p>
                  <p className="mt-2 text-lg font-mono">{item.value}</p>
                </div>
              ))}
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-xs text-textSecondary space-y-2">
              <div className="flex items-center justify-between">
                <span>Position in Channel</span>
                <span className="font-mono">
                  {data.distanceToUpper < data.distanceToLower ? "Upper half" : "Lower half"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Slope</span>
                <span className="font-mono">{data.slope.toFixed(4)} pts/candle</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Trend Quality</span>
                <span className="font-mono">{data.trendQuality}</span>
              </div>
            </div>
          </div>
        )}
        </div>
      </div>
    </div>
  );
}
