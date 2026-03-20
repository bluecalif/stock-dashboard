/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      animation: {
        "slide-down": "slide-down 0.3s ease-out",
      },
      keyframes: {
        "slide-down": {
          "0%": { opacity: "0", transform: "translateX(-50%) translateY(-1rem)" },
          "100%": { opacity: "1", transform: "translateX(-50%) translateY(0)" },
        },
      },
    },
  },
  plugins: [],
}

