/**
 * sandboxStore.ts --- Independent Zustand store for demo/sandbox account.
 *
 * Initial cash: $100,000. Tracks cash, positions, orders, and equity history.
 * buyStock / sellStock mutate state and record a snapshot after each trade.
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

// ---- State ----

interface SandboxState {
  /** Whether the user is currently in simulation mode */
  isSimulationMode: boolean;
  setIsSimulationMode: (v: boolean) => void;

  sandboxCash: number;
  sandboxPositions: SandboxPosition[];
  sandboxOrders: SandboxOrder[];
  sandboxEquityHistory: SandboxEquityPoint[];

  buyStock: (symbol: string, quantity: number, price: number) => void;
  sellStock: (symbol: string, quantity: number, price: number) => void;
  snapshotEquity: () => void;
  resetSandbox: () => void;
}

const INITIAL_CASH = 100_000;

export const useSandboxStore = create<SandboxState>((set, get) => ({
  isSimulationMode: false,
  setIsSimulationMode: (v) => set({ isSimulationMode: v }),

  sandboxCash: INITIAL_CASH,
  sandboxPositions: [],
  sandboxOrders: [],
  sandboxEquityHistory: [],

  buyStock: (symbol, quantity, price) => {
    const state = get();
    const cost = quantity * price;
    if (cost > state.sandboxCash) return; // insufficient funds

    const order: SandboxOrder = {
      orderId: nextId(),
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

    // Auto-snapshot after trade
    get().snapshotEquity();
  },

  sellStock: (symbol, quantity, price) => {
    const state = get();
    const idx = state.sandboxPositions.findIndex((p) => p.symbol === symbol);
    if (idx < 0) return;
    const pos = state.sandboxPositions[idx];
    if (quantity > pos.quantity) return; // insufficient shares

    const revenue = quantity * price;

    const order: SandboxOrder = {
      orderId: nextId(),
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

    get().snapshotEquity();
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

  resetSandbox: () => {
    set({
      isSimulationMode: false,
      sandboxCash: INITIAL_CASH,
      sandboxPositions: [],
      sandboxOrders: [],
      sandboxEquityHistory: [],
    });
  },
}));
