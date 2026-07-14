/**
 * KLineChart — TradingView Lightweight Charts v4
 *   跟 react-router 的 query 联动 symbol 切换
 *   使用 ResizeObserver 自适应父容器大小
 */

import { useEffect, useRef, useCallback } from "react";
import {
  createChart,
  ColorType,
  CrosshairMode,
} from "lightweight-charts";
import { api } from "../lib/api";

export function KLineChart({ symbol }: { symbol: string }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<any>(null);
  const candleSeries = useRef<any>(null);
  const volSeries = useRef<any>(null);

  // 初始化 chart（仅一次）
  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;

    const chart = createChart(container, {
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
      timeScale: {
        borderColor: "#1F222C",
        timeVisible: true,
        secondsVisible: true,
      },
    });
    chartRef.current = chart;

    // lightweight-charts v4 API: addCandlestickSeries / addHistogramSeries
    const cs = chart.addCandlestickSeries({
      upColor: "#10B981",
      downColor: "#F43F5E",
      wickUpColor: "#10B981",
      wickDownColor: "#F43F5E",
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

    // ResizeObserver 让 chart 自适应父容器
    const ro = new ResizeObserver(() => {
      const { width, height } = container.getBoundingClientRect();
      if (width > 0 && height > 0) {
        chart.applyOptions({ width, height });
      }
    });
    ro.observe(container);

    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
      candleSeries.current = null;
      volSeries.current = null;
    };
  }, []);

  // 切换 symbol 时加载新数据
  const loadData = useCallback(async (sym: string) => {
    if (!candleSeries.current) return;
    try {
      const ohlc = await api.ohlc(sym, 300);
      // 时间戳兼容：mock 返回秒级(10位)，real 返回毫秒级(13位)，统一转为秒
      const toSeconds = (t: number) => t > 1e12 ? Math.floor(t / 1000) : t;
      const candleData = ohlc.map((c) => ({
        time: toSeconds(c.t) as any,
        open: c.o,
        high: c.h,
        low: c.l,
        close: c.c,
      }));
      const volData = ohlc.map((c) => ({
        time: toSeconds(c.t) as any,
        value: c.v,
        color:
          c.c >= c.o
            ? "rgba(16,185,129,0.45)"
            : "rgba(244,63,94,0.45)",
      }));

      candleSeries.current.setData(candleData);
      volSeries.current.setData(volData);
      chartRef.current?.timeScale().fitContent();
    } catch (e) {
      console.warn("ohlc load failed:", e);
    }
  }, []);

  useEffect(() => {
    loadData(symbol);
  }, [symbol, loadData]);

  return (
    <div
      ref={containerRef}
      className="w-full h-full rounded-lg border border-line"
    />
  );
}
