import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          teal: "#35C8BB",
          "teal-light": "#E6FAF8",
          "teal-mid": "#B0EDE7",
          "teal-deep": "#1FA899",
          blue: "#1B8FD4",
          "blue-light": "#E3F2FD",
          gold: "#D4A017",
          "gold-light": "#FFF8E1",
        },
        surface: {
          base: "#F7FAFA",
          white: "#FFFFFF",
          warm: "#FAFCFC",
          raised: "#FFFFFF",
          muted: "#F0F4F4",
          border: "#E2EAEA",
          "border-strong": "#C8D8D8",
        },
        ink: {
          rich: "#1A2540",
          body: "#3A4560",
          secondary: "#6B7A90",
          muted: "#9EAAB8",
          faint: "#C5CED6",
        },
      },
      fontFamily: {
        display: ['"Outfit"', "system-ui", "sans-serif"],
        body: ['"Nunito Sans"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "monospace"],
      },
      boxShadow: {
        card: "0 1px 3px rgba(26, 37, 64, 0.06), 0 4px 16px rgba(26, 37, 64, 0.04)",
        "card-hover": "0 4px 24px rgba(26, 37, 64, 0.1), 0 0 0 1px rgba(53, 200, 187, 0.12)",
        soft: "0 2px 8px rgba(26, 37, 64, 0.04)",
        glow: "0 0 20px rgba(53, 200, 187, 0.15), 0 0 60px rgba(53, 200, 187, 0.05)",
        "glow-sm": "0 0 10px rgba(53, 200, 187, 0.12)",
      },
      backgroundImage: {
        "gradient-teal": "linear-gradient(135deg, #35C8BB 0%, #1B8FD4 100%)",
        "gradient-teal-soft": "linear-gradient(135deg, #E6FAF8 0%, #E3F2FD 100%)",
        "hero-mesh": "radial-gradient(ellipse at 20% 0%, rgba(53,200,187,0.08) 0%, transparent 50%), radial-gradient(ellipse at 80% 100%, rgba(27,143,212,0.05) 0%, transparent 50%)",
      },
      animation: {
        "pulse-soft": "pulse-soft 3s ease-in-out infinite",
        "badge-ring": "badge-ring 2.5s ease-in-out infinite",
        "slide-up": "slide-up 0.5s cubic-bezier(0.16, 1, 0.3, 1)",
      },
      keyframes: {
        "pulse-soft": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.7" },
        },
        "badge-ring": {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(53, 200, 187, 0.35)" },
          "50%": { boxShadow: "0 0 0 6px rgba(53, 200, 187, 0)" },
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      borderRadius: {
        "2xl": "16px",
        "3xl": "20px",
        "4xl": "24px",
      },
    },
  },
  plugins: [],
};

export default config;
