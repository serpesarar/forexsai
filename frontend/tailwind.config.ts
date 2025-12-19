import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"] ,
  theme: {
    extend: {
      colors: {
        background: "#0a0e27",
        card: "rgba(255,255,255,0.05)",
        accent: {
          from: "#667eea",
          to: "#764ba2"
        },
        success: "#26a69a",
        danger: "#ef5350",
        warning: "#ffa726",
        textPrimary: "#ffffff",
        textSecondary: "rgba(255,255,255,0.7)"
      },
      boxShadow: {
        glass: "0 20px 40px rgba(0, 0, 0, 0.35)",
        glow: "0 0 25px rgba(118, 75, 162, 0.4)"
      },
      backdropBlur: {
        glass: "12px"
      }
    }
  },
  plugins: []
};

export default config;
