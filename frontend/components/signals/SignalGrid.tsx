"use client";

import dynamic from "next/dynamic";
import SignalCard from "./SignalCard";

// Lazy-load heavy panels so the initial bundle stays small.
const MLPredictionPanel = dynamic(() => import("../MLPredictionPanel"), { ssr: false });
const EmelPanel = dynamic(() => import("../panels/EmelPanel"), { ssr: false });
const SMCPanel = dynamic(() => import("../panels/SMCPanel"), { ssr: false });
const PulsePanel = dynamic(() => import("../panels/PulsePanel"), { ssr: false });
const PulseMLPanel = dynamic(() => import("../panels/PulseMLPanel"), { ssr: false });
const PulseV3Panel = dynamic(() => import("../panels/PulseV3Panel"), { ssr: false });

interface Props {
  symbol: string;
  symbolLabel: string;
}

/**
 * 2×3 responsive signal grid.
 * Row 1: ML (0.25) · EMEL (0.20) · SMC (0.10)
 * Row 2: Pulse 1 (0.15) · Pulse 2 (0.15) · Pulse 3 (0.15)
 */
export function SignalGrid({ symbol, symbolLabel }: Props) {
  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      <SignalCard modelKey="ml" title="ML Prediction" subtitle="LightGBM · 150 feature" weight={0.25}>
        <MLPredictionPanel symbol={symbol} symbolLabel={symbolLabel} />
      </SignalCard>

      <SignalCard modelKey="emel" title="EMEL 9-Check" subtitle="Strategic 9-point" weight={0.2}>
        <EmelPanel symbol={symbol} />
      </SignalCard>

      <SignalCard modelKey="smc" title="Smart Money Concepts" subtitle="ICT · Order Blocks · FVG" weight={0.1}>
        <SMCPanel lockedSymbol={symbol} />
      </SignalCard>

      <SignalCard modelKey="pulse1" title="Pulse 1 – Algo" subtitle="6-component scalp" weight={0.15}>
        <PulsePanel symbol={symbol} />
      </SignalCard>

      <SignalCard modelKey="pulse2" title="Pulse 2 – ML+TA" subtitle="ML hybrid" weight={0.15}>
        <PulseMLPanel symbol={symbol} />
      </SignalCard>

      <SignalCard modelKey="pulse3" title="Pulse 3 – MTF" subtitle="5m · 1H · 4H" weight={0.15}>
        <PulseV3Panel symbol={symbol} />
      </SignalCard>
    </div>
  );
}

export default SignalGrid;
