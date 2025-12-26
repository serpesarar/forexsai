import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "var(--bg-primary)",
        card: "var(--bg-card)",
        accent: "var(--accent)",
        success: "var(--success)",
        danger: "var(--danger)",
        textPrimary: "var(--text-primary)",
        textSecondary: "var(--text-secondary)",
      },
      boxShadow: {
        glass: "0 18px 35px rgba(0, 0, 0, 0.35)",
      },
      backdropBlur: {
        glass: "10px",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "JetBrains Mono", "ui-monospace", "SFMono-Regular"],
      },
    },
  },
  plugins: [],
};

export default config;
