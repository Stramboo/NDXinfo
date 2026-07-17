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

-- 任务完成记录
CREATE TABLE IF NOT EXISTS quest_progress (
    quest_id TEXT PRIMARY KEY,
    completed INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT
);

-- 学习 XP 积分（单行记录）
CREATE TABLE IF NOT EXISTS learning_stats (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    total_xp INTEGER NOT NULL DEFAULT 0,
    streak_days INTEGER NOT NULL DEFAULT 0,
    last_active_date TEXT,
    updated_at TEXT NOT NULL
);

-- 沙盒交易账户
CREATE TABLE IF NOT EXISTS sandbox_account (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    cash REAL NOT NULL DEFAULT 100000,
    initial_cash REAL NOT NULL DEFAULT 100000,
    updated_at TEXT NOT NULL
);

-- 沙盒持仓
CREATE TABLE IF NOT EXISTS sandbox_positions (
    symbol TEXT PRIMARY KEY,
    quantity REAL NOT NULL,
    avg_cost REAL NOT NULL
);

-- 沙盒订单历史
CREATE TABLE IF NOT EXISTS sandbox_orders (
    order_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    ts INTEGER NOT NULL
);

-- 现金账本（每一笔现金变动可追溯）
CREATE TABLE IF NOT EXISTS cash_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT,
    entry_type TEXT NOT NULL,    -- 'BUY', 'SELL', 'COMMISSION', 'TRANSFER'
    amount REAL NOT NULL,         -- 正=入金, 负=出金
    balance_after REAL NOT NULL,
    created_at TEXT NOT NULL
);

-- 交易计划（下单前必填）
CREATE TABLE IF NOT EXISTS trade_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL,        -- 'long'/'short'
    reason TEXT NOT NULL,
    plan_type TEXT DEFAULT 'quick', -- 'quick'/'detailed'
    entry_price REAL,
    target_price REAL,
    stop_loss_price REAL,
    max_loss_pct REAL,
    position_pct REAL,
    planned_holding TEXT,
    created_at TEXT NOT NULL
);

-- 交易复盘记录 (v2.4)
CREATE TABLE IF NOT EXISTS trade_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity REAL,
    price REAL,
    pnl REAL,
    pnl_pct REAL,
    holding_days REAL,
    score REAL,
    mistakes_json TEXT DEFAULT '[]',
    summary TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_reviews_trade ON trade_reviews(trade_id);

-- AI 教练对话历史 (v2.4)
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,               -- 'user' / 'assistant'
    message TEXT NOT NULL,
    qtype TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

-- XP 流水 (v2.4) — 幂等键 (source, source_id)
CREATE TABLE IF NOT EXISTS xp_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    source_id TEXT DEFAULT '',
    amount INTEGER NOT NULL,
    total_after INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_xp_log_source ON xp_log(source, source_id);

