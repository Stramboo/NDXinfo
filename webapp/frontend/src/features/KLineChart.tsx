/**
 * KLineChart — TradingView Lightweight Charts v4
 *   跟 react-router 的 query 联动 symbol 切换
 */

import { useEffect, useRef } from "react";
import {
  createChart,
  ColorType,
  CrosshairMode,
} from "lightweight-charts";
import { api } from "../lib/api";

export function KLineChart({ symbol }: { symbol: string }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef     = useRef<any>(null);
  const candleSeries = useRef<any>(null);
  const volSeries    = useRef<any>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "#101218" },
        textColor: "#8A93A4",
      },
      grid: {
        vertLines: { color: "#1F222C" },
        horzLines: { color: "#1F222C" },
      },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: "#1F222C" },
      timeScale: { borderColor: "#1F222C", timeVisible: true, secondsVisible: true },
    });
    chartRef.current = chart;

    // lightweight-charts v4 API: addCandlestickSeries / addHistogramSeries
    const cs = chart.addCandlestickSeries({
      upColor: "#10B981", downColor: "#F43F5E",
      wickUpColor: "#10B981", wickDownColor: "#F43F5E",
      borderVisible: false,
    });
    candleSeries.current = cs;

    const vs = chart.addHistogramSeries({
      color: "#1F222C",
      priceFormat: { type: "volume" },
      priceScaleId: "",
    });
    vs.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });
    volSeries.current = vs;

    return () => {
      chart.remove();
      chartRef.current = null;
      candleSeries.current = null;
      volSeries.current = null;
    };
  }, []);

  useEffect(() => {
    if (!candleSeries.current) return;
    (async () => {
      try {
        const ohlc = await api.ohlc(symbol, 300);
        candleSeries.current.setData(
          ohlc.map((c) => ({
            time: Math.floor(c.t / 1000),
            open: c.o, high: c.h, low: c.l, close: c.c,
          }))
        );
        volSeries.current.setData(
          ohlc.map((c) => ({
            time: Math.floor(c.t / 1000),
            value: c.v,
            color: c.c >= c.o ? "rgba(16,185,129,0.45)" : "rgba(244,63,94,0.45)",
          }))
        );
        chartRef.current?.timeScale().fitContent();
      } catch (e) {
        console.warn("ohlc load failed:", e);
      }
    })();
  }, [symbol]);

  return (
    <div
      ref={containerRef}
      className="rounded-lg border border-line"
      style={{ height: 460 }}
    />
  );
}
