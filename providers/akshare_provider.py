# -*- coding: utf-8 -*-
"""
akshare 数据提供者模块

基于 akshare 实现港股（HK）和 A 股（SH/SZ）数据获取，
是 DataProvider 的具体实现。

支持带前缀的标的代码格式：
    - HK:0700  -> 港股腾讯控股，akshare 符号 "00700"（补零至5位）
    - SH:600519 -> 沪市贵州茅台，akshare 符号 "600519"
    - SZ:000001 -> 深市平安银行，akshare 符号 "000001"

若 akshare 未安装，模块仍可正常导入，但所有数据获取方法
将返回空结果并记录警告日志，实现优雅降级。
"""

import time
import logging
import pandas as pd
from datetime import datetime, timedelta

from providers.base import DataProvider

logger = logging.getLogger(__name__)

# 尝试导入 akshare，若未安装则置为 None，后续方法将优雅降级
try:
    import akshare as ak
    _AKSHARE_AVAILABLE = True
except ImportError:
    ak = None
    _AKSHARE_AVAILABLE = False
    logger.warning(
        "akshare 未安装，港股/A股数据获取功能将不可用。"
        "可通过 pip install akshare 安装。"
    )

# akshare 返回的中文列名 -> 英文标准列名映射
# 同时兼容可能出现的带空格变体
_COLUMN_MAP = {
    "日期": "Date",
    "开盘": "Open",
    "最高": "High",
    "最低": "Low",
    "收盘": "Close",
    "成交量": "Volume",
    "成交额": "Amount",
    "振幅": "Amplitude",
    "涨跌幅": "ChangePct",
    "涨跌额": "ChangeAmt",
    "换手率": "Turnover",
}

# 周期字符串到天数的映射，用于计算起止日期
_PERIOD_DAYS = {
    "1d": 1,
    "5d": 5,
    "1mo": 30,
    "3mo": 90,
    "6mo": 180,
    "1y": 365,
    "2y": 730,
    "5y": 1825,
    "10y": 3650,
    "ytd": 365,
    "max": 3650,
}


