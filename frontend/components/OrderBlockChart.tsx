"use client";

import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  ReferenceArea
} from "recharts";

type OrderBlock = {
  index: number;
  type: "bullish" | "bearish";
  zone_low: number;
  zone_high: number;
  score: number;
};

type Props = {
  orderBlocks: OrderBlock[];
};

const sampleSeries = Array.from({ length: 30 }, (_, idx) => ({
  index: idx,
  price: 21500 + Math.sin(idx / 3) * 20 + idx * 0.5
}));

export default function OrderBlockChart({ orderBlocks }: Props) {
  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={sampleSeries}>
          <XAxis dataKey="index" hide />
          <YAxis domain={[21450, 21650]} hide />
          <Tooltip contentStyle={{ background: "#10142f", borderRadius: 12 }} />
          <Line type="monotone" dataKey="price" stroke="#667eea" strokeWidth={2} dot={false} />
          {orderBlocks.map((ob) => (
            <ReferenceArea
              key={ob.index}
              x1={Math.max(0, ob.index - 2)}
              x2={Math.min(sampleSeries.length - 1, ob.index + 2)}
              y1={ob.zone_low}
              y2={ob.zone_high}
              strokeOpacity={0}
              fill={ob.type === "bullish" ? "rgba(38,166,154,0.3)" : "rgba(239,83,80,0.3)"}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
