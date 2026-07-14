# -*- coding: utf-8 -*-
"""
userstore.py — 用户数据 SQLite 持久层

管理自选列表、价格告警、投资组合、交易日志、策略参数等用户个性化数据。
数据库文件: data/userdata.db
线程安全: 所有写操作使用 threading.Lock 保护
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# 数据库路径
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
DB_PATH = os.path.join(_ROOT, "data", "userdata.db")

# SQL 建表语句
SCHEMA = """
-- 自选列表
CREATE TABLE IF NOT EXISTS watchlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    symbols TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 价格告警
CREATE TABLE IF NOT EXISTS price_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    condition TEXT NOT NULL,
    target_value REAL NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    triggered INTEGER NOT NULL DEFAULT 0,
    triggered_at TEXT,
    created_at TEXT NOT NULL,
    note TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_alerts_symbol ON price_alerts(symbol);

-- 投资组合持仓
CREATE TABLE IF NOT EXISTS portfolio_holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    name TEXT DEFAULT '',
    quantity REAL NOT NULL,
    avg_cost REAL NOT NULL,
    entry_date TEXT NOT NULL,
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 投资组合净值快照
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    total_value REAL NOT NULL,
    cash REAL DEFAULT 0,
    holdings_json TEXT DEFAULT '[]',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_snap_date ON portfolio_snapshots(date);

-- 交易日志
CREATE TABLE IF NOT EXISTS trade_journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    direction TEXT,
    entry_date TEXT,
    exit_date TEXT,
    entry_price REAL,
    exit_price REAL,
    quantity REAL,
    pnl REAL,
    pnl_pct REAL,
    tags TEXT DEFAULT '[]',
    notes TEXT DEFAULT '',
    rating INTEGER DEFAULT 0,
    screenshots TEXT DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_journal_symbol ON trade_journal(symbol);
CREATE INDEX IF NOT EXISTS idx_journal_date ON trade_journal(entry_date);

-- 策略自定义参数
CREATE TABLE IF NOT EXISTS strategy_params (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name TEXT NOT NULL UNIQUE,
    params_json TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL
);

-- 通用用户偏好（key-value）
CREATE TABLE IF NOT EXISTS user_prefs (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 术语表（后端维护，前端只读）
CREATE TABLE IF NOT EXISTS glossary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term TEXT NOT NULL UNIQUE,
    definition TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT '基础',
    created_at TEXT NOT NULL
);

