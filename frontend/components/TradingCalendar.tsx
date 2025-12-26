import { ChevronLeft, ChevronRight } from "lucide-react";
import DashboardCard from "./DashboardCard";

interface CalendarDay {
  date: number;
  pnl?: number;
  isCurrentMonth?: boolean;
}

interface TradingCalendarProps {
  monthLabel: string;
  days: CalendarDay[];
  isLoading?: boolean;
}

const weekDays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export default function TradingCalendar({ monthLabel, days, isLoading = false }: TradingCalendarProps) {
  return (
    <DashboardCard className="p-0">
      <div className="flex items-center justify-between border-b border-white/5 px-5 py-4">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-textSecondary">Calendar</p>
          <h3 className="mt-1 text-lg font-semibold text-textPrimary">{monthLabel}</h3>
        </div>
        <div className="flex items-center gap-2">
          <button className="rounded-full border border-white/10 p-2 text-textSecondary transition hover:text-textPrimary">
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button className="rounded-full border border-white/10 p-2 text-textSecondary transition hover:text-textPrimary">
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
      {isLoading ? (
        <div className="p-5">
          <div className="grid grid-cols-7 gap-3">
            {Array.from({ length: 28 }).map((_, index) => (
              <div key={index} className="skeleton h-16 w-full" />
            ))}
          </div>
        </div>
      ) : (
        <div className="p-5">
          <div className="grid grid-cols-7 gap-2 text-xs text-textSecondary">
            {weekDays.map((day) => (
              <div key={day} className="text-center uppercase tracking-[0.2em]">
                {day}
              </div>
            ))}
          </div>
          <div className="mt-3 grid grid-cols-7 gap-2">
            {days.map((day, index) => {
              const isPositive = typeof day.pnl === "number" && day.pnl > 0;
              const isNegative = typeof day.pnl === "number" && day.pnl < 0;

              return (
                <div
                  key={`${day.date}-${index}`}
                  className={`rounded-xl border border-white/5 px-3 py-2 text-sm transition hover:border-white/20 ${
                    day.isCurrentMonth === false ? "opacity-40" : ""
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-textPrimary">{day.date}</span>
                    {typeof day.pnl === "number" ? (
                      <span
                        className={`text-[11px] font-semibold ${
                          isPositive ? "text-success" : isNegative ? "text-danger" : "text-textSecondary"
                        }`}
                      >
                        {day.pnl > 0 ? "+" : ""}${Math.abs(day.pnl).toFixed(0)}
                      </span>
                    ) : null}
                  </div>
                  <div className="mt-2 h-1 rounded-full bg-white/5">
                    <div
                      className={`h-full rounded-full ${
                        isPositive ? "bg-success" : isNegative ? "bg-danger" : "bg-white/10"
                      }`}
                      style={{
                        width: `${Math.min(Math.abs(day.pnl ?? 0) / 20, 100)}%`
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </DashboardCard>
  );
}
