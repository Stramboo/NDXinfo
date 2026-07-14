# -*- coding: utf-8 -*-
"""
K线图表组件

基于 pyqtgraph 绘制专业金融图表：
- K线蜡烛图
- 成交量柱状图
- 可叠加技术指标（MA, MACD, RSI, 布林带）
"""

from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

import pyqtgraph as pg
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QCheckBox, QComboBox, QPushButton)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from gui.styles import (
    BG_DARK, BG_PANEL, BG_INPUT, TEXT_PRIMARY, TEXT_SECONDARY,
    TEXT_ACCENT, GREEN, RED, YELLOW, BORDER, BTN_DEFAULT,
)


class CandlestickItem(pg.GraphicsObject):
    """
    自定义K线蜡烛图项

    使用 QPainter 逐根绘制蜡烛实体和影线。
    """

    def __init__(self, data=None):
        pg.GraphicsObject.__init__(self)
        self.data = np.empty((0, 5))  # [idx, open, high, low, close]
        self.wick_color = pg.mkColor(TEXT_SECONDARY)
        self.up_color = pg.mkColor(GREEN)
        self.down_color = pg.mkColor(RED)
        self.setData(data)

    def setData(self, data):
        if data is None:
            self.data = np.empty((0, 5))
        else:
            self.data = np.array(data)
        self.prepareGeometryChange()
        self.informViewBoundsChanged()

    def boundingRect(self):
        if len(self.data) == 0:
            return pg.QtCore.QRectF()
        x_min = self.data[:, 0].min()
        x_max = self.data[:, 0].max()
        y_min = self.data[:, 2].min()  # low
        y_max = self.data[:, 1].max()  # high
        return pg.QtCore.QRectF(x_min - 1, y_min, x_max - x_min + 2, y_max - y_min)

    def paint(self, p, *args):
        if len(self.data) == 0:
            return
        p.setPen(pg.mkPen(self.wick_color, width=1))

        for i in range(len(self.data)):
            x, open_v, high, low, close = self.data[i]

            # 宽度自适应
            bar_width = 0.6
            if len(self.data) > 30:
                bar_width = 0.8

            # 画影线
            p.drawLine(pg.QtCore.QPointF(x, low), pg.QtCore.QPointF(x, high))

            # 画蜡烛实体
            if close >= open_v:
                p.setBrush(pg.mkBrush(self.up_color))
                p.setPen(pg.mkPen(self.up_color, width=1))
            else:
                p.setBrush(pg.mkBrush(self.down_color))
                p.setPen(pg.mkPen(self.down_color, width=1))

            body_top = max(open_v, close)
            body_bottom = min(open_v, close)
            rect = pg.QtCore.QRectF(
                x - bar_width / 2, body_bottom,
                bar_width, body_top - body_bottom
            )
            p.drawRect(rect)


