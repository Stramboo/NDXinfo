# -*- coding: utf-8 -*-
"""
SQLite 持久层（SQLiteStore）

把订单 / 信号 / 权益快照 / 错误日志落盘，便于事后分析。

表结构:
    orders           —— 下单与成交事件
    signals          —— 策略信号事件
    equity_snapshots —— 每 tick 资产快照
    errors           —— 异常 / 拦截记录

CLI: python -m trading.persistence stats
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Any, Optional


class SQLiteStore:
    """轻量 SQLite 持久化（线程安全）"""

    SCHEMA_SQL = """
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL,
        order_id TEXT,
        symbol TEXT NOT NULL,
        side TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL,
        commission REAL,
        slippage_bps REAL,
        status TEXT,
        rejection_code INTEGER DEFAULT 0,
        note TEXT DEFAULT '',
        strategy_name TEXT DEFAULT '',
        signal_reason TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL,
        symbol TEXT NOT NULL,
        strategy TEXT,
        action TEXT,
        strength REAL,
        reason TEXT,
        executed INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS equity_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL,
        equity REAL,
        cash REAL,
        market_value REAL,
        daily_pnl REAL
    );
    CREATE TABLE IF NOT EXISTS errors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL,
        level TEXT,
        module TEXT,
        msg TEXT,
        traceback TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol);
    CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol);
    CREATE INDEX IF NOT EXISTS idx_orders_ts ON orders(ts);
    """

    def __init__(self, db_path: str = "data/trader.db"):
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.db_path = db_path
        self._lock = threading.Lock()
        # check_same_thread=False 以支持多线程写；外层串行化由锁保证
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        with self._lock:
            self._conn.executescript(self.SCHEMA_SQL)
            self._conn.commit()

    # ---------- 写入 ----------

    def insert_order(self, **kwargs) -> int:
        ts = kwargs.pop("ts", None) or datetime.now().isoformat(timespec="seconds")
        keys = ["ts"] + list(kwargs.keys())
        qms = ",".join(["?"] * len(keys))
        sql = f"INSERT INTO orders ({','.join(keys)}) VALUES ({qms})"
        with self._lock:
            cur = self._conn.execute(sql, [ts] + list(kwargs.values()))
            self._conn.commit()
            return cur.lastrowid

    def insert_signal(self, **kwargs) -> int:
        ts = kwargs.pop("ts", None) or datetime.now().isoformat(timespec="seconds")
        keys = ["ts"] + list(kwargs.keys())
        qms = ",".join(["?"] * len(keys))
        sql = f"INSERT INTO signals ({','.join(keys)}) VALUES ({qms})"
        with self._lock:
            cur = self._conn.execute(sql, [ts] + list(kwargs.values()))
            self._conn.commit()
            return cur.lastrowid

    def insert_equity_snapshot(self, **kwargs) -> int:
        ts = kwargs.pop("ts", None) or datetime.now().isoformat(timespec="seconds")
        keys = ["ts"] + list(kwargs.keys())
        qms = ",".join(["?"] * len(keys))
        sql = f"INSERT INTO equity_snapshots ({','.join(keys)}) VALUES ({qms})"
        with self._lock:
            cur = self._conn.execute(sql, [ts] + list(kwargs.values()))
            self._conn.commit()
            return cur.lastrowid

    def insert_error(self, **kwargs) -> int:
        ts = kwargs.pop("ts", None) or datetime.now().isoformat(timespec="seconds")
        keys = ["ts"] + list(kwargs.keys())
        qms = ",".join(["?"] * len(keys))
        sql = f"INSERT INTO errors ({','.join(keys)}) VALUES ({qms})"
        with self._lock:
            cur = self._conn.execute(sql, [ts] + list(kwargs.values()))
            self._conn.commit()
            return cur.lastrowid

    # ---------- 读取 / 统计 ----------

    def table_counts(self) -> dict[str, int]:
        out = {}
        with self._lock:
            for t in ("orders", "signals", "equity_snapshots", "errors"):
                cur = self._conn.execute(f"SELECT COUNT(*) FROM {t}")
                out[t] = cur.fetchone()[0]
        return out

    def db_size_mb(self) -> float:
        try:
            return round(os.path.getsize(self.db_path) / 1024 / 1024, 4)
        except OSError:
            return 0.0

    def stats_24h(self) -> dict:
        """24h 错误分布与最近 tick 耗时"""
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat(timespec="seconds")
        with self._lock:
            err_rows = self._conn.execute(
                "SELECT level, COUNT(*) FROM errors WHERE ts > ? GROUP BY level",
                (cutoff,),
            ).fetchall()
            eq_rows = self._conn.execute(
                "SELECT COUNT(*) FROM equity_snapshots WHERE ts > ?",
                (cutoff,),
            ).fetchone()
        return {
            "errors_by_level_24h": {lvl or "?": cnt for lvl, cnt in err_rows},
            "snapshots_24h": eq_rows[0] if eq_rows else 0,
        }

    def close(self) -> None:
        with self._lock:
            self._conn.close()


def main(argv: Optional[list[str]] = None) -> int:
    """python -m trading.persistence stats"""
    import argparse
    parser = argparse.ArgumentParser(prog="python -m trading.persistence")
    parser.add_argument(
        "command", nargs="?", default="stats",
        choices=["stats", "tables"],
        help="stats=统计  tables=列出表与行数",
    )
    parser.add_argument("--db", default="data/trader.db")
    args = parser.parse_args(argv)

    store = SQLiteStore(args.db)
    if args.command == "tables":
        counts = store.table_counts()
        print(json.dumps(counts, indent=2, ensure_ascii=False))
    else:
        counts = store.table_counts()
        s24 = store.stats_24h()
        print(json.dumps({
            "tables": counts,
            "db_size_mb": store.db_size_mb(),
            "24h": s24,
        }, indent=2, ensure_ascii=False))
    store.close()
    return 0


__all__ = ["SQLiteStore", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
