import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Core backgrounds
        background: "#060d20",
        obsidian: "#0B1326",
        surface: "#060d20",
        "surface-dim": "#060d20",
        "surface-bright": "#1f2b49",
        "surface-container": "#0f1930",
        "surface-container-high": "#141f38",
        "surface-container-highest": "#1a2540",
        "surface-container-low": "#091328",
        "surface-container-lowest": "#000000",
        "surface-tint": "#ba9eff",
        "surface-variant": "#1a2540",

        // Primary palette
        primary: "#ba9eff",
        "primary-container": "#ae8dff",
        "primary-dim": "#8455ef",
        "primary-fixed": "#ae8dff",
        "primary-fixed-dim": "#a27cff",
        "violet-primary": "#C0C1FF",
        "violet-container": "#8083FF",

        // Secondary palette
        secondary: "#9093ff",
        "secondary-container": "#2f2ebe",
        "secondary-dim": "#6063ee",
        "secondary-fixed": "#cdcdff",
        "secondary-fixed-dim": "#bdbeff",

        // Tertiary / Success
        tertiary: "#9bffce",
        "tertiary-container": "#69f6b8",
        "tertiary-dim": "#58e7ab",
        "tertiary-fixed": "#69f6b8",
        "tertiary-fixed-dim": "#58e7ab",
        "emerald-trust": "#4EDEA3",

        // Error / Danger
        error: "#ff6e84",
        "error-container": "#a70138",
        "error-dim": "#d73357",
        coral: "#FF6E84",

        // Text colors
        "on-background": "#dee5ff",
        "on-surface": "#dee5ff",
        "on-surface-variant": "#a3aac4",
        "on-primary": "#39008c",
        "on-primary-container": "#2b006e",
        "on-secondary": "#080079",
        "on-secondary-container": "#ccccff",
        "on-tertiary": "#006443",
        "on-tertiary-container": "#005a3c",
        "on-error": "#490013",
        "on-error-container": "#ffb2b9",
        frost: "#DAE2FD",
        "frost-muted": "#A3AAC4",
        ghost: "#464554",

        // Outlines / Borders
        outline: "#6d758c",
        "outline-variant": "#40475d",

        // Inverse
        "inverse-on-surface": "#4d556b",
        "inverse-primary": "#6e3bd7",
        "inverse-surface": "#faf8ff",
      },
      fontFamily: {
        inter: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'],
        grotesk: ['Space Grotesk', 'system-ui', 'sans-serif'],
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        glow: {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '0.8' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      animation: {
        'fade-in': 'fadeIn 0.6s ease-out forwards',
        'slide-up': 'slideUp 0.6s ease-out forwards',
        'slide-down': 'slideDown 0.4s ease-out forwards',
        'glow': 'glow 3s ease-in-out infinite',
        'float': 'float 4s ease-in-out infinite',
        'shimmer': 'shimmer 3s linear infinite',
      },
      backgroundImage: {
        'violet-gradient': 'linear-gradient(135deg, #c0c1ff, #8083ff)',
        'hero-glow': 'radial-gradient(ellipse at center, rgba(99, 102, 241, 0.15) 0%, transparent 70%)',
      },
      boxShadow: {
        'violet-glow': '0 0 20px rgba(99, 102, 241, 0.3)',
        'violet-glow-lg': '0 0 40px rgba(99, 102, 241, 0.2)',
        'ambient': '0px 20px 40px rgba(7, 0, 108, 0.15)',
      },
    },
  },
  plugins: [],
}
export default config
