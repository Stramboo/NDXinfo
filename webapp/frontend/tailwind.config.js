/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // 这些颜色都会同时受 html.dark 控制；tailwind 让 fg/bg 颜色按
        // 当前主题从 CSS 变量里读，所以切换 theme = 切换 .dark 类
        bg: {
          DEFAULT: "var(--bg)",          // 主背景
          panel:   "var(--bg-panel)",    // 卡片底
          subtle:  "var(--bg-subtle)",   // 行/分隔
          input:   "var(--bg-input)",
          hover:   "var(--bg-hover)",
        },
        fg: {
          DEFAULT: "var(--fg)",          // 主前景
          muted:   "var(--fg-muted)",
          dim:     "var(--fg-dim)",
        },
        emerald: {
          400: "#34D399", 500: "#10B981", 600: "#059669",
        },
        rose: {
          400: "#FB7185", 500: "#F43F5E", 600: "#E11D48",
        },
        amber: {
          400: "#FBBF24", 500: "#F59E0B",
        },
        line: { DEFAULT: "var(--line)" },
      },
      fontFamily: {
        sans: ['Inter', '"Noto Sans SC"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Cascadia Code"', 'Consolas', 'monospace'],
      },
      borderRadius: { xl: "0.875rem" },
      transitionTimingFunction: { "out-smooth": "cubic-bezier(.22, 1, .36, 1)" },
    },
  },
  plugins: [],
};
