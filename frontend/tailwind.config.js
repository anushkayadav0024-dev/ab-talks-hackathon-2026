/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        darkBg: "#0B0F19",
        darkCard: "#151B2C",
        darkBorder: "#222D44",
        accentTeal: "#0D9488", // teal-600
        accentTealLight: "#14B8A6", // teal-500
        accentIndigo: "#4F46E5", // indigo-600
        accentIndigoLight: "#6366F1", // indigo-500
      },
    },
  },
  plugins: [],
}
