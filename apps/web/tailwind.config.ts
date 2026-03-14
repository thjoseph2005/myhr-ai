import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          50: "#eef4fb",
          100: "#dbe7f5",
          500: "#14335c",
          700: "#0f2747",
          900: "#09182d"
        },
        accent: {
          500: "#c9242b",
          600: "#a61e24"
        },
        ink: "#0d1b2a",
        panel: "#f7f9fc",
        line: "#d5deea"
      },
      fontFamily: {
        sans: ["\"Avenir Next\"", "Avenir", "Segoe UI", "sans-serif"]
      },
      boxShadow: {
        card: "0 18px 60px rgba(12, 31, 56, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;
