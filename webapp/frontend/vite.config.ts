import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": { target: "http://127.0.0.1:8765", changeOrigin: true },
      "/ws":  { target: "ws://127.0.0.1:8765", ws: true, changeOrigin: true },
    },
    fs: {
      // 允许访问项目根目录的 reports/（给 NdxStatusBar "查看报告" 链接用）
      allow: ["..", "../..", "../../.."],
    },
  },
});