class AkshareProvider(DataProvider):
    """
    基于 akshare 的港股/A股数据提供者

    实现 DataProvider 接口，封装 akshare API 调用，
    支持港股（HK:前缀）和 A 股（SH:/SZ:前缀）数据获取。
    """

    def __init__(self):
        super().__init__()

    # ============================================================
    # 接口方法实现
    # ============================================================

    def fetch_history(self, ticker, period="1y"):
        """
        获取港股/A股历史行情数据

        根据 ticker 前缀路由到不同的 akshare 接口：
            - HK: 前缀 -> ak.stock_hk_daily_em（港股日线）
            - SH:/SZ: 前缀 -> ak.stock_zh_a_hist（A股日线）

        参数:
            ticker: 带前缀的标的代码，如 "HK:0700"、"SH:600519"
            period: 数据周期，如 "1y"、"3mo"

        返回:
            pd.DataFrame，含 Open、High、Low、Close、Volume 列（首字母大写）
        """
        # akshare 未安装时优雅降级
        if not _AKSHARE_AVAILABLE:
            logger.warning(f"akshare 未安装，无法获取 {ticker} 数据")
            return pd.DataFrame()

        # 解析前缀和代码
        prefix, code = self._parse_ticker(ticker)
        if prefix is None:
            logger.warning(f"无法识别的标的代码格式: {ticker}，需以 HK:/SH:/SZ: 开头")
            return pd.DataFrame()

        try:
            if prefix == "HK":
                df = self._fetch_hk_history(code, period)
            else:
                # SH / SZ 均使用 A 股接口
                df = self._fetch_a_share_history(code, period)

            if df is None or df.empty:
                logger.warning(f"获取 {ticker} 数据为空")
                return pd.DataFrame()

            # 标准化列名为英文并首字母大写
            df = self._map_columns(df)
            logger.info(f"获取 {ticker} 数据成功: {len(df)} 条记录")
            return df

        except Exception as e:
            logger.warning(f"获取 {ticker} 数据失败: {e}")
            return pd.DataFrame()

    def fetch_batch(self, tickers, period="1y"):
        """
        批量获取多只港股/A股历史行情数据

        逐只调用 fetch_history，每次请求间隔 0.3 秒以避免触发限流。

        参数:
            tickers: 带前缀的标的代码列表
            period: 数据周期

        返回:
            dict[str, pd.DataFrame]，键为标的代码，值为对应 DataFrame
        """
        if not _AKSHARE_AVAILABLE:
            logger.warning("akshare 未安装，批量获取港股/A股数据不可用")
            return {t: pd.DataFrame() for t in tickers}

        result = {}
        for ticker in tickers:
            df = self.fetch_history(ticker, period)
            result[ticker] = df
            # 请求间隔，避免触发 akshare 数据源限流
            time.sleep(0.3)

        success_count = sum(1 for v in result.values() if not v.empty)
        logger.info(f"批量下载 {len(tickers)} 只港股/A股完成，成功 {success_count} 只")
        return result

    def fetch_info(self, ticker):
        """
        获取港股/A股基本信息

        参数:
            ticker: 带前缀的标的代码

        返回:
            dict，含 name、sector、market_cap 字段
        """
        if not _AKSHARE_AVAILABLE:
            logger.warning(f"akshare 未安装，无法获取 {ticker} 基本信息")
            return {"name": ticker, "sector": "N/A", "market_cap": None}

        prefix, code = self._parse_ticker(ticker)
        if prefix is None:
            return {"name": ticker, "sector": "N/A", "market_cap": None}

        try:
            # 尝试使用东财个股信息接口获取基本信息
            if prefix in ("SH", "SZ"):
                info_df = ak.stock_individual_info_em(symbol=code)
                return self._parse_a_share_info(info_df, ticker)
            else:
                # 港股暂无完善的个股信息接口，返回基本占位信息
                return {
                    "name": ticker,
                    "sector": "N/A",
                    "market_cap": None,
                }
        except Exception as e:
            logger.warning(f"获取 {ticker} 基本信息失败: {e}")
            return {"name": ticker, "sector": "N/A", "market_cap": None}

    def screen_gainers(self, top_n=10):
        """
        筛选涨幅榜（港股/A股暂不支持）

        当前版本不支持港股/A股涨幅榜筛选，直接返回空列表。

        参数:
            top_n: 返回前 N 只

        返回:
            list，空列表
        """
        logger.info("港股/A股涨幅榜筛选暂不支持，返回空列表")
        return []

    # ============================================================
    # 内部辅助方法
    # ============================================================

    def _parse_ticker(self, ticker):
        """
        解析带前缀的标的代码

        参数:
            ticker: 带前缀的标的代码，如 "HK:0700"、"SH:600519"

        返回:
            tuple(prefix, code)，如 ("HK", "0700")；无法识别时返回 (None, None)
        """
        if not isinstance(ticker, str) or ":" not in ticker:
            return (None, None)

        parts = ticker.split(":", 1)
        prefix = parts[0].upper()
        code = parts[1].strip()

        if prefix not in ("HK", "SH", "SZ"):
            return (None, None)

        # 港股代码补零至5位（akshare 要求5位数字格式）
        if prefix == "HK":
            code = code.zfill(5)

        return (prefix, code)

    def _period_to_dates(self, period):
        """
        将周期字符串转换为起止日期

        参数:
            period: 周期字符串，如 "1y"、"3mo"

        返回:
            tuple(start_date, end_date)，格式为 "YYYYMMDD"
        """
        days = _PERIOD_DAYS.get(period.lower(), 365)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return (
            start_date.strftime("%Y%m%d"),
            end_date.strftime("%Y%m%d"),
        )

    def _fetch_hk_history(self, code, period):
        """
        获取港股日线历史数据

        使用 ak.stock_hk_daily_em 接口，该接口返回全部历史数据，
        需根据 period 在本地按日期过滤。

        参数:
            code: 港股代码（5位数字字符串），如 "00700"
            period: 数据周期

        返回:
            pd.DataFrame，原始 akshare 返回值
        """
        def _fetch():
            return ak.stock_hk_daily_em(symbol=code, adjust="qfq")

        result = self._retry(_fetch)
        if result is None or result.empty:
            return pd.DataFrame()

        # stock_hk_daily_em 返回全部历史数据，需按日期过滤
        result = self._filter_by_period(result, period)
        return result

    def _fetch_a_share_history(self, code, period):
        """
        获取 A 股日线历史数据

        使用 ak.stock_zh_a_hist 接口，支持通过 start_date / end_date
        指定数据范围。

        参数:
            code: A 股代码，如 "600519"、"000001"
            period: 数据周期

        返回:
            pd.DataFrame，原始 akshare 返回值
        """
        start_date, end_date = self._period_to_dates(period)

        def _fetch():
            return ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",
            )

        result = self._retry(_fetch)
        if result is None:
            return pd.DataFrame()
        return result

    def _filter_by_period(self, df, period):
        """
        按周期过滤 DataFrame 的日期范围

        stock_hk_daily_em 返回全部历史数据，此方法根据 period
        计算起始日期并过滤。

        参数:
            df: 含日期列的 DataFrame
            period: 数据周期

        返回:
            过滤后的 DataFrame
        """
        if df is None or df.empty:
            return df

        days = _PERIOD_DAYS.get(period.lower(), 365)
        cutoff = datetime.now() - timedelta(days=days)

        # 尝试从 "日期" 列过滤
        date_col = None
        if "日期" in df.columns:
            date_col = "日期"
        elif "Date" in df.columns:
            date_col = "Date"

        if date_col is None:
            return df

        try:
            df[date_col] = pd.to_datetime(df[date_col])
            df = df[df[date_col] >= cutoff].copy()
        except Exception as e:
            logger.warning(f"按日期过滤失败: {e}，返回全部数据")

        return df

    def _map_columns(self, df):
        """
        将 akshare 中文列名映射为英文标准列名

        参数:
            df: 含中文列名的 DataFrame

        返回:
            列名标准化后的 DataFrame，含 Open、High、Low、Close、Volume
        """
        if df is None or df.empty:
            return df

        # 重命名已知的中文列
        rename_dict = {}
        for col in df.columns:
            col_clean = str(col).strip()
            if col_clean in _COLUMN_MAP:
                rename_dict[col] = _COLUMN_MAP[col_clean]

        if rename_dict:
            df = df.rename(columns=rename_dict)

        # 将日期列设为索引（与 yfinance 返回格式一致）
        if "Date" in df.columns:
            try:
                df["Date"] = pd.to_datetime(df["Date"])
                df = df.set_index("Date")
            except Exception as e:
                logger.warning(f"设置日期索引失败: {e}")

        # 仅保留标准 OHLCV 列（若存在）
        standard_cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
        if standard_cols:
            df = df[standard_cols]

        return df

    def _parse_a_share_info(self, info_df, ticker):
        """
        解析东财个股信息接口返回结果

        ak.stock_individual_info_em 返回 item/value 两列的 DataFrame，
        需转换为字典格式。

        参数:
            info_df: akshare 返回的个股信息 DataFrame
            ticker: 原始标的代码（用于回退）

        返回:
            dict，含 name、sector、market_cap 字段
        """
        if info_df is None or info_df.empty:
            return {"name": ticker, "sector": "N/A", "market_cap": None}

        try:
            # 转为 {item: value} 字典
            info = dict(zip(info_df["item"], info_df["value"]))

            name = info.get("股票简称", ticker)
            sector = info.get("行业", "N/A")
            market_cap = info.get("总市值")

            # 尝试将市值转为数值
            if market_cap is not None:
                try:
                    market_cap = float(market_cap)
                except (ValueError, TypeError):
                    pass

            return {
                "name": name,
                "sector": sector,
                "market_cap": market_cap,
            }
        except Exception as e:
            logger.warning(f"解析个股信息失败: {e}")
            return {"name": ticker, "sector": "N/A", "market_cap": None}
