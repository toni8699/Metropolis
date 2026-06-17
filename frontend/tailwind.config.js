/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        vroom: {
          bg: "#D0F0C0",
          surface: "#FCFCE5",
          card: "#f5f5d0",
          muted: "#35593b",
          muted2: "#46634b",
          text: "#2D5A27",
          heading: "#183B1E",
          accent: "#E34B31",
          sage: "#dbe8be",
          coral: "#F8AFA1",
          gold: "#FFD166",
          error: "#ffd8cf",
          errorText: "#7a2215",
        },
      },
      boxShadow: {
        neo: "8px 8px 0px 0px rgba(24,59,30,0.45)",
        neoSm: "4px 4px 0px 0px rgba(24,59,30,0.45)",
        neoBlack: "8px 8px 0px 0px rgba(0,0,0,1)",
        neoLg: "10px 10px 0px 0px rgba(0,0,0,1)",
        neoCard: "6px 6px 0px 0px rgba(24,59,30,0.45)",
      },
    },
  },
  plugins: [],
};
