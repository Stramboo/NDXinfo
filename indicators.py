# -*- coding: utf-8 -*-
"""
NASDAQ 每日分析报告 - 技术指标计算模块
纯 pandas 实现，零 C 依赖，Windows 友好
"""

import pandas as pd
import numpy as np
from config import (
    MA_PERIODS, RSI_PERIOD, MACD_FAST, MACD_SLOW, MACD_SIGNAL,
    KDJ_PERIOD, BOLL_PERIOD, BOLL_STD
)


def calc_moving_averages(df, periods=None):
    """计算移动平均线 MA(5/10/20/60)"""
    if periods is None:
        periods = MA_PERIODS
    for p in periods:
        df[f"MA{p}"] = df["Close"].rolling(window=p).mean()
    return df


def calc_macd(df, fast=MACD_FAST, slow=MACD_SLOW, signal=MACD_SIGNAL):
    """
    计算 MACD
    DIF = EMA(fast) - EMA(slow)
    DEA = EMA(signal) of DIF
    HIST = 2 * (DIF - DEA)
    """
    ema_fast = df["Close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["Close"].ewm(span=slow, adjust=False).mean()
    df["DIF"] = ema_fast - ema_slow
    df["DEA"] = df["DIF"].ewm(span=signal, adjust=False).mean()
    df["MACD_HIST"] = 2 * (df["DIF"] - df["DEA"])
    return df


def calc_rsi(df, period=RSI_PERIOD):
    """
    计算 RSI(14) - 使用 Wilder 平滑法
    RS = avg_gain / avg_loss
    RSI = 100 - 100 / (1 + RS)
    """
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    # Wilder 平滑 = EMA with alpha = 1/period
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
    # 避免除以0
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))
    # 当 avg_loss 为 0 时 RSI = 100
    df["RSI"] = df["RSI"].fillna(100)
    return df


def calc_kdj(df, period=KDJ_PERIOD):
    """
    计算 KDJ
    RSV = (Close - Low_n) / (High_n - Low_n) * 100
    K = SMA(RSV, 3)
    D = SMA(K, 3)
    J = 3*K - 2*D
    """
    low_n = df["Low"].rolling(window=period).min()
    high_n = df["High"].rolling(window=period).max()
    denom = high_n - low_n
    denom = denom.replace(0, np.nan)
    rsv = (df["Close"] - low_n) / denom * 100
    rsv = rsv.fillna(50)  # 无波动时取中值
    df["K"] = rsv.rolling(window=3).mean()
    df["D"] = df["K"].rolling(window=3).mean()
    df["J"] = 3 * df["K"] - 2 * df["D"]
    return df


def calc_bollinger(df, period=BOLL_PERIOD, std_mult=BOLL_STD):
    """
    计算布林带
    中轨 = MA(period)
    上轨 = 中轨 + std_mult * std(period)
    下轨 = 中轨 - std_mult * std(period)
    """
    df["BOLL_MID"] = df["Close"].rolling(window=period).mean()
    df["BOLL_STD"] = df["Close"].rolling(window=period).std()
    df["BOLL_UPPER"] = df["BOLL_MID"] + std_mult * df["BOLL_STD"]
    df["BOLL_LOWER"] = df["BOLL_MID"] - std_mult * df["BOLL_STD"]
    return df


def calc_all_indicators(df):
    """一次性计算所有技术指标"""
    if df is None or df.empty:
        return df
    df = calc_moving_averages(df)
    df = calc_macd(df)
    df = calc_rsi(df)
    df = calc_kdj(df)
    df = calc_bollinger(df)
    return df
