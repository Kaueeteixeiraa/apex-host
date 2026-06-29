/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        apex: {
          bg: "#070711",
          panel: "#10101c",
          line: "#26233d",
          purple: "#9d4edd",
          cyan: "#00d4ff",
          text: "#f4f1ff",
          muted: "#9d98b7"
        }
      },
      boxShadow: {
        neon: "0 0 0 1px rgba(157, 78, 221, 0.35), 0 16px 60px rgba(0, 0, 0, 0.35)",
        glow: "0 0 35px rgba(0, 212, 255, 0.18)"
      }
    }
  },
  plugins: []
};
