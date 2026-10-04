/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      colors: {
        bg: {
          primary: '#0B0F17',
          secondary: '#111827',
          tertiary: '#1a2234',
          card: '#131b2e',
          hover: '#1e2a40',
        },
        brand: {
          teal: '#0ECFCF',
          tealDim: '#0ECFCF33',
          violet: '#7C3AED',
          violetDim: '#7C3AED33',
          pink: '#EC4899',
        },
        accent: {
          50: '#edfcfc',
          100: '#d1f7f7',
          200: '#a8eeee',
          300: '#6ee0e0',
          400: '#33c9c9',
          500: '#0ECFCF',
          600: '#0aa8a8',
          700: '#0d8282',
          800: '#106868',
          900: '#125656',
        },
        signal: {
          infection: '#F97316',
          autoimmunity: '#8B5CF6',
          metabolic: '#10B981',
          cancer: '#EF4444',
          tissue: '#F59E0B',
          unclassified: '#6B7280',
        },
        severity: {
          high: '#EF4444',
          medium: '#F59E0B',
          low: '#10B981',
          ns: '#6B7280',
        },
        border: {
          subtle: '#1e2d4a',
          bright: '#2a3f5f',
        },
      },
      backgroundImage: {
        'gradient-brand': 'linear-gradient(135deg, #0ECFCF 0%, #7C3AED 100%)',
        'gradient-card': 'linear-gradient(135deg, rgba(14,207,207,0.05) 0%, rgba(124,58,237,0.05) 100%)',
        'gradient-hero': 'radial-gradient(ellipse 80% 50% at 50% -20%, rgba(14,207,207,0.15) 0%, transparent 60%), radial-gradient(ellipse 60% 40% at 80% 80%, rgba(124,58,237,0.1) 0%, transparent 60%)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'weave': 'weave 8s ease-in-out infinite',
        'counter': 'counter 1s ease-out',
        'shimmer': 'shimmer 2s linear infinite',
        'fade-up': 'fadeUp 0.5s ease-out',
        'slide-in': 'slideIn 0.3s ease-out',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        weave: {
          '0%, 100%': { strokeDashoffset: '0' },
          '50%': { strokeDashoffset: '20' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideIn: {
          '0%': { opacity: '0', transform: 'translateX(100%)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
      boxShadow: {
        card: '0 1px 3px rgba(0,0,0,0.4), 0 0 0 1px rgba(30,45,74,0.8)',
        glow: '0 0 20px rgba(14,207,207,0.15)',
        'glow-violet': '0 0 20px rgba(124,58,237,0.15)',
        'inner-subtle': 'inset 0 1px 0 rgba(255,255,255,0.04)',
      },
    },
  },
  plugins: [],
}
