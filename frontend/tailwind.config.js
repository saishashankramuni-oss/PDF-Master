/** tailwind.config.js */
module.exports = {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1a1a2e',
          50: '#f0f0f5',
          100: '#e0e0e8',
          200: '#d0d0dc',
          300: '#a0a0b8',
          400: '#707094',
          500: '#505080',
          600: '#30305c',
          700: '#202040',
          800: '#101028',
          900: '#00001a',
        },
        secondary: {
          DEFAULT: '#f7fafc',
        },
        accent: {
          DEFAULT: '#00d4aa',
          50: '#e6fffa',
          100: '#b2f5eb',
          200: '#81ecec',
          300: '#4fd1c5',
          400: '#1dd1af',
          500: '#00d4aa',
          600: '#00a888',
          700: '#007c6c',
          800: '#005052',
          900: '#002830',
        },
        danger: {
          DEFAULT: '#ef4444',
        },
        warning: {
          DEFAULT: '#f59e0b',
        },
        info: {
          DEFAULT: '#3b82f6',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Poppins', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        lg: '0.5rem',
        md: '0.375rem',
        sm: '0.25rem',
      },
    },
  },
  plugins: [],
}