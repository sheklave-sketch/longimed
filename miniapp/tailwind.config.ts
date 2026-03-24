import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        teal: {
          50: "#F0FDFA",
          100: "#CCFBF1",
          200: "#99F6E4",
          300: "#5EEAD4",
          400: "#35C8BB",
          500: "#14B8A6",
          600: "#0D9488",
          700: "#0F766E",
        },
        navy: {
          50: "#F0F1F4",
          100: "#D4D7E0",
          200: "#A9AFBF",
          300: "#7E849F",
          400: "#535A7E",
          500: "#2E3557",
          600: "#1A2540",
          700: "#111830",
          800: "#0A0E1F",
          900: "#050810",
        },
        sky: {
          400: "#1B8FD4",
        },
        surface: "#F5FFFE",
      },
      fontFamily: {
        display: ['"Plus Jakarta Sans"', "system-ui", "sans-serif"],
        body: ['"DM Sans"', "system-ui", "sans-serif"],
      },
      boxShadow: {
        glass: "0 8px 32px 0 rgba(26, 37, 64, 0.06)",
        "glass-lg": "0 16px 48px 0 rgba(26, 37, 64, 0.1)",
        glow: "0 0 24px rgba(53, 200, 187, 0.2)",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "mesh-teal":
          "radial-gradient(at 20% 80%, rgba(53,200,187,0.08) 0%, transparent 50%), radial-gradient(at 80% 20%, rgba(27,143,212,0.06) 0%, transparent 50%)",
      },
    },
  },
  plugins: [],
};

export default config;
