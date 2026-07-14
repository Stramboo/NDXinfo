/**
 * tradeStore.ts — 中心状态机（Zustand）
 *
 * 每个 push/poll 都让组件重新订阅
 */

import { create } from "zustand";
import type { Account, Order, Position, Signal, EquityPoint } from "../lib/api";

export type WSLike =
  | { type: "tick";          data: { symbol: string; price: number; ts: number } }
  | { type: "order_update";  data: Order }
  | { type: "equity_update"; data: EquityPoint }
  | { type: "signal";        data: Signal }
  | { type: "log";           data: { level: string; msg: string; ts: number; context?: Record<string, unknown> } }
  | { type: "pong";          data: { ts: number } };

export type LogEntry = { level: string; msg: string; ts: number; context?: Record<string, unknown> };

type State = {
  // WS
  wsStatus: "idle" | "open" | "closed";
  setWsStatus: (s: "open" | "closed") => void;

  // 数据
  account: Account | null;
  positions: Position[];
  orders: Order[];
  quotes: Record<string, { price: number; ts: number }>;
  signals: Signal[];
  equityHistory: EquityPoint[];
  logs: LogEntry[];

  // 方法
  setAccount: (a: Account) => void;
  setPositions: (p: Position[]) => void;
  setOrders: (o: Order[]) => void;
  setSignals: (s: Signal[]) => void;
  setEquityHistory: (e: EquityPoint[]) => void;

  dispatch: (ev: WSLike) => void;
};

const MAX_LOGS = 200;
const MAX_SIGNALS = 200;
const MAX_EQUITY = 600;

export const useTradeStore = create<State>((set, get) => ({
  wsStatus: "idle",
  setWsStatus: (s) => set({ wsStatus: s }),

  account: null,
  positions: [],
  orders: [],
  quotes: {},
  signals: [],
  equityHistory: [],
  logs: [],

  setAccount: (a) => set({ account: a }),
  setPositions: (p) => set({ positions: p }),
  setOrders: (o) => set({ orders: o }),
  setSignals: (s) => set({ signals: s }),
  setEquityHistory: (e) => set({ equityHistory: e }),

  dispatch: (ev) => {
    switch (ev.type) {
      case "tick":
        set((s) => ({
          quotes: {
            ...s.quotes,
            [ev.data.symbol]: { price: ev.data.price, ts: ev.data.ts },
          },
        }));
        break;
      case "order_update": {
        // 把新订单 prepend，cap 到 100
        const orders = [ev.data, ...get().orders.filter((o) => o.order_id !== ev.data.order_id)];
        set({ orders: orders.slice(0, 100) });
        break;
      }
      case "equity_update": {
        const hist = [...get().equityHistory, ev.data].slice(-MAX_EQUITY);
        set({
          equityHistory: hist,
          account: get().account
            ? { ...get().account!, equity: ev.data.equity,
                cash: ev.data.cash, market_value: ev.data.market_value,
                daily_pnl: ev.data.daily_pnl }
            : null,
        });
        break;
      }
      case "signal": {
        const list = [ev.data, ...get().signals].slice(0, MAX_SIGNALS);
        set({ signals: list });
        break;
      }
      case "log": {
        const logs = [
          { level: ev.data.level, msg: ev.data.msg,
            ts: ev.data.ts, context: ev.data.context },
          ...get().logs,
        ].slice(0, MAX_LOGS);
        set({ logs });
        break;
      }
      case "pong":
        break;
    }
  },
}));
