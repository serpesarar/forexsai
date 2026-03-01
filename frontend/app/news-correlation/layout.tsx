import { Metadata } from "next";

export const metadata: Metadata = {
  title: "News-Chart Correlation | ForexsAI",
  description: "AI-powered financial news analysis with chart correlation",
};

export default function NewsCorrelationLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-slate-950">
      {/* Sidebar is rendered by root layout */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
