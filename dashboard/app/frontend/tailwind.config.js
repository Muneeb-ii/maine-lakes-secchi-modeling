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
          accentSoft: "#EFF6FF",
          muted: "#4B5563",
          amber: "#E69F00",
          sectionLake: "#0072B2",
          sectionDrivers: "#009E73",
          sectionCompare: "#CC79A7",
          claro: "#1A9B6E",
          claroBright: "#09ED68",
          claroSoft: "#E8F7F1",
        },
        delta: {
          up: "#00836D",
          down: "#D55E00",
        },
        clarity: {
          turbid: {
            bg: "#FFF7ED",
            border: "#D55E00",
          },
          moderate: {
            bg: "#FFFBEB",
            border: "#E69F00",
          },
          clearer: {
            bg: "#ECFDF5",
            border: "#00836D",
          },
        },
      },
      boxShadow: {
        panel: "0 14px 35px rgba(15, 23, 42, 0.08)",
      },
    },
  },
  plugins: [],
};
