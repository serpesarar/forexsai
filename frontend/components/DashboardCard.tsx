import { ReactNode } from "react";
import clsx from "clsx";

interface DashboardCardProps {
  title?: string;
  children: ReactNode;
  className?: string;
}

export default function DashboardCard({ title, children, className }: DashboardCardProps) {
  return (
    <div
      className={clsx(
        "rounded-2xl border border-white/5 bg-card/95 shadow-glass backdrop-blur-sm",
        "transition duration-300 hover:-translate-y-1 hover:shadow-[0_24px_50px_rgba(0,0,0,0.35)]",
        className
      )}
    >
      {title ? (
        <div className="border-b border-white/5 px-5 py-4">
          <h3 className="text-sm font-semibold text-textSecondary uppercase tracking-[0.2em]">
            {title}
          </h3>
        </div>
      ) : null}
      <div className="p-5">{children}</div>
    </div>
  );
}
