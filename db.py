# -*- coding: utf-8 -*-
"""
NASDAQ 每日分析报告 - SQLite 存储层
持久化每日价格快照、指标快照、报告元数据
"""

import os
import sqlite3
import logging
from datetime import datetime
from config import DB_PATH, DATA_DIR

logger = logging.getLogger(__name__)


class DbManager:
    """SQLite 数据库管理器"""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._ensure_dir()
        self._init_db()

    def _ensure_dir(self):
        """确保数据目录存在"""
        os.makedirs(DATA_DIR, exist_ok=True)

    def _init_db(self):
        """初始化数据库表"""
        with self._get_conn() as conn:
            conn.executescript("""
                -- 每日价格快照
                CREATE TABLE IF NOT EXISTS daily_prices (
                    ticker TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL, high REAL, low REAL,
                    close REAL, volume INTEGER, change_pct REAL,
                    PRIMARY KEY (ticker, date)
                );

                -- 指标快照
                CREATE TABLE IF NOT EXISTS indicator_snapshots (
                    ticker TEXT NOT NULL,
                    date TEXT NOT NULL,
                    rsi REAL, macd_hist REAL, atr REAL,
                    trend TEXT, recommendation TEXT,
                    vix REAL, breadth_ratio REAL,
                    PRIMARY KEY (ticker, date)
                );

                -- 报告元数据
                CREATE TABLE IF NOT EXISTS reports (
                    date TEXT PRIMARY KEY,
                    file_path TEXT,
                    ixic_close REAL,
                    vix REAL,
                    trend TEXT,
                    breadth_ratio REAL,
                    overall_sentiment TEXT,
                    created_at TEXT
                );

                -- 回测结果历史
                CREATE TABLE IF NOT EXISTS backtest_results (
                    date TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    total_return REAL,
                    annual_return REAL,
                    max_drawdown REAL,
                    sharpe REAL,
                    win_rate REAL,
                    num_trades INTEGER,
                    PRIMARY KEY (date, strategy)
                );

                -- ML 预测历史
                CREATE TABLE IF NOT EXISTS predictions (
                    date TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    predicted_dir TEXT,
                    actual_dir TEXT,
                    confidence TEXT,
                    PRIMARY KEY (date, ticker)
                );
            """)
        logger.debug("数据库初始化完成")

    def _get_conn(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)

    def upsert_daily_price(self, ticker, date, open_p, high, low, close, volume, change_pct):
        """写入或更新每日价格"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO daily_prices
                (ticker, date, open, high, low, close, volume, change_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (ticker, date, open_p, high, low, close, volume, change_pct))

    def upsert_indicator_snapshot(self, ticker, date, rsi, macd_hist, atr,
                                   trend, recommendation, vix=None, breadth_ratio=None):
        """写入或更新指标快照"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO indicator_snapshots
                (ticker, date, rsi, macd_hist, atr, trend, recommendation, vix, breadth_ratio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (ticker, date, rsi, macd_hist, atr, trend, recommendation, vix, breadth_ratio))

    def upsert_report(self, date, file_path, ixic_close, vix, trend,
                       breadth_ratio, overall_sentiment=None):
        """写入或更新报告元数据"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO reports
                (date, file_path, ixic_close, vix, trend, breadth_ratio, overall_sentiment, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (date, file_path, ixic_close, vix, trend, breadth_ratio,
                  overall_sentiment, datetime.now().isoformat()))

    def upsert_backtest_result(self, date, strategy, metrics):
        """写入回测结果"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO backtest_results
                (date, strategy, total_return, annual_return, max_drawdown, sharpe, win_rate, num_trades)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (date, strategy,
                  metrics.get("total_return"), metrics.get("annual_return"),
                  metrics.get("max_drawdown"), metrics.get("sharpe_ratio"),
                  metrics.get("win_rate"), metrics.get("num_trades")))

    def get_previous_report(self, date, lookback_days=1):
        """获取前一次报告的元数据"""
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM reports
                WHERE date < ?
                ORDER BY date DESC
                LIMIT 1
            """, (date,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_previous_indicators(self, ticker, date, lookback_days=1):
        """获取某只股票前一次的指标快照"""
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM indicator_snapshots
                WHERE ticker = ? AND date < ?
                ORDER BY date DESC
                LIMIT 1
            """, (ticker, date))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_indicator_history(self, ticker, days=30):
        """获取某只股票的指标历史"""
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM indicator_snapshots
                WHERE ticker = ?
                ORDER BY date DESC
                LIMIT ?
            """, (ticker, days))
            return [dict(row) for row in cursor.fetchall()]

    def get_report_list(self, limit=30):
        """获取报告列表"""
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT date, ixic_close, vix, trend, breadth_ratio, overall_sentiment
                FROM reports
                ORDER BY date DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """关闭连接（SQLite 自动管理，此方法为兼容性保留）"""
        pass
