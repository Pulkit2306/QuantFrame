/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        dark: {
          900: '#0a0a0f',
          800: '#111118',
          700: '#1a1a24',
          600: '#22222f',
        },
        accent: {
          green: '#00ff88',
          red: '#ff4466',
          blue: '#4488ff',
        }
      }
    }
  },
  plugins: [],
}
