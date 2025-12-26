import { ReactNode } from "react";
import DashboardCard from "./DashboardCard";

interface MetricCardProps {
  label: string;
  value: string;
  meta: string;
  trend?: "positive" | "negative" | "neutral";
  icon?: ReactNode;
}

const trendStyles: Record<NonNullable<MetricCardProps["trend"]>, string> = {
  positive: "text-success",
  negative: "text-danger",
  neutral: "text-textPrimary"
};

export default function MetricCard({ label, value, meta, trend = "neutral", icon }: MetricCardProps) {
  return (
    <DashboardCard>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-textSecondary">{label}</p>
          <h3 className={`mt-2 text-2xl font-semibold ${trendStyles[trend]}`}>{value}</h3>
          <p className="mt-2 text-xs text-textSecondary">{meta}</p>
        </div>
        {icon ? (
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/5 text-textSecondary">
            {icon}
          </div>
        ) : null}
      </div>
    </DashboardCard>
  );
}
