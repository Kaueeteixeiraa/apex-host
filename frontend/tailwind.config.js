/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        apex: {
          bg: "#070711",
          panel: "#071221",
          line: "#14365f",
          purple: "#1d4ed8",
          cyan: "#18b6ff",
          blue: "#006dff",
          text: "#eef7ff",
          muted: "#8ea7c7"
        }
      },
      boxShadow: {
        neon: "0 0 0 1px rgba(24, 182, 255, 0.32), 0 18px 70px rgba(0, 109, 255, 0.18)",
        glow: "0 0 38px rgba(24, 182, 255, 0.28)"
      }
    }
  },
  plugins: []
};
