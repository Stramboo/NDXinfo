/**
 * useWS — 订阅后端 WebSocket 事件（指数退避自动重连 + 心跳）
 */

import { useEffect, useRef } from "react";
import { useTradeStore, type WSLike } from "../store/tradeStore";

const WS_URL =
  (import.meta as any).env?.VITE_WS_URL ??
  (() => {
    const scheme = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${scheme}//${window.location.host}/ws`;
  })();

/** 指数退避参数 */
const INITIAL_BACKOFF = 1500;
const MAX_BACKOFF = 30_000;
const BACKOFF_MULTIPLIER = 1.5;

export function useWS() {
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    let backoff = INITIAL_BACKOFF;
    let ws: WebSocket;
    let heartbeat: ReturnType<typeof setInterval> | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    const cleanup = () => {
      if (heartbeat) { clearInterval(heartbeat); heartbeat = null; }
      if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
    };

    const connect = () => {
      // 如果组件已卸载，停止重连
      if (!mountedRef.current) return;

      cleanup();
      const store = useTradeStore.getState();
      store.setWsStatus("idle");

      ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        if (!mountedRef.current) { ws.close(); return; }
        backoff = INITIAL_BACKOFF; // 连接成功，重置退避
        store.setWsStatus("open");
        heartbeat = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send("PING");
        }, 15_000);
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;
        store.setWsStatus("closed");
        cleanup();
        // 指数退避重连
        reconnectTimer = setTimeout(() => {
          backoff = Math.min(backoff * BACKOFF_MULTIPLIER, MAX_BACKOFF);
          connect();
        }, backoff);
      };

      ws.onerror = () => {
        // onclose 一定会紧接着触发，不做额外处理
      };

      ws.onmessage = (e) => {
        let ev: WSLike;
        try { ev = JSON.parse(e.data); } catch { return; }
        useTradeStore.getState().dispatch(ev);
      };
    };

    connect();

    return () => {
      mountedRef.current = false;
      cleanup();
      if (ws) { ws.onclose = null; ws.close(); }
    };
  }, []);
}
