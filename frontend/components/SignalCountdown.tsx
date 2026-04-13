"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useSignalCountdown } from "../hooks/useSignalCountdown";

interface SignalCountdownProps {
  /** Model identifier (clear_trend, pulse_v3, emel, etc.) */
  modelKey: string;
  /** Custom refresh interval in seconds (optional) */
  refreshIntervalSeconds?: number;
  /** Last signal timestamp to sync countdown */
  signalTimestamp?: string | Date | null;
  /** Callback when countdown reaches 0 */
  onRefresh?: () => void;
  /** Size variant */
  size?: "sm" | "md" | "lg";
  /** Show progress ring */
  showProgress?: boolean;
  /** Custom label */
  label?: string;
}

const sizeConfig = {
  sm: {
    container: "px-2 py-1 text-[10px]",
    ring: 24,
    stroke: 2,
    fontSize: "9px",
  },
  md: {
    container: "px-3 py-1.5 text-[12px]",
    ring: 32,
    stroke: 2.5,
    fontSize: "11px",
  },
  lg: {
    container: "px-4 py-2 text-[14px]",
    ring: 40,
    stroke: 3,
    fontSize: "13px",
  },
};

export function SignalCountdown({
  modelKey,
  refreshIntervalSeconds,
  signalTimestamp,
  onRefresh,
  size = "md",
  showProgress = true,
  label,
}: SignalCountdownProps) {
  const {
    formattedTime,
    progressPercent,
    isWarning,
    isCritical,
    isActive,
    remainingSeconds,
  } = useSignalCountdown(modelKey, refreshIntervalSeconds, signalTimestamp);

  const [wasRefreshed, setWasRefreshed] = useState(false);

  // Trigger onRefresh callback when countdown reaches 0
  useEffect(() => {
    if (remainingSeconds === 0 && !wasRefreshed) {
      setWasRefreshed(true);
      onRefresh?.();
    } else if (remainingSeconds > 0) {
      setWasRefreshed(false);
    }
  }, [remainingSeconds, wasRefreshed, onRefresh]);

  const config = sizeConfig[size];

  // Dynamic colors based on countdown state
  const getColors = () => {
    if (isCritical) {
      return {
        bg: "rgba(239, 68, 68, 0.15)", // red
        border: "rgba(239, 68, 68, 0.5)",
        text: "#ef4444",
        ring: "#ef4444",
        glow: "0 0 20px rgba(239, 68, 68, 0.4)",
        pulse: "pulse-red 1s ease-in-out infinite",
      };
    }
    if (isWarning) {
      return {
        bg: "rgba(234, 179, 8, 0.15)", // yellow
        border: "rgba(234, 179, 8, 0.5)",
        text: "#eab308",
        ring: "#eab308",
        glow: "0 0 15px rgba(234, 179, 8, 0.3)",
        pulse: "pulse-yellow 1.5s ease-in-out infinite",
      };
    }
    return {
      bg: "rgba(6, 182, 212, 0.12)", // cyan
      border: "rgba(6, 182, 212, 0.35)",
      text: "#06b6d4",
      ring: "#06b6d4",
      glow: "0 0 10px rgba(6, 182, 212, 0.2)",
      pulse: "none",
    };
  };

  const colors = getColors();
  const radius = (config.ring - config.stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (progressPercent / 100) * circumference;

  return (
    <motion.div
      className={`flex items-center gap-2 rounded-xl font-mono font-bold tracking-wide ${config.container}`}
      style={{
        background: colors.bg,
        border: `1px solid ${colors.border}`,
        color: colors.text,
        boxShadow: `${colors.glow}, 0 0 0 1px rgba(255,255,255,0.02) inset`,
        animation: colors.pulse,
      }}
      animate={{
        scale: isCritical ? [1, 1.05, 1] : 1,
      }}
      transition={{
        duration: 0.3,
        repeat: isCritical ? Infinity : 0,
        repeatType: "reverse",
      }}
    >
      {/* Progress Ring */}
      {showProgress && (
        <div className="relative" style={{ width: config.ring, height: config.ring }}>
          <svg
            width={config.ring}
            height={config.ring}
            className="transform -rotate-90"
          >
            {/* Background ring */}
            <circle
              cx={config.ring / 2}
              cy={config.ring / 2}
              r={radius}
              fill="none"
              stroke="rgba(255,255,255,0.1)"
              strokeWidth={config.stroke}
            />
            {/* Progress ring */}
            <motion.circle
              cx={config.ring / 2}
              cy={config.ring / 2}
              r={radius}
              fill="none"
              stroke={colors.ring}
              strokeWidth={config.stroke}
              strokeLinecap="round"
              strokeDasharray={circumference}
              animate={{ strokeDashoffset }}
              transition={{ duration: 0.5, ease: "easeOut" }}
            />
          </svg>
          
          {/* Center dot indicator */}
          <motion.div
            className="absolute inset-0 flex items-center justify-center"
            animate={{
              scale: isActive ? [1, 1.2, 1] : 1,
            }}
            transition={{
              duration: isCritical ? 0.5 : isWarning ? 1 : 2,
              repeat: Infinity,
            }}
          >
            <div
              className="w-2 h-2 rounded-full"
              style={{
                background: isActive ? "var(--accent-positive)" : colors.ring,
                boxShadow: `0 0 8px ${isActive ? "var(--accent-positive)" : colors.ring}`,
              }}
            />
          </motion.div>
        </div>
      )}

      {/* Text Content */}
      <div className="flex flex-col items-start">
        {label && (
          <span className="text-[9px] uppercase tracking-wider opacity-60">
            {label}
          </span>
        )}
        <AnimatePresence mode="wait">
          <motion.span
            key={formattedTime}
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 5 }}
            transition={{ duration: 0.15 }}
            style={{ fontSize: config.fontSize }}
          >
            {formattedTime}
          </motion.span>
        </AnimatePresence>
      </div>

      {/* Keyframe styles */}
      <style jsx>{`
        @keyframes pulse-red {
          0%, 100% { box-shadow: 0 0 20px rgba(239, 68, 68, 0.4); }
          50% { box-shadow: 0 0 30px rgba(239, 68, 68, 0.6), 0 0 40px rgba(239, 68, 68, 0.3); }
        }
        @keyframes pulse-yellow {
          0%, 100% { box-shadow: 0 0 15px rgba(234, 179, 8, 0.3); }
          50% { box-shadow: 0 0 25px rgba(234, 179, 8, 0.5); }
        }
      `}</style>
    </motion.div>
  );
}

