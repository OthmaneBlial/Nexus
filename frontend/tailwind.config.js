/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx,vue}"],
  theme: {
    extend: {
      colors: {
        slateglass: {
          800: "rgba(15, 23, 42, 0.85)",
          900: "rgba(2, 6, 23, 0.92)",
        },
      },
    },
  },
  plugins: [],
};
