import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"] ,
  theme: {
    extend: {
      colors: {
        background: "#1a1d29",
        card: "#252837",
        accent: {
          from: "#4ade80",
          to: "#22c55e"
        },
        success: "#4ade80",
        danger: "#f87171",
        warning: "#fbbf24",
        textPrimary: "#f8fafc",
        textSecondary: "rgba(248, 250, 252, 0.7)"
      },
      boxShadow: {
        glass: "0 20px 40px rgba(0, 0, 0, 0.35)",
        glow: "0 0 25px rgba(74, 222, 128, 0.35)"
      },
      backdropBlur: {
        glass: "12px"
      }
    }
  },
  plugins: []
};

export default config;
