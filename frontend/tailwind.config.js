/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['Georgia', 'serif'],
      },
      colors: {
        paper: '#fcfcfc',
        ink: '#1a1a1a',
      }
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