-- 学习进度（记录每章的完成状态）
CREATE TABLE IF NOT EXISTS learning_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id TEXT NOT NULL UNIQUE,
    completed INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class UserStore:
    """用户数据存储：线程安全 SQLite CRUD"""

    def __init__(self, db_path: str = DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._db_path = db_path
        self._lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def _init_db(self):
        with self._lock:
            conn = self._get_conn()
            conn.executescript(SCHEMA)
            conn.commit()
        logger.info("userdata.db initialized at %s", self._db_path)

    # ==================================================================
    # 自选列表 CRUD
    # ==================================================================

    def watchlist_list(self) -> list[dict]:
        with self._lock:
            rows = self._get_conn().execute(
                "SELECT * FROM watchlists ORDER BY updated_at DESC"
            ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["symbols"] = json.loads(d.get("symbols", "[]"))
            result.append(d)
        return result

    def watchlist_get(self, list_id: int) -> Optional[dict]:
        with self._lock:
            row = self._get_conn().execute(
                "SELECT * FROM watchlists WHERE id=?", (list_id,)
            ).fetchone()
        if row is None:
            return None
        d = dict(row)
        d["symbols"] = json.loads(d.get("symbols", "[]"))
        return d

    def watchlist_create(self, name: str, symbols: list[str] = None) -> dict:
        now = _now()
        syms_json = json.dumps(symbols or [])
        with self._lock:
            cur = self._get_conn().execute(
                "INSERT INTO watchlists (name, symbols, created_at, updated_at) VALUES (?,?,?,?)",
                (name, syms_json, now, now),
            )
            self._get_conn().commit()
            list_id = cur.lastrowid
        return self.watchlist_get(list_id)

    def watchlist_update(self, list_id: int, name: str = None, symbols: list[str] = None) -> Optional[dict]:
        existing = self.watchlist_get(list_id)
        if existing is None:
            return None
        now = _now()
        new_name = name or existing["name"]
        new_syms = json.dumps(symbols if symbols is not None else existing["symbols"])
        with self._lock:
            self._get_conn().execute(
                "UPDATE watchlists SET name=?, symbols=?, updated_at=? WHERE id=?",
                (new_name, new_syms, now, list_id),
            )
            self._get_conn().commit()
        return self.watchlist_get(list_id)

    def watchlist_delete(self, list_id: int) -> bool:
        with self._lock:
            cur = self._get_conn().execute(
                "DELETE FROM watchlists WHERE id=?", (list_id,)
            )
            self._get_conn().commit()
            return cur.rowcount > 0

    # ==================================================================
    # 价格告警 CRUD
    # ==================================================================

    def alert_list(self) -> list[dict]:
        with self._lock:
            rows = self._get_conn().execute(
                "SELECT * FROM price_alerts ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def alert_get(self, alert_id: int) -> Optional[dict]:
        with self._lock:
            row = self._get_conn().execute(
                "SELECT * FROM price_alerts WHERE id=?", (alert_id,)
            ).fetchone()
        return dict(row) if row else None

    def alert_create(self, symbol: str, condition: str, target_value: float, note: str = "") -> dict:
        now = _now()
        with self._lock:
            cur = self._get_conn().execute(
                "INSERT INTO price_alerts (symbol, condition, target_value, created_at, note) VALUES (?,?,?,?,?)",
                (symbol.upper(), condition, target_value, now, note),
            )
            self._get_conn().commit()
            alert_id = cur.lastrowid
        return self.alert_get(alert_id)

    def alert_update(self, alert_id: int, **kwargs) -> Optional[dict]:
        allowed = {"symbol", "condition", "target_value", "enabled", "note"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return self.alert_get(alert_id)
        set_clause = ", ".join(f"{k}=?" for k in updates)
        values = list(updates.values()) + [alert_id]
        with self._lock:
            self._get_conn().execute(
                f"UPDATE price_alerts SET {set_clause} WHERE id=?", values
            )
            self._get_conn().commit()
        return self.alert_get(alert_id)

    def alert_delete(self, alert_id: int) -> bool:
        with self._lock:
            cur = self._get_conn().execute("DELETE FROM price_alerts WHERE id=?", (alert_id,))
            self._get_conn().commit()
            return cur.rowcount > 0

    def alert_ack(self, alert_id: int) -> bool:
        """确认已触发告警，重置 triggered 状态"""
        with self._lock:
            cur = self._get_conn().execute(
                "UPDATE price_alerts SET triggered=0, triggered_at=NULL WHERE id=?",
                (alert_id,),
            )
            self._get_conn().commit()
            return cur.rowcount > 0

    def alert_mark_triggered(self, alert_id: int) -> None:
        """标记告警已触发"""
        now = _now()
        with self._lock:
            self._get_conn().execute(
                "UPDATE price_alerts SET triggered=1, triggered_at=? WHERE id=?",
                (now, alert_id),
            )
            self._get_conn().commit()

    def alert_get_active(self) -> list[dict]:
        """获取所有启用且未触发的告警（供 ticker 检查用）"""
        with self._lock:
            rows = self._get_conn().execute(
                "SELECT * FROM price_alerts WHERE enabled=1 AND triggered=0"
            ).fetchall()
        return [dict(r) for r in rows]

    # ==================================================================
    # 投资组合 CRUD
    # ==================================================================

    def portfolio_holdings(self) -> list[dict]:
        with self._lock:
            rows = self._get_conn().execute(
                "SELECT * FROM portfolio_holdings ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def portfolio_add_holding(self, symbol: str, name: str, quantity: float,
                               avg_cost: float, entry_date: str = None, notes: str = "") -> dict:
        now = _now()
        entry = entry_date or now
        with self._lock:
            cur = self._get_conn().execute(
                """INSERT INTO portfolio_holdings
                   (symbol, name, quantity, avg_cost, entry_date, notes, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (symbol.upper(), name, quantity, avg_cost, entry, notes, now, now),
            )
            self._get_conn().commit()
            holding_id = cur.lastrowid
        row = self._get_conn().execute(
            "SELECT * FROM portfolio_holdings WHERE id=?", (holding_id,)
        ).fetchone()
        return dict(row)

    def portfolio_update_holding(self, holding_id: int, **kwargs) -> Optional[dict]:
        allowed = {"symbol", "name", "quantity", "avg_cost", "notes"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return None
        updates["updated_at"] = _now()
        set_clause = ", ".join(f"{k}=?" for k in updates)
        values = list(updates.values()) + [holding_id]
        with self._lock:
            self._get_conn().execute(
                f"UPDATE portfolio_holdings SET {set_clause} WHERE id=?", values
            )
            self._get_conn().commit()
        row = self._get_conn().execute(
            "SELECT * FROM portfolio_holdings WHERE id=?", (holding_id,)
        ).fetchone()
        return dict(row) if row else None

    def portfolio_delete_holding(self, holding_id: int) -> bool:
        with self._lock:
            cur = self._get_conn().execute(
                "DELETE FROM portfolio_holdings WHERE id=?", (holding_id,)
            )
            self._get_conn().commit()
            return cur.rowcount > 0

    def portfolio_snapshots(self, limit: int = 90) -> list[dict]:
        with self._lock:
            rows = self._get_conn().execute(
                "SELECT * FROM portfolio_snapshots ORDER BY date ASC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def portfolio_add_snapshot(self, total_value: float, cash: float = 0,
                                holdings_json: str = "[]") -> dict:
        now = _now()
        date_str = datetime.now().strftime("%Y-%m-%d")
        with self._lock:
            self._get_conn().execute(
                """INSERT OR REPLACE INTO portfolio_snapshots
                   (date, total_value, cash, holdings_json, created_at)
                   VALUES (?,?,?,?,?)""",
                (date_str, total_value, cash, holdings_json, now),
            )
            self._get_conn().commit()
        return {"date": date_str, "total_value": total_value, "cash": cash}

    # ==================================================================
    # 交易日志 CRUD
    # ==================================================================

    def journal_list(self, symbol: str = None, limit: int = 50) -> list[dict]:
        with self._lock:
            if symbol:
                rows = self._get_conn().execute(
                    "SELECT * FROM trade_journal WHERE symbol=? ORDER BY created_at DESC LIMIT ?",
                    (symbol.upper(), limit),
                ).fetchall()
            else:
                rows = self._get_conn().execute(
                    "SELECT * FROM trade_journal ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["tags"] = json.loads(d.get("tags", "[]"))
            result.append(d)
        return result

    def journal_create(self, **kwargs) -> dict:
        now = _now()
        allowed = ["symbol", "direction", "entry_date", "exit_date",
                   "entry_price", "exit_price", "quantity", "pnl", "pnl_pct",
                   "tags", "notes", "rating"]
        fields = {k: kwargs.get(k) for k in allowed if k in kwargs}
        fields["tags"] = json.dumps(fields.get("tags") or [])
        fields["created_at"] = now
        fields["updated_at"] = now
        columns = ", ".join(fields.keys())
        placeholders = ", ".join("?" for _ in fields)
        values = list(fields.values())
        with self._lock:
            cur = self._get_conn().execute(
                f"INSERT INTO trade_journal ({columns}) VALUES ({placeholders})", values
            )
            self._get_conn().commit()
            journal_id = cur.lastrowid
        row = self._get_conn().execute(
            "SELECT * FROM trade_journal WHERE id=?", (journal_id,)
        ).fetchone()
        d = dict(row)
        d["tags"] = json.loads(d.get("tags", "[]"))
        return d

    def journal_update(self, journal_id: int, **kwargs) -> Optional[dict]:
        allowed = ["symbol", "direction", "entry_date", "exit_date",
                   "entry_price", "exit_price", "quantity", "pnl", "pnl_pct",
                   "notes", "rating"]
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if "tags" in kwargs:
            updates["tags"] = json.dumps(kwargs["tags"])
        if not updates:
            return None
        updates["updated_at"] = _now()
        set_clause = ", ".join(f"{k}=?" for k in updates)
        values = list(updates.values()) + [journal_id]
        with self._lock:
            self._get_conn().execute(
                f"UPDATE trade_journal SET {set_clause} WHERE id=?", values
            )
            self._get_conn().commit()
        row = self._get_conn().execute(
            "SELECT * FROM trade_journal WHERE id=?", (journal_id,)
        ).fetchone()
        if row is None:
            return None
        d = dict(row)
        d["tags"] = json.loads(d.get("tags", "[]"))
        return d

    def journal_delete(self, journal_id: int) -> bool:
        with self._lock:
            cur = self._get_conn().execute(
                "DELETE FROM trade_journal WHERE id=?", (journal_id,)
            )
            self._get_conn().commit()
            return cur.rowcount > 0

    def journal_stats(self) -> dict:
        with self._lock:
            row = self._get_conn().execute("""
                SELECT
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) as losses,
                    SUM(pnl) as total_pnl,
                    AVG(pnl_pct) as avg_pnl_pct,
                    AVG(rating) as avg_rating
                FROM trade_journal
                WHERE pnl IS NOT NULL
            """).fetchone()
        if row is None:
            return {"total_trades": 0, "wins": 0, "losses": 0,
                    "total_pnl": 0, "avg_pnl_pct": 0, "avg_rating": 0}
        d = dict(row)
        total = d["total_trades"] or 0
        d["win_rate"] = round(d["wins"] / total * 100, 1) if total > 0 else 0
        return d

    # ==================================================================
    # 策略参数
    # ==================================================================

    def strategy_params_get(self, strategy_name: str) -> dict:
        with self._lock:
            row = self._get_conn().execute(
                "SELECT * FROM strategy_params WHERE strategy_name=?", (strategy_name,)
            ).fetchone()
        if row is None:
            return {"strategy_name": strategy_name, "params_json": "{}"}
        d = dict(row)
        d["params"] = json.loads(d.get("params_json", "{}"))
        return d

    def strategy_params_set(self, strategy_name: str, params: dict) -> dict:
        now = _now()
        params_json = json.dumps(params)
        with self._lock:
            self._get_conn().execute(
                """INSERT OR REPLACE INTO strategy_params
                   (strategy_name, params_json, updated_at) VALUES (?,?,?)""",
                (strategy_name, params_json, now),
            )
            self._get_conn().commit()
        return {"strategy_name": strategy_name, "params": params, "updated_at": now}

    # ==================================================================
    # 通用偏好
    # ==================================================================

    def pref_get(self, key: str) -> Optional[Any]:
        with self._lock:
            row = self._get_conn().execute(
                "SELECT value_json FROM user_prefs WHERE key=?", (key,)
            ).fetchone()
        return json.loads(row["value_json"]) if row else None

    def pref_set(self, key: str, value: Any) -> None:
        now = _now()
        value_json = json.dumps(value)
        with self._lock:
            self._get_conn().execute(
                "INSERT OR REPLACE INTO user_prefs (key, value_json, updated_at) VALUES (?,?,?)",
                (key, value_json, now),
            )
            self._get_conn().commit()

    # ==================================================================
    # 术语表 + 学习进度
    # ==================================================================

    def seed_glossary(self):
        """幂等插入术语表数据"""
        from webapp.backend.learning_content import GLOSSARY
        now = _now()
        with self._lock:
            conn = self._get_conn()
            for entry in GLOSSARY:
                conn.execute(
                    "INSERT OR IGNORE INTO glossary (term, definition, category, created_at) VALUES (?,?,?,?)",
                    (entry["term"], entry["definition"], entry["category"], now),
                )
            conn.commit()

    def glossary_list(self, category: str = None) -> list[dict]:
        with self._lock:
            if category:
                rows = self._get_conn().execute(
                    "SELECT * FROM glossary WHERE category=? ORDER BY term", (category,)
                ).fetchall()
            else:
                rows = self._get_conn().execute(
                    "SELECT * FROM glossary ORDER BY category, term"
                ).fetchall()
        return [dict(r) for r in rows]

    def glossary_search(self, query: str) -> list[dict]:
        with self._lock:
            rows = self._get_conn().execute(
                "SELECT * FROM glossary WHERE term LIKE ? OR definition LIKE ? ORDER BY term LIMIT 20",
                (f"%{query}%", f"%{query}%"),
            ).fetchall()
        return [dict(r) for r in rows]

    def learning_progress_list(self) -> list[dict]:
        with self._lock:
            rows = self._get_conn().execute(
                "SELECT * FROM learning_progress ORDER BY chapter_id"
            ).fetchall()
        return [dict(r) for r in rows]

    def learning_progress_mark(self, chapter_id: str) -> dict:
        now = _now()
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                """INSERT OR REPLACE INTO learning_progress
                   (chapter_id, completed, completed_at, created_at, updated_at)
                   VALUES (?, 1, ?, ?, ?)""",
                (chapter_id, now, now, now),
            )
            conn.commit()
        return {"chapter_id": chapter_id, "completed": True, "completed_at": now}

    def learning_progress_reset(self):
        with self._lock:
            self._get_conn().execute("DELETE FROM learning_progress")
            self._get_conn().commit()


__all__ = ["UserStore"]