-- 每日活跃打卡 (v2.4)
CREATE TABLE IF NOT EXISTS daily_checkins (
    date TEXT PRIMARY KEY,            -- YYYY-MM-DD
    xp_earned INTEGER DEFAULT 0,
    lessons_done INTEGER DEFAULT 0,
    trades_done INTEGER DEFAULT 0,
    reviews_done INTEGER DEFAULT 0,
    explores_done INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 沙盒净值快照 (v2.4)
CREATE TABLE IF NOT EXISTS sandbox_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER NOT NULL,
    equity REAL NOT NULL,
    cash REAL NOT NULL,
    market_value REAL NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sandbox_snap_ts ON sandbox_snapshots(ts);

-- 测验/考试成绩 (v2.4)
CREATE TABLE IF NOT EXISTS quiz_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id TEXT NOT NULL,
    quiz_type TEXT NOT NULL,          -- 'lesson_quiz' / 'stage_exam'
    score INTEGER NOT NULL,
    correct_count INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    passed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
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

    # ---- 任务进度 ----

    def quest_list(self) -> list[dict]:
        with self._lock:
            rows = self._get_conn().execute(
                "SELECT * FROM quest_progress ORDER BY quest_id"
            ).fetchall()
        return [dict(r) for r in rows]

    def quest_is_completed(self, quest_id: str) -> bool:
        with self._lock:
            row = self._get_conn().execute(
                "SELECT completed FROM quest_progress WHERE quest_id=?", (quest_id,)
            ).fetchone()
        return row is not None and row[0] == 1

    def quest_mark_completed(self, quest_id: str):
        now = _now()
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                """INSERT OR REPLACE INTO quest_progress (quest_id, completed, completed_at)
                   VALUES (?, 1, ?)""",
                (quest_id, now),
            )
            conn.commit()

    def quest_progress_reset(self):
        with self._lock:
            self._get_conn().execute("DELETE FROM quest_progress")
            self._get_conn().commit()

    # ---- 学习统计 ----

    def _ensure_learning_stats(self):
        """确保 learning_stats 有初始化记录"""
        now = _now()
        with self._lock:
            self._get_conn().execute(
                """INSERT OR IGNORE INTO learning_stats (id, total_xp, streak_days, last_active_date, updated_at)
                   VALUES (1, 0, 0, NULL, ?)""",
                (now,),
            )
            self._get_conn().commit()

    def get_learning_stats(self) -> dict:
        self._ensure_learning_stats()
        with self._lock:
            row = self._get_conn().execute(
                "SELECT * FROM learning_stats WHERE id=1"
            ).fetchone()
        return dict(row) if row else {"total_xp": 0, "streak_days": 0, "last_active_date": None}

    def add_xp(self, amount: int):
        self._ensure_learning_stats()
        now = _now()
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                "UPDATE learning_stats SET total_xp = total_xp + ?, updated_at = ? WHERE id = 1",
                (amount, now),
            )
            conn.commit()
        return self.get_learning_stats()["total_xp"]

    def update_streak(self) -> int:
        """更新连续学习天数，返回当前 streak"""
        from datetime import datetime as dt
        self._ensure_learning_stats()
        today = dt.now().strftime("%Y-%m-%d")
        with self._lock:
            row = self._get_conn().execute(
                "SELECT last_active_date, streak_days FROM learning_stats WHERE id=1"
            ).fetchone()
            last_date = row[0] if row else None
            current_streak = row[1] if row else 0

            if last_date == today:
                return current_streak  # 今天已记录

            from datetime import timedelta
            yesterday = (dt.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            if last_date == yesterday:
                current_streak += 1
            elif last_date != today:
                current_streak = 1

            now = _now()
            self._get_conn().execute(
                "UPDATE learning_stats SET streak_days=?, last_active_date=?, updated_at=? WHERE id=1",
                (current_streak, today, now),
            )
            self._get_conn().commit()
        return current_streak

    # ---- 交易计划 ----

    def trade_plan_create(self, symbol: str, direction: str, reason: str,
                          entry_price: float = None, target_price: float = None,
                          stop_loss_price: float = None, max_loss_pct: float = None,
                          position_pct: float = None, planned_holding: str = None) -> dict:
        now = _now()
        with self._lock:
            cur = self._get_conn().execute(
                """INSERT INTO trade_plans (symbol, direction, reason, entry_price,
                   target_price, stop_loss_price, max_loss_pct, position_pct,
                   planned_holding, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (symbol.upper(), direction, reason, entry_price, target_price,
                 stop_loss_price, max_loss_pct, position_pct, planned_holding, now),
            )
            self._get_conn().commit()
            plan_id = cur.lastrowid
        return {"id": plan_id, "symbol": symbol.upper(), "direction": direction, "created_at": now}

    def trade_plan_list(self, limit: int = 20) -> list[dict]:
        with self._lock:
            rows = self._get_conn().execute(
                "SELECT * FROM trade_plans ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [{
            "id": r[0], "symbol": r[1], "direction": r[2], "reason": r[3],
            "plan_type": r[4], "entry_price": r[5], "target_price": r[6],
            "stop_loss_price": r[7], "max_loss_pct": r[8], "position_pct": r[9],
            "planned_holding": r[10], "created_at": r[11],
        } for r in rows]

    # ---- 沙盒交易 ----

    def _ensure_sandbox_account(self):
        now = _now()
        with self._lock:
            self._get_conn().execute(
                """INSERT OR IGNORE INTO sandbox_account (id, cash, initial_cash, updated_at)
                   VALUES (1, 100000, 100000, ?)""",
                (now,),
            )
            self._get_conn().commit()

    def sandbox_get(self) -> dict:
        self._ensure_sandbox_account()
        with self._lock:
            row = self._get_conn().execute(
                "SELECT * FROM sandbox_account WHERE id=1"
            ).fetchone()
            pos_rows = self._get_conn().execute(
                "SELECT * FROM sandbox_positions"
            ).fetchall()
        return {
            "cash": row[1],
            "initial_cash": row[2],
            "positions": [{"symbol": r[0], "quantity": r[1], "avg_cost": r[2]} for r in pos_rows],
        }

    def sandbox_buy(self, symbol: str, quantity: int, price: float, order_id: str, ts: int):
        self._ensure_sandbox_account()
        cost = quantity * price
        now = _now()
        with self._lock:
            conn = self._get_conn()
            # 扣款
            conn.execute(
                "UPDATE sandbox_account SET cash = cash - ?, updated_at = ? WHERE id = 1 AND cash >= ?",
                (cost, now, cost),
            )
            # 现金账本
            balance = conn.execute("SELECT cash FROM sandbox_account WHERE id=1").fetchone()
            conn.execute(
                "INSERT INTO cash_ledger (order_id, entry_type, amount, balance_after, created_at) VALUES (?,?,?,?,?)",
                (order_id, "BUY", -cost, float(balance[0]) if balance else 0, now),
            )
            # 更新持仓
            existing = conn.execute(
                "SELECT quantity, avg_cost FROM sandbox_positions WHERE symbol=?", (symbol,)
            ).fetchone()
            if existing:
                total_qty = existing[0] + quantity
                total_cost = existing[0] * existing[1] + cost
                new_avg = total_cost / total_qty
                conn.execute(
                    "UPDATE sandbox_positions SET quantity=?, avg_cost=? WHERE symbol=?",
                    (total_qty, new_avg, symbol),
                )
            else:
                conn.execute(
                    "INSERT INTO sandbox_positions (symbol, quantity, avg_cost) VALUES (?,?,?)",
                    (symbol, quantity, price),
                )
            # 记录订单
            conn.execute(
                "INSERT OR REPLACE INTO sandbox_orders (order_id, symbol, side, quantity, price, ts) VALUES (?,?,?,?,?,?)",
                (order_id, symbol, "BUY", quantity, price, ts),
            )
            conn.commit()

    def sandbox_sell(self, symbol: str, quantity: int, price: float, order_id: str, ts: int):
        self._ensure_sandbox_account()
        revenue = quantity * price
        now = _now()
        with self._lock:
            conn = self._get_conn()
            # 加钱
            conn.execute(
                "UPDATE sandbox_account SET cash = cash + ?, updated_at = ? WHERE id = 1",
                (revenue, now),
            )
            # 现金账本
            balance = conn.execute("SELECT cash FROM sandbox_account WHERE id=1").fetchone()
            conn.execute(
                "INSERT INTO cash_ledger (order_id, entry_type, amount, balance_after, created_at) VALUES (?,?,?,?,?)",
                (order_id, "SELL", revenue, float(balance[0]) if balance else 0, now),
            )
            # 更新持仓
            existing = conn.execute(
                "SELECT quantity FROM sandbox_positions WHERE symbol=?", (symbol,)
            ).fetchone()
            if existing:
                remaining = existing[0] - quantity
                if remaining <= 0:
                    conn.execute("DELETE FROM sandbox_positions WHERE symbol=?", (symbol,))
                else:
                    conn.execute(
                        "UPDATE sandbox_positions SET quantity=? WHERE symbol=?",
                        (remaining, symbol),
                    )
            # 记录订单
            conn.execute(
                "INSERT OR REPLACE INTO sandbox_orders (order_id, symbol, side, quantity, price, ts) VALUES (?,?,?,?,?,?)",
                (order_id, symbol, "SELL", quantity, price, ts),
            )
            conn.commit()

    def sandbox_orders_list(self, limit: int = 100) -> list[dict]:
        with self._lock:
            rows = self._get_conn().execute(
                "SELECT * FROM sandbox_orders ORDER BY ts DESC LIMIT ?", (limit,)
            ).fetchall()
        return [{"order_id": r[0], "symbol": r[1], "side": r[2], "quantity": r[3], "price": r[4], "ts": r[5]} for r in rows]

    def cash_ledger_list(self, limit: int = 100) -> list[dict]:
        """查询现金账本"""
        with self._lock:
            rows = self._get_conn().execute(
                "SELECT * FROM cash_ledger ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [{"id": r[0], "order_id": r[1], "entry_type": r[2], "amount": r[3], "balance_after": r[4], "created_at": r[5]} for r in rows]

    def sandbox_rebuild_positions(self) -> dict:
        """从 sandbox_orders 重建持仓（验证 Order/Fill一致性的关键能力）"""
        with self._lock:
            conn = self._get_conn()
            rows = conn.execute(
                "SELECT symbol, side, quantity, price FROM sandbox_orders ORDER BY ts ASC"
            ).fetchall()
        positions: dict[str, dict] = {}
        for symbol, side, qty, price in rows:
            if side == "BUY":
                if symbol not in positions:
                    positions[symbol] = {"quantity": 0, "total_cost": 0}
                positions[symbol]["quantity"] += qty
                positions[symbol]["total_cost"] += qty * price
            else:
                if symbol in positions:
                    positions[symbol]["quantity"] -= qty
                    if positions[symbol]["quantity"] <= 0:
                        del positions[symbol]
        result = {}
        for sym, p in positions.items():
            result[sym] = {
                "quantity": p["quantity"],
                "avg_cost": round(p["total_cost"] / p["quantity"], 4) if p["quantity"] > 0 else 0,
            }
        return result

    def sandbox_reset(self):
        with self._lock:
            conn = self._get_conn()
            conn.execute("DELETE FROM sandbox_positions")
            conn.execute("DELETE FROM sandbox_orders")
            conn.execute("DELETE FROM cash_ledger")
            conn.execute("DELETE FROM sandbox_account")
            conn.commit()

    # ============================================================
    # v2.4 新表 CRUD
    # ============================================================

    # ---- 交易复盘 ----

    def review_save(self, review: dict):
        """保存交易复盘记录"""
        import json as _json
        now = _now()
        with self._lock:
            self._get_conn().execute(
                """INSERT INTO trade_reviews
                   (trade_id, symbol, side, quantity, price, pnl, pnl_pct,
                    holding_days, score, mistakes_json, summary, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (review.get("trade_id", ""), review.get("symbol", ""),
                 review.get("side", ""), review.get("quantity", 0),
                 review.get("price", 0), review.get("pnl", 0),
                 review.get("pnl_pct", 0), review.get("holding_days", 0),
                 review.get("score", 0),
                 _json.dumps(review.get("mistakes", []), ensure_ascii=False),
                 review.get("summary", ""), now),
            )
            self._get_conn().commit()

    def review_list(self, limit: int = 20) -> list[dict]:
        """查询复盘列表（按时间倒序）"""
        import json as _json
        with self._lock:
            rows = self._get_conn().execute(
                "SELECT * FROM trade_reviews ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [{
            "trade_id": r["trade_id"], "symbol": r["symbol"], "side": r["side"],
            "quantity": r["quantity"], "price": r["price"], "pnl": r["pnl"],
            "pnl_pct": r["pnl_pct"], "holding_days": r["holding_days"],
            "score": r["score"], "mistakes": _json.loads(r["mistakes_json"] or "[]"),
            "summary": r["summary"],
            "created_at": int(datetime.fromisoformat(r["created_at"]).timestamp() * 1000),
        } for r in rows]

    def review_get_by_trade(self, trade_id: str) -> Optional[dict]:
        """按订单 ID 查询复盘"""
        import json as _json
        with self._lock:
            r = self._get_conn().execute(
                "SELECT * FROM trade_reviews WHERE trade_id=? ORDER BY id DESC LIMIT 1",
                (trade_id,),
            ).fetchone()
        if not r:
            return None
        return {
            "trade_id": r["trade_id"], "symbol": r["symbol"], "side": r["side"],
            "quantity": r["quantity"], "price": r["price"], "pnl": r["pnl"],
            "pnl_pct": r["pnl_pct"], "holding_days": r["holding_days"],
            "score": r["score"], "mistakes": _json.loads(r["mistakes_json"] or "[]"),
            "summary": r["summary"],
        }

    # ---- 对话历史 ----

    def chat_save(self, role: str, message: str, qtype: str = ""):
        """保存一条对话记录"""
        with self._lock:
            self._get_conn().execute(
                "INSERT INTO chat_history (role, message, qtype, created_at) VALUES (?,?,?,?)",
                (role, message, qtype, _now()),
            )
            self._get_conn().commit()

    def chat_history_list(self, limit: int = 50) -> list[dict]:
        """查询对话历史（按时间正序返回）"""
        with self._lock:
            rows = self._get_conn().execute(
                "SELECT * FROM chat_history ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [{"role": r["role"], "message": r["message"], "qtype": r["qtype"],
                 "created_at": r["created_at"]} for r in reversed(rows)]

    # ---- XP 流水 ----

    def xp_log_add(self, source: str, source_id: str, amount: int, total_after: int):
        """写入 XP 流水"""
        with self._lock:
            self._get_conn().execute(
                "INSERT INTO xp_log (source, source_id, amount, total_after, created_at) VALUES (?,?,?,?,?)",
                (source, source_id, amount, total_after, _now()),
            )
            self._get_conn().commit()

    def xp_log_exists(self, source: str, source_id: str) -> bool:
        """检查某来源的 XP 是否已发放（幂等判断）"""
        with self._lock:
            row = self._get_conn().execute(
                "SELECT 1 FROM xp_log WHERE source=? AND source_id=? LIMIT 1",
                (source, source_id),
            ).fetchone()
        return row is not None

    def xp_log_list(self, limit: int = 50) -> list[dict]:
        """查询 XP 流水"""
        with self._lock:
            rows = self._get_conn().execute(
                "SELECT * FROM xp_log ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [{"source": r["source"], "source_id": r["source_id"],
                 "amount": r["amount"], "total_after": r["total_after"],
                 "created_at": r["created_at"]} for r in rows]

    # ---- 每日打卡 ----

    def checkin_touch(self, date: str, field: str = "xp_earned", increment: int = 1):
        """更新当日打卡计数（不存在则创建）"""
        now = _now()
        allowed = {"xp_earned", "lessons_done", "trades_done", "reviews_done", "explores_done"}
        if field not in allowed:
            return
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                """INSERT INTO daily_checkins (date, created_at, updated_at)
                   VALUES (?,?,?)
                   ON CONFLICT(date) DO NOTHING""",
                (date, now, now),
            )
            conn.execute(
                f"UPDATE daily_checkins SET {field} = {field} + ?, updated_at = ? WHERE date = ?",
                (increment, now, date),
            )
            conn.commit()

    def checkin_get(self, date: str) -> Optional[dict]:
        """查询某日打卡记录"""
        with self._lock:
            r = self._get_conn().execute(
                "SELECT * FROM daily_checkins WHERE date=?", (date,)
            ).fetchone()
        if not r:
            return None
        return {"date": r["date"], "xp_earned": r["xp_earned"],
                "lessons_done": r["lessons_done"], "trades_done": r["trades_done"],
                "reviews_done": r["reviews_done"], "explores_done": r["explores_done"]}

    def checkin_list(self, days: int = 180) -> list[dict]:
        """查询最近 N 天打卡记录"""
        with self._lock:
            rows = self._get_conn().execute(
                "SELECT * FROM daily_checkins ORDER BY date DESC LIMIT ?", (days,)
            ).fetchall()
        return [{"date": r["date"], "xp_earned": r["xp_earned"],
                 "lessons_done": r["lessons_done"], "trades_done": r["trades_done"],
                 "reviews_done": r["reviews_done"], "explores_done": r["explores_done"]}
                for r in rows]

    # ---- 沙盒净值快照 ----

    def sandbox_snapshot_add(self, ts: int, equity: float, cash: float, market_value: float):
        """添加净值快照"""
        with self._lock:
            self._get_conn().execute(
                "INSERT INTO sandbox_snapshots (ts, equity, cash, market_value, created_at) VALUES (?,?,?,?,?)",
                (ts, equity, cash, market_value, _now()),
            )
            self._get_conn().commit()

    def sandbox_snapshots_list(self, limit: int = 500) -> list[dict]:
        """查询净值快照（按时间正序）"""
        with self._lock:
            rows = self._get_conn().execute(
                "SELECT * FROM sandbox_snapshots ORDER BY ts DESC LIMIT ?", (limit,)
            ).fetchall()
        return [{"ts": r["ts"], "equity": r["equity"], "cash": r["cash"],
                 "market_value": r["market_value"]} for r in reversed(rows)]

    # ---- 测验成绩 ----

    def quiz_result_save(self, quiz_id: str, quiz_type: str, score: int,
                         correct_count: int, total_questions: int, passed: bool):
        """保存测验/考试成绩"""
        with self._lock:
            self._get_conn().execute(
                """INSERT INTO quiz_results
                   (quiz_id, quiz_type, score, correct_count, total_questions, passed, created_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (quiz_id, quiz_type, score, correct_count, total_questions,
                 1 if passed else 0, _now()),
            )
            self._get_conn().commit()

    def quiz_result_best(self, quiz_id: str) -> Optional[dict]:
        """查询某测验的最佳成绩"""
        with self._lock:
            r = self._get_conn().execute(
                """SELECT * FROM quiz_results WHERE quiz_id=?
                   ORDER BY score DESC, id DESC LIMIT 1""",
                (quiz_id,),
            ).fetchone()
        if not r:
            return None
        return {"quiz_id": r["quiz_id"], "quiz_type": r["quiz_type"],
                "score": r["score"], "correct_count": r["correct_count"],
                "total_questions": r["total_questions"], "passed": bool(r["passed"])}

    def quiz_results_passed(self, quiz_type: str = "stage_exam") -> list[dict]:
        """查询所有已通过的考试（用于证书墙）"""
        with self._lock:
            rows = self._get_conn().execute(
                """SELECT quiz_id, MAX(score) as best_score, MIN(created_at) as first_passed_at
                   FROM quiz_results WHERE quiz_type=? AND passed=1
                   GROUP BY quiz_id ORDER BY first_passed_at""",
                (quiz_type,),
            ).fetchall()
        return [{"quiz_id": r["quiz_id"], "score": r["best_score"],
                 "passed_at": r["first_passed_at"]} for r in rows]


__all__ = ["UserStore"]
