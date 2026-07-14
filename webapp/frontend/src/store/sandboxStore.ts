/**
 * sandboxStore.ts --- Independent Zustand store for demo/sandbox account.
 *
 * Initial cash: $100,000. Tracks cash, positions, orders, and equity history.
 * buyStock / sellStock mutate state, sync to backend SQLite, and record a snapshot.
 * On mount, loadFromServer restores persisted state.
 */

import { create } from "zustand";

// ---- Types ----

export type SandboxPosition = {
  symbol: string;
  quantity: number;
  avgCost: number;
  currentPrice: number;
};

export type SandboxOrder = {
  orderId: string;
  symbol: string;
  side: "BUY" | "SELL";
  quantity: number;
  price: number;
  ts: number;
  status: "filled";
};

export type SandboxEquityPoint = {
  ts: number;
  equity: number;
  cash: number;
  marketValue: number;
};

// ---- Helpers ----

let _oid = 0;
function nextId(): string {
  return `sandbox-${Date.now()}-${++_oid}`;
}

async function persistOrder(symbol: string, side: string, quantity: number, price: number, orderId: string) {
  try {
    await fetch("/api/sandbox/order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol, side, quantity, price, order_id: orderId }),
    });
  } catch { /* silently ignore persistence errors */ }
}

// ---- State ----

interface SandboxState {
  loaded: boolean;
  /** Whether the user is currently in simulation mode */
  isSimulationMode: boolean;
  setIsSimulationMode: (v: boolean) => void;

  sandboxCash: number;
  sandboxPositions: SandboxPosition[];
  sandboxOrders: SandboxOrder[];
  sandboxEquityHistory: SandboxEquityPoint[];

  loadFromServer: () => Promise<void>;
  buyStock: (symbol: string, quantity: number, price: number) => void;
  sellStock: (symbol: string, quantity: number, price: number) => void;
  updatePrices: (prices: Record<string, number>) => void;
  snapshotEquity: () => void;
  resetSandbox: () => Promise<void>;
}

const INITIAL_CASH = 100_000;

export const useSandboxStore = create<SandboxState>((set, get) => ({
  loaded: false,
  isSimulationMode: false,
  setIsSimulationMode: (v) => set({ isSimulationMode: v }),

  sandboxCash: INITIAL_CASH,
  sandboxPositions: [],
  sandboxOrders: [],
  sandboxEquityHistory: [],

  loadFromServer: async () => {
    if (get().loaded) return;
    try {
      const res = await fetch("/api/sandbox/account");
      if (!res.ok) throw new Error("failed");
      const data = await res.json();
      set({
        loaded: true,
        sandboxCash: data.cash ?? INITIAL_CASH,
        sandboxPositions: (data.positions || []).map((p: any) => ({
          symbol: p.symbol,
          quantity: p.quantity,
          avgCost: p.avg_cost,
          currentPrice: p.avg_cost, // will be updated by prices fetch
        })),
      });
    } catch {
      set({ loaded: true }); // use default state
    }
  },

  buyStock: (symbol, quantity, price) => {
    const state = get();
    const cost = quantity * price;
    if (cost > state.sandboxCash) return; // insufficient funds

    const orderId = nextId();
    const order: SandboxOrder = {
      orderId,
      symbol,
      side: "BUY",
      quantity,
      price,
      ts: Date.now(),
      status: "filled",
    };

    // Update / create position
    const idx = state.sandboxPositions.findIndex((p) => p.symbol === symbol);
    let positions: SandboxPosition[];
    if (idx >= 0) {
      const existing = state.sandboxPositions[idx];
      const totalQty = existing.quantity + quantity;
      const totalCost = existing.avgCost * existing.quantity + cost;
      positions = [...state.sandboxPositions];
      positions[idx] = {
        ...existing,
        quantity: totalQty,
        avgCost: totalCost / totalQty,
        currentPrice: price,
      };
    } else {
      positions = [
        ...state.sandboxPositions,
        { symbol, quantity, avgCost: price, currentPrice: price },
      ];
    }

    set({
      sandboxCash: state.sandboxCash - cost,
      sandboxPositions: positions,
      sandboxOrders: [order, ...state.sandboxOrders].slice(0, 100),
    });

    // Persist to backend (fire-and-forget)
    persistOrder(symbol, "BUY", quantity, price, orderId);
    get().snapshotEquity();
  },

  sellStock: (symbol, quantity, price) => {
    const state = get();
    const idx = state.sandboxPositions.findIndex((p) => p.symbol === symbol);
    if (idx < 0) return;
    const pos = state.sandboxPositions[idx];
    if (quantity > pos.quantity) return; // insufficient shares

    const revenue = quantity * price;
    const orderId = nextId();

    const order: SandboxOrder = {
      orderId,
      symbol,
      side: "SELL",
      quantity,
      price,
      ts: Date.now(),
      status: "filled",
    };

    let positions: SandboxPosition[];
    if (quantity === pos.quantity) {
      positions = state.sandboxPositions.filter((_, i) => i !== idx);
    } else {
      positions = [...state.sandboxPositions];
      positions[idx] = {
        ...pos,
        quantity: pos.quantity - quantity,
        currentPrice: price,
      };
    }

    set({
      sandboxCash: state.sandboxCash + revenue,
      sandboxPositions: positions,
      sandboxOrders: [order, ...state.sandboxOrders].slice(0, 100),
    });

    // Persist to backend (fire-and-forget)
    persistOrder(symbol, "SELL", quantity, price, orderId);
    get().snapshotEquity();
  },

  updatePrices: (prices: Record<string, number>) => {
    const state = get();
    const positions = state.sandboxPositions.map((p) => ({
      ...p,
      currentPrice: prices[p.symbol] ?? p.currentPrice,
    }));
    set({ sandboxPositions: positions });
  },

  snapshotEquity: () => {
    const state = get();
    const marketValue = state.sandboxPositions.reduce(
      (sum, p) => sum + p.quantity * p.currentPrice,
      0,
    );
    const equity = state.sandboxCash + marketValue;
    const point: SandboxEquityPoint = {
      ts: Date.now(),
      equity,
      cash: state.sandboxCash,
      marketValue,
    };
    const history = [...state.sandboxEquityHistory, point].slice(-600);
    set({ sandboxEquityHistory: history });
  },

  resetSandbox: async () => {
    try { await fetch("/api/sandbox/reset", { method: "POST" }); } catch {}
    set({
      isSimulationMode: false,
      sandboxCash: INITIAL_CASH,
      sandboxPositions: [],
      sandboxOrders: [],
      sandboxEquityHistory: [],
    });
  },
}));
