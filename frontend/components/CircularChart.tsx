import DashboardCard from "./DashboardCard";

interface CircularChartProps {
  title: string;
  winners: number;
  losers: number;
  isLoading?: boolean;
}

const RADIUS = 52;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export default function CircularChart({ title, winners, losers, isLoading = false }: CircularChartProps) {
  const total = winners + losers;
  const winRate = total === 0 ? 0 : Math.round((winners / total) * 100);
  const offset = CIRCUMFERENCE - (winRate / 100) * CIRCUMFERENCE;

  return (
    <DashboardCard title={title} className="relative">
      {isLoading ? (
        <div className="space-y-4">
          <div className="skeleton h-36 w-36 rounded-full" />
          <div className="skeleton h-4 w-2/3" />
          <div className="skeleton h-4 w-1/2" />
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          <div className="flex flex-wrap items-center justify-between gap-6">
            <div className="relative flex h-36 w-36 items-center justify-center">
              <svg className="h-36 w-36 -rotate-90" viewBox="0 0 120 120">
                <circle
                  cx="60"
                  cy="60"
                  r={RADIUS}
                  stroke="rgba(255,255,255,0.08)"
                  strokeWidth="12"
                  fill="none"
                />
                <circle
                  cx="60"
                  cy="60"
                  r={RADIUS}
                  stroke="#f87171"
                  strokeWidth="12"
                  fill="none"
                />
                <circle
                  cx="60"
                  cy="60"
                  r={RADIUS}
                  stroke="#4ade80"
                  strokeWidth="12"
                  fill="none"
                  strokeDasharray={CIRCUMFERENCE}
                  strokeDashoffset={offset}
                  strokeLinecap="round"
                  className="transition-all duration-700 ease-out"
                />
              </svg>
              <div className="absolute text-center">
                <p className="text-3xl font-semibold text-textPrimary">{winRate}%</p>
                <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">Winrate</p>
              </div>
            </div>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <span className="h-3 w-3 rounded-sm bg-success" />
                <div>
                  <p className="text-lg font-semibold text-textPrimary">{winners}</p>
                  <p className="text-xs uppercase tracking-[0.2em] text-textSecondary">Winners</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="h-3 w-3 rounded-sm bg-danger" />
                <div>
                  <p className="text-lg font-semibold text-textPrimary">{losers}</p>
                  <p className="text-xs uppercase tracking-[0.2em] text-textSecondary">Losers</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </DashboardCard>
  );
}
