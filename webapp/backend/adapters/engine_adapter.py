# -*- coding: utf-8 -*-
"""
engine_adapter.py — 把现有 trading/TradingEngine 包进 FastAPI 的 Facade

- 保留 TradingEngine 的全部业务逻辑（broker、strategy、risk、executor）
- 把 TradingEngine 的事件（signal / status / log）通过 EventBus 推给 WS
- 同步方法（account / positions / orders / place_order）包装成 async 兼容

注意：
- 默认 broker_type='simulation'；传入 alpaca/paper 时需要在 config 里加 API key
- 不动 TradingEngine 内部任何代码；只在外层做事件桥 + 字段适配
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)


class EngineAdapter:
    """TradingEngine 的薄壳：同步调用 + 事件回调"""

    def __init__(self, broker_type: str = "simulation", strategy_name: str = "multi",
                 initial_cash: float = 100_000, bus=None):
        self._bus = bus
        self.broker_type = broker_type
        self.strategy_name = strategy_name
        self.initial_cash = initial_cash
        self._engine = None
        self._init_engine()

    def _init_engine(self):
        from trading.trading_engine import TradingEngine
        # 重要：把 TradingEngine 的 callback 装好
        self._engine = TradingEngine(
            broker_type=self.broker_type,
            strategy_name=self.strategy_name,
            initial_cash=self.initial_cash,
        )
        self._engine.on_signal(self._on_signal)
        self._engine.on_status_changed(self._on_status)
        self._engine.on_log(self._on_log)

    # ---------- 账户 / 持仓 / 订单 ----------

    def account(self) -> dict:
        acc = self._engine.broker.get_account()
        return {
            "cash": round(acc.cash, 2),
            "equity": round(acc.equity, 2),
            "settled_cash": round(getattr(acc, "settled_cash", acc.cash), 2),
            "market_value": round(acc.equity - acc.cash, 2),
            "total_return_pct": round((acc.equity / self.initial_cash - 1.0) * 100.0, 4),
            "daily_pnl": round(getattr(acc, "daily_pnl", 0.0), 2),
            "positions": len(self._engine.broker.get_positions()),
        }

    def positions(self) -> list[dict]:
        return self.positions_list()

    def positions_list(self) -> list[dict]:
        out = []
        for p in self._engine.broker.get_positions():
            last_price = self._broker_price(p.symbol) or p.avg_cost
            mv = round(last_price * p.quantity, 2)
            pnl = round((last_price - p.avg_cost) * p.quantity, 2)
            pct = round((last_price / p.avg_cost - 1.0) * 100.0, 4) if p.avg_cost else 0.0
            out.append({
                "symbol": p.symbol,
                "quantity": p.quantity,
                "avg_cost": round(p.avg_cost, 4),
                "last_price": round(last_price, 2),
                "market_value": mv,
                "unrealized_pnl": pnl,
                "unrealized_pnl_pct": pct,
            })
        return out

    def orders(self, limit: int = 50) -> list[dict]:
        return self.orders_list(limit=limit)

    def orders_list(self, limit: int = 50) -> list[dict]:
        out = []
        try:
            history = self._engine.executor.get_order_history(limit=limit) or []
        except Exception:
            history = []
        for o in history[::-1]:
            out.append({
                "order_id": getattr(o, "order_id", ""),
                "symbol": o.symbol,
                "side": o.side,
                "quantity": o.quantity,
                "avg_fill_price": round(getattr(o, "avg_fill_price", o.price or 0), 4),
                "commission": round(getattr(o, "commission", 0.0), 2),
                "status": getattr(o, "status", "filled"),
                "note": getattr(o, "note", "") or "",
                "rejection_code": int(getattr(o, "rejection_code", 0) or 0),
                "ts": int(time.time() * 1000),
            })
        return out

    def signal_log(self, limit: int = 50) -> list[dict]:
        # real 引擎的 signals 暂时由 EventBus 缓存（这里返回空，由前端从 store 读）
        return []

    # ---------- 行情 ----------

    def symbols(self) -> list[str]:
        try:
            return list(self._engine.market_data.get_symbols())
        except Exception:
            return []

    @property
    def prices(self) -> dict[str, float]:
        out = {}
        for s in self.symbols():
            p = self._broker_price(s)
            if p > 0: out[s] = p
        return out

    def quote(self, symbol: str) -> dict:
        sym = symbol.upper()
        return {"symbol": sym, "price": self._broker_price(sym) or 0.0,
                "ts": int(time.time() * 1000)}

    def ohlc(self, symbol: str, interval: str = "1m", limit: int = 200) -> list[dict]:
        sym = symbol.upper()
        try:
            df = self._engine.market_data.fetch_history(sym, period="6mo")
        except Exception:
            df = None
        if df is None or len(df) == 0:
            return []
        df = df.tail(limit)
        out = []
        for idx, r in df.iterrows():
            try:
                t = int(idx.timestamp() * 1000) if hasattr(idx, "timestamp") else int(time.time()*1000)
            except Exception:
                t = int(time.time() * 1000)
            out.append({
                "t": t,
                "o": float(r["Open"]), "h": float(r["High"]),
                "l": float(r["Low"]),  "c": float(r["Close"]),
                "v": int(r.get("Volume", 0) or 0),
            })
        return out

    def start_time(self) -> float:
        # mock engine 有 start_time；real 引擎取 process start
        return getattr(self, "_start_time", time.time())

    # 让 mock / real 接口完全对齐
    @property
    def equity_history(self) -> list[dict]:
        # real 引擎暂时没有本地缓存 equity（实盘接 broker 后会拉真实 PnL）
        # 前端会自己用 equity_update 增量构建
        return []

    # ---------- 下单 ----------

    def place_order(self, symbol: str, side: str, quantity: int,
                    order_type: str = "MARKET",
                    limit_price: Optional[float] = None) -> dict:
        if side.upper() == "BUY":
            o = self._engine.manual_buy(symbol, quantity)
        else:
            o = self._engine.manual_sell(symbol, quantity)
        d = self._order_to_dict(o)
        if self._bus is not None:
            try:
                # 在 event loop 里 publish
                self._bus.publish_threadsafe({"type": "order_update", "data": d})
            except Exception:
                pass
        return d

    def to_dict(self) -> dict:
        """让 server 端用 .to_dict() 时返回 account 形态（兼容 MockEngine 接口）"""
        return self.account()

    # ---------- 自动 / 状态 ----------

    def start_auto(self, interval: int = 30) -> None:
        self._engine.start_auto(interval_seconds=interval)

    def stop_auto(self) -> None:
        self._engine.stop_auto()

    def status(self) -> dict:
        try:
            return self._engine.get_status()
        except Exception as e:
            return {"error": str(e)}

    def strategy_info(self) -> dict:
        s = self._engine.strategy
        return {
            "name": getattr(s, "name", "multi"),
            "weights": getattr(s, "weights", {"multi": 1.0}),
            "available": [
                "multi", "macd", "rsi", "ma_trend", "bollinger",
                "kdj", "boll_width", "ensemble",
            ],
        }

    def limits(self) -> dict:
        rm = self._engine.risk_manager
        lim = getattr(rm, "limits", None) or {}
        return {
            "max_position_pct": getattr(lim, "max_position_pct", 0.25),
            "stop_loss_pct": getattr(lim, "stop_loss_pct", -0.08),
            "trailing_stop_pct": getattr(lim, "trailing_pct", -0.05),
            "max_daily_trades": getattr(lim, "max_daily_trades", 20),
            "use_atr_stop": getattr(lim, "use_atr_stop", False),
        }

    # ---------- 内部 ----------

    def _broker_price(self, symbol: str) -> float:
        try:
            quote = self._engine.broker.get_quote(symbol)
            if quote and getattr(quote, "last", None):
                return float(quote.last)
            # 没 quote 就用 market_data 的最后价
            price = self._engine.market_data.get_price(symbol)
            return float(price or 0.0)
        except Exception:
            return 0.0

    def _order_to_dict(self, o) -> dict:
        price = getattr(o, "avg_fill_price", None) or getattr(o, "price", 0) or 0
        return {
            "order_id": getattr(o, "order_id", ""),
            "symbol": o.symbol,
            "side": o.side,
            "quantity": o.quantity,
            "avg_fill_price": round(float(price), 4),
            "commission": round(getattr(o, "commission", 0.0), 2),
            "status": getattr(o, "status", "filled"),
            "note": getattr(o, "note", "") or "",
            "rejection_code": int(getattr(o, "rejection_code", 0) or 0),
            "ts": int(time.time() * 1000),
        }

    def _on_signal(self, signal) -> None:
        if self._bus is None: return
        d = {
            "symbol": signal.symbol, "action": signal.action,
            "strength": getattr(signal, "strength", 0.5),
            "reason": getattr(signal, "reason", ""),
            "ts": int(time.time() * 1000),
        }
        self._bus.publish_threadsafe({"type": "signal", "data": d})

    def _on_status(self, status: dict) -> None:
        if self._bus is None: return
        self._bus.publish_threadsafe({"type": "status", "data": status})

    def _on_log(self, msg: str) -> None:
        if self._bus is None: return
        self._bus.publish_threadsafe({
            "type": "log",
            "data": {"level": "INFO", "msg": str(msg),
                     "ts": int(time.time() * 1000)},
        })


__all__ = ["EngineAdapter"]
