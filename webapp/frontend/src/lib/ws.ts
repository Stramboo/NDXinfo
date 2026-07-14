/**
 * useWS — 订阅后端 WebSocket 事件（自动重连 + 心跳）
 */

import { useEffect } from "react";
import { useTradeStore, type WSLike } from "../store/tradeStore";

const WS_URL =
  (import.meta as any).env?.VITE_WS_URL
  ?? (() => {
    const scheme = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${scheme}//${window.location.host}/ws`;
  })();

function connect() {
  const ws = new WebSocket(WS_URL);
  const store = useTradeStore.getState();

  ws.onopen = () => {
    store.setWsStatus("open");
    // heartbeat
    const heartbeat = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send("PING");
    }, 15_000);
    (ws as any)._heartbeat = heartbeat;
  };

  ws.onclose = () => {
    store.setWsStatus("closed");
    clearInterval((ws as any)._heartbeat);
    // simple reconnect with backoff
    setTimeout(connect, 1500);
  };

  ws.onerror = () => store.setWsStatus("closed");
  ws.onmessage = (e) => {
    let ev: WSLike;
    try { ev = JSON.parse(e.data); } catch { return; }
    useTradeStore.getState().dispatch(ev);
  };
  return ws;
}

export function useWS() {
  useEffect(() => {
    const ws = connect();
    return () => {
      ws.close();
    };
  }, []);
}
