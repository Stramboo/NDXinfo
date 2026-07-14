# -*- coding: utf-8 -*-
"""SimExecutionRules 的纯逻辑测试。"""
import pytest

from trading.sim_rules import SimExecutionRules, DEFAULT_RULES


class TestSimExecutionRules:
    def test_default_is_no_slipppage_commission(self):
        r = DEFAULT_RULES
        assert r.slippage_bps == 0
        assert r.commission_per_share == 0
        assert r.fill_delay_ms == 0
        assert r.t_plus_one is False

    @pytest.mark.parametrize(
        "ref,bps,side,expected",
        [
            (100.0, 10, True, 100.10),   # 1 bps * 100 = 0.1  -> 100.10
            (100.0, 10, False, 99.90),
            (50.0, 0, True, 50.0),
        ],
    )
    def test_slippage_model(self, ref, bps, side, expected):
        r = SimExecutionRules(slippage_bps=bps)
        assert r.compute_fill_price(ref, side) == pytest.approx(expected)

    def test_commission_min_floor(self):
        r = SimExecutionRules(commission_per_share=0.0, min_commission=1.0)
        assert r.compute_commission(10, 100.0) == 1.0
        r2 = SimExecutionRules(commission_per_share=0.05, min_commission=0.5)
        assert r2.compute_commission(10, 100.0) == 0.5  # 10 * 0.05 = 0.5 == floor
        assert r2.compute_commission(100, 100.0) == 5.0  # 100 * 0.05 = 5.0
