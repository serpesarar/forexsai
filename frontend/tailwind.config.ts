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
        glass: "0 18px 35px rgba(0, 0, 0, 0.5), 0 0 15px rgba(79, 140, 255, 0.03)",
        "glow-sm": "0 0 15px rgba(79, 140, 255, 0.15)",
        "glow-md": "0 0 30px rgba(79, 140, 255, 0.2)",
        "glow-lg": "0 0 50px rgba(79, 140, 255, 0.25)",
        "glow-success": "0 0 30px rgba(22, 199, 132, 0.2)",
        "glow-danger": "0 0 30px rgba(234, 57, 67, 0.2)",
        "glow-warning": "0 0 30px rgba(245, 166, 35, 0.2)",
        "neon": "0 0 5px rgba(79, 140, 255, 0.2), 0 0 20px rgba(79, 140, 255, 0.1)",
        "neon-pink": "0 0 5px rgba(234, 57, 67, 0.2), 0 0 20px rgba(234, 57, 67, 0.1)",
        "card-hover": "0 25px 50px -12px rgba(0, 0, 0, 0.6), 0 0 30px rgba(79, 140, 255, 0.1)",
      },
      backdropBlur: {
        glass: "10px",
        xs: "2px",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "JetBrains Mono", "ui-monospace", "SFMono-Regular"],
      },
      animation: {
        "gradient-x": "gradient-x 15s ease infinite",
        "gradient-y": "gradient-y 15s ease infinite",
        "gradient-xy": "gradient-xy 15s ease infinite",
        "pulse-slow": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "shimmer": "shimmer 2s linear infinite",
        "float": "float 6s ease-in-out infinite",
        "glow-pulse": "glow-pulse 2s ease-in-out infinite",
        "slide-up": "slide-up 0.5s ease-out",
        "slide-down": "slide-down 0.5s ease-out",
        "fade-in": "fade-in 0.5s ease-out",
        "scale-in": "scale-in 0.3s ease-out",
        "spin-slow": "spin 8s linear infinite",
        "bounce-slow": "bounce 3s infinite",
      },
      keyframes: {
        "gradient-x": {
          "0%, 100%": { "background-position": "0% 50%" },
          "50%": { "background-position": "100% 50%" },
        },
        "gradient-y": {
          "0%, 100%": { "background-position": "50% 0%" },
          "50%": { "background-position": "50% 100%" },
        },
        "gradient-xy": {
          "0%, 100%": { "background-position": "0% 0%" },
          "25%": { "background-position": "100% 0%" },
          "50%": { "background-position": "100% 100%" },
          "75%": { "background-position": "0% 100%" },
        },
        "shimmer": {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
        "float": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
        "glow-pulse": {
          "0%, 100%": { opacity: "1", filter: "brightness(1)" },
          "50%": { opacity: "0.8", filter: "brightness(1.2)" },
        },
        "slide-up": {
          "0%": { transform: "translateY(20px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        "slide-down": {
          "0%": { transform: "translateY(-20px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "scale-in": {
          "0%": { transform: "scale(0.95)", opacity: "0" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
        "mesh-gradient": "linear-gradient(135deg, rgba(79, 140, 255, 0.06) 0%, rgba(79, 140, 255, 0.06) 50%, rgba(22, 199, 132, 0.04) 100%)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
