/**
 * preferenceStore.ts — 用户偏好 Zustand store
 *
 * 管理：主题、语言、默认股票、K线周期、通知开关、仪表盘布局等
 * 自动持久化到 localStorage（key: ndxinfo.preferences）
 */

import { create } from "zustand";

// ---- 仪表盘面板可见性 ----
export type DashboardPanel =
  | "ndx-status"
  | "account-cards"
  | "equity-curve"
  | "positions"
  | "live-quotes"
  | "recent-orders"
  | "recent-signals"
  | "watchlist";

export type LayoutTemplate = "grid-3-col" | "grid-2-col" | "compact";

export interface DashboardLayout {
  template: LayoutTemplate;
  panelOrder: DashboardPanel[];
  hiddenPanels: DashboardPanel[];
}

const DEFAULT_PANEL_ORDER: DashboardPanel[] = [
  "ndx-status", "account-cards", "equity-curve",
  "positions", "live-quotes", "recent-orders", "recent-signals",
];

const DEFAULT_LAYOUT: DashboardLayout = {
  template: "grid-3-col",
  panelOrder: DEFAULT_PANEL_ORDER,
  hiddenPanels: [],
};

// ---- State ----
interface PreferenceState {
  // 外观
  theme: "dark" | "light";

  // 交易偏好
  defaultSymbol: string;
  chartInterval: "1m" | "5m" | "15m" | "1h" | "1d";

  // 通知
  notificationsEnabled: boolean;

  // 仪表盘布局
  dashboardLayout: DashboardLayout;

  // 方法
  setTheme: (t: "dark" | "light") => void;
  setDefaultSymbol: (s: string) => void;
  setChartInterval: (i: "1m" | "5m" | "15m" | "1h" | "1d") => void;
  setNotificationsEnabled: (v: boolean) => void;
  setDashboardLayout: (l: Partial<DashboardLayout>) => void;
  togglePanel: (panel: DashboardPanel) => void;
  resetDefaults: () => void;
}

// ---- localStorage 辅助 ----
const STORAGE_KEY = "ndxinfo.preferences";

function loadFromStorage(): Partial<PreferenceState> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch { /* ignore */ }
  return {};
}

function saveToStorage(state: PreferenceState) {
  try {
    const data: Record<string, unknown> = {
      theme: state.theme,
      defaultSymbol: state.defaultSymbol,
      chartInterval: state.chartInterval,
      notificationsEnabled: state.notificationsEnabled,
      dashboardLayout: state.dashboardLayout,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch { /* ignore */ }
}

// ---- 创建 store ----
const saved = loadFromStorage();

export const usePreferenceStore = create<PreferenceState>((set, get) => ({
  theme: saved.theme || "dark",
  defaultSymbol: saved.defaultSymbol || "NVDA",
  chartInterval: saved.chartInterval || "1d",
  notificationsEnabled: saved.notificationsEnabled ?? true,
  dashboardLayout: saved.dashboardLayout || { ...DEFAULT_LAYOUT },

  setTheme: (t) => {
    set({ theme: t });
    saveToStorage(get() as PreferenceState);
  },

  setDefaultSymbol: (s) => {
    set({ defaultSymbol: s });
    saveToStorage(get() as PreferenceState);
  },

  setChartInterval: (i) => {
    set({ chartInterval: i });
    saveToStorage(get() as PreferenceState);
  },

  setNotificationsEnabled: (v) => {
    set({ notificationsEnabled: v });
    saveToStorage(get() as PreferenceState);
  },

  setDashboardLayout: (l) => {
    const current = get().dashboardLayout;
    set({ dashboardLayout: { ...current, ...l } });
    saveToStorage(get() as PreferenceState);
  },

  togglePanel: (panel) => {
    const current = get().dashboardLayout;
    const hidden = current.hiddenPanels.includes(panel)
      ? current.hiddenPanels.filter((p) => p !== panel)
      : [...current.hiddenPanels, panel];
    set({ dashboardLayout: { ...current, hiddenPanels: hidden } });
    saveToStorage(get() as PreferenceState);
  },

  resetDefaults: () => {
    set({
      theme: "dark",
      defaultSymbol: "NVDA",
      chartInterval: "1d",
      notificationsEnabled: true,
      dashboardLayout: { ...DEFAULT_LAYOUT },
    });
    saveToStorage(get() as PreferenceState);
  },
}));
