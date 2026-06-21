import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          base: "#0a0a0f",
          raised: "#0f0f18",
          overlay: "#141422",
        },
        accent: {
          blue: "#3b82f6",
          cyan: "#22d3ee",
          purple: "#a78bfa",
          amber: "#f59e0b",
        },
      },
      animation: {
        "glow-pulse": "glow-pulse 2s ease-in-out infinite alternate",
        "fade-in": "fade-in 0.3s ease-out",
        "slide-up": "slide-up 0.4s ease-out",
        "dot-bounce": "dot-bounce 1.4s infinite ease-in-out both",
      },
      keyframes: {
        "glow-pulse": {
          "0%": { boxShadow: "0 0 5px rgba(59, 130, 246, 0.1)" },
          "100%": { boxShadow: "0 0 20px rgba(59, 130, 246, 0.3)" },
        },
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "dot-bounce": {
          "0%, 80%, 100%": { transform: "scale(0)" },
          "40%": { transform: "scale(1)" },
        },
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};

export default config;
