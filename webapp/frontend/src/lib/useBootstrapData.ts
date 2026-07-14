/**
 * useBootstrapData — 启动时拉一次初始数据，配合 WS 增量更新
 */

import { useEffect } from "react";
import { useTradeStore } from "../store/tradeStore";
import { api } from "./api";

export function useBootstrapData() {
  const setAccount       = useTradeStore((s) => s.setAccount);
  const setPositions     = useTradeStore((s) => s.setPositions);
  const setOrders        = useTradeStore((s) => s.setOrders);
  const setSignals       = useTradeStore((s) => s.setSignals);
  const setEquityHistory = useTradeStore((s) => s.setEquityHistory);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      const [a, p, o, s, e] = await Promise.all([
        api.account(),
        api.positions(),
        api.orders(100),
        api.signals(100),
        api.equity(400),
      ]);
      if (cancelled) return;
      setAccount(a);
      setPositions(p);
      setOrders(o);
      setSignals(s);
      setEquityHistory(e);
    })().catch((err) => {
      console.warn("bootstrap failed:", err);
    });

    return () => { cancelled = true; };
  }, [setAccount, setPositions, setOrders, setSignals, setEquityHistory]);
}
