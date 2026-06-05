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
          deep: "#F8FAFC",
          surface: "#EEF2F7",
          panel: "#FFFFFF",
          border: "#CBD5E1",
          accent: "#005AB5",
          muted: "#4B5563",
          amber: "#E69F00",
        },
        delta: {
          up: "#00836D",
          down: "#D55E00",
        },
      },
      boxShadow: {
        panel: "0 14px 35px rgba(15, 23, 42, 0.08)",
      },
    },
  },
  plugins: [],
};
