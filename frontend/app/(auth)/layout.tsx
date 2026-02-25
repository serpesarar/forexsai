import { ReactNode } from "react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-black text-white relative overflow-hidden font-sans">
      {/* Subtle Vignette */}
      <div className="pointer-events-none absolute inset-0 z-0 bg-[radial-gradient(ellipse_at_center,_transparent_0%,_black_100%)] opacity-60" />

      {/* Faint noise texture */}
      <div className="pointer-events-none absolute inset-0 z-0 bg-[url('/noise.png')] opacity-[0.025] mix-blend-overlay" />

      {/* Very subtle grid */}
      <div
        className="pointer-events-none absolute inset-0 z-0 opacity-[0.015]"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px),
                            linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)`,
          backgroundSize: '60px 60px'
        }}
      />

      {/* Ambient cyan glow - top corner */}
      <div className="pointer-events-none absolute -top-32 -right-32 w-[500px] h-[500px] z-0 rounded-full bg-cyan-500/5 blur-3xl" />

      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
}
