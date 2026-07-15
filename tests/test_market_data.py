# -*- coding: utf-8 -*-
"""
test_market_data.py — MarketDataService 单元测试
"""
import pytest

from market_data.service import MarketDataService
from market_data.models import Bar, BarsResult, Quote, MarketStatus
from market_data.providers.mock import MockProvider


@pytest.fixture
def mock_svc() -> MarketDataService:
    return MarketDataService(provider=MockProvider())


class TestMockProvider:
    """Mock 模式下各项功能"""

    def test_get_bars_returns_bars(self, mock_svc):
        result = mock_svc.get_bars("AAPL", period="1y")
        assert isinstance(result, BarsResult)
        assert result.symbol == "AAPL"
        assert result.source == "mock"
        assert len(result.bars) > 30  # 至少有足够多的K线

    def test_get_bars_invalid_symbol(self, mock_svc):
        result = mock_svc.get_bars("INVALID")
        assert len(result.bars) == 0

    def test_get_quote_returns_quote(self, mock_svc):
        quote = mock_svc.get_quote("NVDA")
        assert quote is not None
        assert isinstance(quote, Quote)
        assert quote.symbol == "NVDA"
        assert quote.price > 0
        assert quote.source == "mock"

    def test_get_quote_unsupported(self, mock_svc):
        quote = mock_svc.get_quote("INVALID")
        assert quote is None

    def test_batch_quotes(self, mock_svc):
        result = mock_svc.get_batch_quotes(["NVDA", "AAPL", "MSFT"])
        assert len(result) == 3
        assert "NVDA" in result
        assert result["NVDA"].price > 0

    def test_get_market_status(self, mock_svc):
        status = mock_svc.get_market_status()
        assert isinstance(status, MarketStatus)
        assert status.exchange == "MOCK"

    def test_supports_symbol(self, mock_svc):
        assert mock_svc.supports_symbol("NVDA")
        assert mock_svc.supports_symbol("AAPL")
        assert not mock_svc.supports_symbol("UNKNOWN")

    def test_cache_invalidation(self, mock_svc):
        q1 = mock_svc.get_quote("NVDA")
        mock_svc.invalidate_cache()
        q2 = mock_svc.get_quote("NVDA")
        # 缓存清除后仍应能获取（重新查询）
        assert q2 is not None
        assert q2.price > 0

    def test_bars_to_dataframe(self, mock_svc):
        df = mock_svc.get_bars_as_dataframe("AAPL", period="3mo")
        assert df is not None
        assert len(df) > 0
        assert "Close" in df.columns
        assert "Open" in df.columns


class TestBarModel:
    """Bar 数据模型"""

    def test_bar_construction(self):
        from datetime import datetime
        bar = Bar(
            timestamp=datetime(2026, 1, 15),
            open=100.0, high=105.0, low=98.0, close=103.0, volume=5000000,
        )
        assert bar.open == 100.0
        assert bar.close == 103.0


class TestBarsResult:
    """BarsResult 模型"""

    def test_to_dataframe(self, mock_svc):
        result = mock_svc.get_bars("NVDA")
        df = result.to_dataframe()
        assert "Close" in df.columns
        assert not df.empty


class TestServiceSingleton:
    """服务单例"""

    def test_singleton(self):
        s1 = MarketDataService.get_instance()
        s2 = MarketDataService.get_instance()
        assert s1 is s2