/**
 * Compact badge version for minimal display
 */
export function SignalCountdownBadge({
  modelKey,
  refreshIntervalSeconds,
  signalTimestamp,
  onRefresh,
}: Omit<SignalCountdownProps, "size" | "showProgress" | "label">) {
  const {
    formattedTime,
    isWarning,
    isCritical,
    remainingSeconds,
  } = useSignalCountdown(modelKey, refreshIntervalSeconds, signalTimestamp);

  const [wasRefreshed, setWasRefreshed] = useState(false);

  useEffect(() => {
    if (remainingSeconds === 0 && !wasRefreshed) {
      setWasRefreshed(true);
      onRefresh?.();
    } else if (remainingSeconds > 0) {
      setWasRefreshed(false);
    }
  }, [remainingSeconds, wasRefreshed, onRefresh]);

  // Dynamic styles based on state
  const getStyles = () => {
    if (isCritical) {
      return {
        background: "color-mix(in srgb, #ef4444 20%, var(--bg-input))",
        border: "1px solid color-mix(in srgb, #ef4444 60%, var(--border-subtle))",
        color: "#ef4444",
        dotColor: "#ef4444",
        animation: "pulse-critical 0.8s ease-in-out infinite",
      };
    }
    if (isWarning) {
      return {
        background: "color-mix(in srgb, #eab308 15%, var(--bg-input))",
        border: "1px solid color-mix(in srgb, #eab308 50%, var(--border-subtle))",
        color: "#eab308",
        dotColor: "#eab308",
        animation: "pulse-warning 1.2s ease-in-out infinite",
      };
    }
    return {
      background: "color-mix(in srgb, var(--accent-info) 12%, var(--bg-input))",
      border: "1px solid color-mix(in srgb, var(--accent-info) 35%, var(--border-subtle))",
      color: "var(--text-primary)",
      dotColor: "var(--accent-positive)",
      animation: "none",
    };
  };

  const styles = getStyles();

  return (
    <motion.div
      className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-[12px] font-mono font-bold tracking-wide"
      style={{
        background: styles.background,
        border: styles.border,
        color: styles.color,
        boxShadow: "0 0 0 1px rgba(255,255,255,0.02) inset, 0 8px 18px rgba(0,0,0,0.22)",
      }}
      animate={{
        scale: isCritical ? [1, 1.03, 1] : 1,
      }}
      transition={{
        duration: 0.4,
        repeat: isCritical ? Infinity : 0,
        repeatType: "reverse",
      }}
    >
      {/* Pulsing dot */}
      <motion.div
        className="w-2 h-2 rounded-full"
        style={{
          background: styles.dotColor,
          boxShadow: `0 0 10px ${styles.dotColor}`,
        }}
        animate={{
          scale: [1, 1.3, 1],
          opacity: [1, 0.7, 1],
        }}
        transition={{
          duration: isCritical ? 0.5 : isWarning ? 1 : 2,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      
      {/* Time text */}
      <AnimatePresence mode="wait">
        <motion.span
          key={formattedTime}
          initial={{ opacity: 0, x: -3 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 3 }}
          transition={{ duration: 0.1 }}
        >
          {formattedTime}
        </motion.span>
      </AnimatePresence>

      {/* CSS for pulse animations */}
      <style jsx>{`
        @keyframes pulse-critical {
          0%, 100% { 
            box-shadow: 0 0 0 1px rgba(255,255,255,0.02) inset, 0 8px 18px rgba(0,0,0,0.22), 0 0 15px rgba(239, 68, 68, 0.3);
          }
          50% { 
            box-shadow: 0 0 0 1px rgba(255,255,255,0.02) inset, 0 8px 25px rgba(0,0,0,0.3), 0 0 25px rgba(239, 68, 68, 0.5);
          }
        }
        @keyframes pulse-warning {
          0%, 100% { 
            box-shadow: 0 0 0 1px rgba(255,255,255,0.02) inset, 0 6px 14px rgba(0,0,0,0.2), 0 0 12px rgba(234, 179, 8, 0.2);
          }
          50% { 
            box-shadow: 0 0 0 1px rgba(255,255,255,0.02) inset, 0 6px 20px rgba(0,0,0,0.25), 0 0 20px rgba(234, 179, 8, 0.4);
          }
        }
      `}</style>
    </motion.div>
  );
}

/**
 * Multi-model countdown display for panels with multiple data sources
 */
export function MultiSignalCountdown({
  models,
}: {
  models: Array<{
    key: string;
    label: string;
    timestamp?: string | Date | null;
    interval?: number;
  }>;
}) {
  return (
    <div className="flex items-center gap-2">
      {models.map((model) => (
        <SignalCountdownBadge
          key={model.key}
          modelKey={model.key}
          refreshIntervalSeconds={model.interval}
          signalTimestamp={model.timestamp}
        />
      ))}
    </div>
  );
}
