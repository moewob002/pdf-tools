/** @type {import('tailwindcss').Config} */
const token = (name) => `rgb(var(--c-${name}) / <alpha-value>)`;

export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  theme: {
    extend: {
      // Semantic colours backed by CSS custom properties (see src/style.css).
      colors: {
        bg: token("bg"),
        surface: { DEFAULT: token("surface"), 2: token("surface-2"), 3: token("surface-3") },
        fg: token("fg"),
        muted: token("muted"),
        line: { DEFAULT: token("line"), strong: token("line-strong") },
        "on-primary": token("on-primary"),
        primary: { DEFAULT: token("primary"), text: token("primary-text") },
        secondary: { DEFAULT: token("secondary"), text: token("secondary-text") },
        accent: { DEFAULT: token("accent"), text: token("accent-text") },
        cyan: { DEFAULT: token("cyan"), text: token("cyan-text") },
        success: token("success"),
        warning: token("warning"),
        danger: token("danger"),
        info: token("info"),
        focus: token("focus"),
      },
    },
  },
  plugins: [],
};
