/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"DM Sans"', "system-ui", "sans-serif"],
        display: ['"Fraunces"', "Georgia", "serif"],
      },
      colors: {
        lake: {
          deep: "#050a12",
          surface: "#0b1220",
          panel: "rgba(11, 18, 32, 0.85)",
          border: "rgba(45, 212, 191, 0.18)",
          accent: "#2dd4bf",
          muted: "#94a3b8",
          amber: "#fbbf24",
        },
        delta: {
          up: "#2dd4bf",
          down: "#f87171",
        },
      },
      boxShadow: {
        panel: "0 20px 50px rgba(2, 6, 23, 0.45)",
      },
    },
  },
  plugins: [],
};