class StockChartWidget(QWidget):
    """
    股票K线图组件

    上半部分：K线 + MA 均线 + 布林带
    下半部分：成交量柱 + MACD
    RSI 等指标可在独立窗口显示

    输入数据格式: DataFrame，含 Open/High/Low/Close/Volume 及技术指标
    """

    symbol_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._df: Optional[pd.DataFrame] = None
        self._symbol: str = ""
        self._show_ma = True
        self._show_boll = True
        self._show_volume = True
        self._show_macd = False
        self._show_rsi = False

        self._init_ui()
        self._init_chart()

    def _init_ui(self):
        """初始化UI布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 顶部控制栏
        ctrl = QHBoxLayout()
        ctrl.setContentsMargins(8, 4, 8, 4)

        self.symbol_label = QLabel("--")
        self.symbol_label.setObjectName("title")
        self.symbol_label.setStyleSheet(f"color: {TEXT_ACCENT}; font-size: 16px;")

        self.price_label = QLabel("")
        self.price_label.setObjectName("value")

        self.change_label = QLabel("")
        self.change_label.setObjectName("positive")

        # 指标开关
        self.ma_check = QCheckBox("MA")
        self.ma_check.setChecked(True)
        self.ma_check.toggled.connect(self._toggle_ma)
        self.ma_check.setStyleSheet(self._check_style())

        self.boll_check = QCheckBox("BOLL")
        self.boll_check.setChecked(True)
        self.boll_check.toggled.connect(self._toggle_boll)
        self.boll_check.setStyleSheet(self._check_style())

        self.macd_check = QCheckBox("MACD")
        self.macd_check.toggled.connect(self._toggle_macd)
        self.macd_check.setStyleSheet(self._check_style())

        self.rsi_check = QCheckBox("RSI")
        self.rsi_check.toggled.connect(self._toggle_rsi)
        self.rsi_check.setStyleSheet(self._check_style())

        ctrl.addWidget(self.symbol_label)
        ctrl.addWidget(self.price_label)
        ctrl.addWidget(self.change_label)
        ctrl.addStretch()
        ctrl.addWidget(QLabel("指标:"))
        ctrl.addWidget(self.ma_check)
        ctrl.addWidget(self.boll_check)
        ctrl.addWidget(self.macd_check)
        ctrl.addWidget(self.rsi_check)

        layout.addLayout(ctrl)

        # 图表区域
        self.graphics_widget = pg.GraphicsLayoutWidget()
        self.graphics_widget.setBackground(BG_PANEL)
        layout.addWidget(self.graphics_widget, 1)

    def _check_style(self):
        return f"""
            QCheckBox {{ color: {TEXT_SECONDARY}; spacing: 4px; font-size: 11px; }}
            QCheckBox::indicator {{ width: 14px; height: 14px; }}
            QCheckBox::indicator:checked {{ background-color: {TEXT_ACCENT}; border-radius: 3px; }}
        """

    def _init_chart(self):
        """初始化图表区域"""
        gw = self.graphics_widget
        gw.clear()

        # === 上半部分：K线图 ===
        self.p1 = gw.addPlot(row=0, col=0)
        self.p1.showGrid(x=True, y=True, alpha=0.2)
        self.p1.setLabel("left", "Price", color=TEXT_SECONDARY)
        self.p1.getAxis("left").setTextPen(TEXT_SECONDARY)
        self.p1.getAxis("bottom").setTextPen(TEXT_SECONDARY)
        self.p1.setMouseEnabled(x=True, y=True)

        # 自定义K线
        self.candlestick = CandlestickItem()
        self.p1.addItem(self.candlestick)

        # MA 均线
        self.ma_lines = {}
        ma_colors = {
            "MA5": "#58a6ff",
            "MA10": "#d29922",
            "MA20": "#3fb950",
            "MA60": "#f85149",
        }
        for name, color in ma_colors.items():
            line = self.p1.plot(pen=pg.mkPen(color, width=1.5), name=name)
            self.ma_lines[name] = line

        # 布林带
        self.boll_upper = self.p1.plot(pen=pg.mkPen("#8b949e", width=1, style=Qt.DashLine))
        self.boll_mid = self.p1.plot(pen=pg.mkPen("#8b949e", width=1, style=Qt.DashLine))
        self.boll_lower = self.p1.plot(pen=pg.mkPen("#8b949e", width=1, style=Qt.DashLine))

        # 填充布林带区域
        self.boll_fill = pg.FillBetweenItem(
            self.boll_upper, self.boll_lower,
            brush=(139, 148, 158, 15)
        )
        self.p1.addItem(self.boll_fill)

        # === 下半部分：成交量 ===
        self.p2 = gw.addPlot(row=1, col=0)
        self.p2.showGrid(y=True, alpha=0.2)
        self.p2.setLabel("left", "Volume", color=TEXT_SECONDARY)
        self.p2.getAxis("left").setTextPen(TEXT_SECONDARY)
        self.p2.getAxis("bottom").setTextPen(TEXT_SECONDARY)
        self.p2.setXLink(self.p1)

        # 使用 BarGraphItem 画成交量
        self.volume_bars = pg.BarGraphItem(x=[], height=[], width=0.6)
        self.p2.addItem(self.volume_bars)

        # === MACD 子图 ===
        self.p3 = gw.addPlot(row=2, col=0)
        self.p3.showGrid(y=True, alpha=0.2)
        self.p3.setLabel("left", "MACD", color=TEXT_SECONDARY)
        self.p3.getAxis("left").setTextPen(TEXT_SECONDARY)
        self.p3.getAxis("bottom").setTextPen(TEXT_SECONDARY)
        self.p3.setXLink(self.p1)
        self.p3.hide()

        self.macd_hist = pg.BarGraphItem(x=[], height=[], width=0.6)
        self.p3.addItem(self.macd_hist)
        self.macd_dif = self.p3.plot(pen=pg.mkPen("#58a6ff", width=1.5))
        self.macd_dea = self.p3.plot(pen=pg.mkPen("#d29922", width=1.5))
        self.macd_zero = self.p3.plot(pen=pg.mkPen("#30363d", width=1))

        # === RSI 子图 ===
        self.p4 = gw.addPlot(row=3, col=0)
        self.p4.showGrid(y=True, alpha=0.2)
        self.p4.setLabel("left", "RSI", color=TEXT_SECONDARY)
        self.p4.getAxis("left").setTextPen(TEXT_SECONDARY)
        self.p4.getAxis("bottom").setTextPen(TEXT_SECONDARY)
        self.p4.setXLink(self.p1)
        self.p4.setYRange(0, 100)
        self.p4.hide()

        self.rsi_line = self.p4.plot(pen=pg.mkPen("#d29922", width=2))
        self.p4.addItem(pg.InfiniteLine(pos=70, angle=0, pen=pg.mkPen(RED, width=1, style=Qt.DashLine)))
        self.p4.addItem(pg.InfiniteLine(pos=30, angle=0, pen=pg.mkPen(GREEN, width=1, style=Qt.DashLine)))

        # 链接X轴
        self.p2.setXLink(self.p1)
        self.p3.setXLink(self.p1)
        self.p4.setXLink(self.p1)

        # 设置行高比例
        gw.ci.layout.setRowStretchFactor(0, 4)
        gw.ci.layout.setRowStretchFactor(1, 1)
        gw.ci.layout.setRowStretchFactor(2, 1)
        gw.ci.layout.setRowStretchFactor(3, 1)

    # ----------------------------------------------------------
    # 数据更新
    # ----------------------------------------------------------

    def set_data(self, df: pd.DataFrame, symbol: str = ""):
        """
        设置图表数据

        参数:
            df:     含 OHLCV 和技术指标的 DataFrame
            symbol: 股票代码
        """
        if df is None or df.empty:
            return

        self._df = df
        self._symbol = symbol
        self.symbol_label.setText(symbol)

        n = len(df)
        x = np.arange(n)

        # 提取价格
        opens = df["Open"].values if "Open" in df.columns else df["Close"].values
        highs = df["High"].values if "High" in df.columns else df["Close"].values
        lows = df["Low"].values if "Low" in df.columns else df["Close"].values
        closes = df["Close"].values

        # 更新K线数据
        candlestick_data = np.column_stack([x, opens, highs, lows, closes])
        self.candlestick.setData(candlestick_data)

        # 更新均线
        for name, line in self.ma_lines.items():
            if name in df.columns:
                values = df[name].values
                mask = ~np.isnan(values)
                line.setData(x[mask], values[mask])
            else:
                line.clear()

        # 更新布林带
        if "BOLL_UPPER" in df.columns:
            valid = ~np.isnan(df["BOLL_UPPER"].values)
            self.boll_upper.setData(x[valid], df["BOLL_UPPER"].values[valid])
            self.boll_mid.setData(x[valid], df["BOLL_MID"].values[valid])
            self.boll_lower.setData(x[valid], df["BOLL_LOWER"].values[valid])

        # 更新成交量
        if "Volume" in df.columns:
            vol = df["Volume"].values
            colors = []
            for i in range(n):
                if closes[i] >= opens[i]:
                    colors.append(GREEN)
                else:
                    colors.append(RED)
            self.volume_bars.setOpts(x=x, height=vol, width=0.6, brushes=colors)

        # 更新MACD
        if "MACD_HIST" in df.columns:
            hist = df["MACD_HIST"].values
            colors = [GREEN if h >= 0 else RED for h in hist]
            valid = ~np.isnan(hist)
            self.macd_hist.setOpts(x=x[valid], height=hist[valid], width=0.6, brushes=np.array(colors)[valid])
            self.macd_dif.setData(x[valid], df["DIF"].values[valid])
            self.macd_dea.setData(x[valid], df["DEA"].values[valid])
            self.macd_zero.setData([x[0], x[-1]], [0, 0])

        # 更新RSI
        if "RSI" in df.columns:
            valid = ~np.isnan(df["RSI"].values)
            self.rsi_line.setData(x[valid], df["RSI"].values[valid])

        # 更新价格显示
        if n > 0:
            price = closes[-1]
            prev_price = closes[-2] if n >= 2 else price
            change = price - prev_price
            change_pct = (change / prev_price * 100) if prev_price else 0

            self.price_label.setText(f"${price:.2f}")
            if change >= 0:
                self.price_label.setStyleSheet(f"color: {GREEN}; font-size: 20px; font-weight: bold;")
                self.change_label.setText(f"+{change:.2f} (+{change_pct:.2f}%)")
                self.change_label.setStyleSheet(f"color: {GREEN}; font-size: 14px; font-weight: bold;")
            else:
                self.price_label.setStyleSheet(f"color: {RED}; font-size: 20px; font-weight: bold;")
                self.change_label.setText(f"{change:.2f} ({change_pct:.2f}%)")
                self.change_label.setStyleSheet(f"color: {RED}; font-size: 14px; font-weight: bold;")

        # 自动缩放
        self.p1.autoRange()

    def _toggle_ma(self, checked):
        self._show_ma = checked
        for line in self.ma_lines.values():
            line.setVisible(checked)

    def _toggle_boll(self, checked):
        self._show_boll = checked
        self.boll_upper.setVisible(checked)
        self.boll_mid.setVisible(checked)
        self.boll_lower.setVisible(checked)

    def _toggle_macd(self, checked):
        self._show_macd = checked
        self.p3.setVisible(checked)

    def _toggle_rsi(self, checked):
        self._show_rsi = checked
        self.p4.setVisible(checked)
