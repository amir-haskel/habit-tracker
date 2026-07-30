/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'Avenir', 'Helvetica', 'Arial', 'sans-serif'],
      },
      colors: {
        // Route-context pastel backgrounds
        surface: {
          dashboard: '#fdf2f5', // faint pink
          config: '#f5f3fb', // light lavender
        },
        // Muted slate for headers/body (never absolute black)
        ink: {
          DEFAULT: '#334155', // slate-700, headers
          soft: '#64748b', // slate-500, body
          faint: '#94a3b8', // slate-400, hints/placeholder
        },
        // Per-habit accent palette (soft pastels)
        accent: {
          orange: '#f9a03f',
          blue: '#5aa9e6',
          mint: '#4fd1c5',
          purple: '#a78bfa',
          pink: '#f472b6',
        },
      },
      borderRadius: {
        card: '20px',
        pill: '9999px',
      },
      boxShadow: {
        // Soft raised card against pastel backgrounds
        card: '0 4px 14px rgba(0, 0, 0, 0.05)',
        'card-hover': '0 6px 20px rgba(0, 0, 0, 0.08)',
        // Subtle inset for pressed/selected states
        inset: 'inset 0 2px 6px rgba(0, 0, 0, 0.06)',
      },
      maxWidth: {
        app: '480px', // mobile-first column, centered on desktop
      },
    },
  },
  plugins: [],
}
