import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./styles/globals.css";

// 启动时应用 localStorage 保存的主题（避免 HTML 默认 dark 闪烁）
(function applyStoredTheme() {
  const stored = (localStorage.getItem("ndxinfo.theme") as "dark" | "light" | null) || "dark";
  const root = document.documentElement;
  root.classList.add(stored);
})();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
