import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#fcf8ff",
        surface: "#ffffff",
        "surface-container": "#f0ecf9",
        "surface-container-low": "#f5f2ff",
        "surface-container-high": "#eae6f4",
        "surface-variant": "#e4e1ee",
        primary: "#3525cd",
        "primary-container": "#4f46e5",
        secondary: "#0058be",
        tertiary: "#7e3000",
        outline: "#777587",
        "outline-variant": "#c7c4d8",
        error: "#ba1a1a",
        "error-container": "#ffdad6",
        "on-surface": "#1b1b24",
        "on-surface-variant": "#464555"
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["Geist", "ui-monospace", "monospace"]
      },
      borderRadius: {
        xl: "0.75rem"
      },
      boxShadow: {
        soft: "0 12px 24px rgba(30, 41, 59, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;
