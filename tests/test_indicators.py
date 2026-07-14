# -*- coding: utf-8 -*-
"""indicators 形状 / NaN 行为纯测试"""
import numpy as np
import pandas as pd
import pytest

from indicators import calc_all_indicators


def _series_df(n=200):
    np.random.seed(0)
    close = 100 + np.cumsum(np.random.normal(0, 1, n))
    df = pd.DataFrame({
        "Open": close,
        "High": close + 0.5,
        "Low": close - 0.5,
        "Close": close,
        "Volume": np.ones(n) * 1e6,
    })
    return df


class TestIndicators:
    def test_all_indicators_adds_expected_columns(self):
        df = calc_all_indicators(_series_df())
        for col in ["MA5", "MA10", "MA20", "DIF", "DEA", "MACD_HIST", "RSI",
                    "BOLL_UPPER", "BOLL_LOWER", "BOLL_MID", "K", "D", "J"]:
            assert col in df.columns, f"缺少 {col}"

    def test_rsi_in_range(self):
        df = calc_all_indicators(_series_df())
        rsi = df["RSI"].dropna()
        assert rsi.between(0, 100.01).all()

    def test_macd_hist_diff_dea_consistent(self):
        df = calc_all_indicators(_series_df())
        last_dif = df["DIF"].iloc[-1]
        last_dea = df["DEA"].iloc[-1]
        last_macd = df["MACD_HIST"].iloc[-1]
        assert last_macd == pytest.approx((last_dif - last_dea) * 2)
