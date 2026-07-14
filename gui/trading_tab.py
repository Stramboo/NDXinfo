# -*- coding: utf-8 -*-
"""
美股自动交易系统 - 交易标签页模块

集成 K 线图表、技术指标面板、手动下单面板和订单历史。
用户可在此页面查看行情图表、分析技术指标、手动下单和管理订单。

布局结构:
    +---------------------------+-------------------+
    |    K线图区域              |   手动下单面板    |
    |   (代码输入/周期选择)      |  (买卖/数量/类型) |
    |                           |                   |
    +---------------------------+   快捷按钮        |
    |   技术指标面板            +-------------------+
    |   (RSI/MACD/MA/布林带)    |   订单历史表格    |
    +---------------------------+-------------------+
"""

import numpy as np
import pandas as pd

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton,
    QTableWidget, QSplitter, QFrame, QSizePolicy, QGroupBox,
    QMessageBox, QButtonGroup, QRadioButton, QHeaderView,
)
from PyQt5.QtGui import QColor, QBrush, QFont

from gui.styles import (
    COLOR_BG, COLOR_PANEL, COLOR_TEXT, COLOR_TEXT_DIM,
    COLOR_GREEN, COLOR_RED, COLOR_BLUE, COLOR_YELLOW,
    COLOR_GRAY, COLOR_BORDER, COLOR_ORANGE,
)
from gui.utils import (
    format_price, format_pct, format_signed, format_number,
    format_volume, format_int, format_datetime,
    color_for_pnl, color_for_change, color_for_side,
    setup_table, set_cell, clear_table,
    flatten_stock_universe, NumericTableWidgetItem,
)
from gui.chart_widget import CandlestickChart


# 时间周期选项映射
TIMEFRAMES = {
    "1分钟": "1Min",
    "5分钟": "5Min",
    "15分钟": "15Min",
    "1小时": "1Hour",
    "日线": "1Day",
}


class TradingTab(QWidget):
    """
    交易标签页。

    提供 K 线图表、技术指标分析、手动下单和订单历史功能。
    """

    def __init__(self, engine, parent=None):
        """
        初始化交易标签页。

        参数:
            engine: TradingEngine 实例
            parent: 父控件
        """
        super().__init__(parent)
        self._engine = engine
        self._current_symbol = "AAPL"
        self._current_timeframe = "1Day"
        self._current_side = "buy"  # 'buy' or 'sell'

        # 获取默认股票
        try:
            from config import STOCK_UNIVERSE
            symbols, _ = flatten_stock_universe(STOCK_UNIVERSE)
            self._default_symbols = symbols if symbols else ["AAPL"]
        except ImportError:
            self._default_symbols = ["AAPL"]

        self._init_ui()

    def _init_ui(self):
        """构建 UI 布局"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # 左右分割
        main_splitter = QSplitter(Qt.Horizontal)

        # ---- 左侧：图表 + 指标 ----
        left_widget = self._create_chart_panel()
        main_splitter.addWidget(left_widget)

        # ---- 右侧：下单 + 订单历史 ----
        right_widget = self._create_right_panel()
        main_splitter.addWidget(right_widget)

        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 1)
        main_splitter.setSizes([800, 400])

        main_layout.addWidget(main_splitter)

    def _create_chart_panel(self):
        """创建左侧图表 + 指标面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # ---- 图表顶部工具栏 ----
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        lbl_symbol = QLabel("代码:")
        toolbar.addWidget(lbl_symbol)

        self._symbol_input = QLineEdit(self._current_symbol)
        self._symbol_input.setMaximumWidth(100)
        self._symbol_input.returnPressed.connect(self._on_load_chart)
        toolbar.addWidget(self._symbol_input)

        lbl_tf = QLabel("周期:")
        toolbar.addWidget(lbl_tf)

        self._timeframe_combo = QComboBox()
        for display, value in TIMEFRAMES.items():
            self._timeframe_combo.addItem(display, value)
        self._timeframe_combo.setCurrentText("日线")
        self._timeframe_combo.currentIndexChanged.connect(self._on_timeframe_changed)
        toolbar.addWidget(self._timeframe_combo)

        self._load_button = QPushButton("加载")
        self._load_button.clicked.connect(self._on_load_chart)
        toolbar.addWidget(self._load_button)

        toolbar.addStretch()

        # 指标叠加复选
        self._ma5_btn = QPushButton("MA5")
        self._ma5_btn.setCheckable(True)
        self._ma5_btn.setChecked(True)
        self._ma5_btn.setFixedWidth(50)
        self._ma5_btn.clicked.connect(self._on_toggle_indicators)
        toolbar.addWidget(self._ma5_btn)

        self._ma10_btn = QPushButton("MA10")
        self._ma10_btn.setCheckable(True)
        self._ma10_btn.setChecked(True)
        self._ma10_btn.setFixedWidth(55)
        self._ma10_btn.clicked.connect(self._on_toggle_indicators)
        toolbar.addWidget(self._ma10_btn)

        self._ma20_btn = QPushButton("MA20")
        self._ma20_btn.setCheckable(True)
        self._ma20_btn.setChecked(True)
        self._ma20_btn.setFixedWidth(55)
        self._ma20_btn.clicked.connect(self._on_toggle_indicators)
        toolbar.addWidget(self._ma20_btn)

        self._ma60_btn = QPushButton("MA60")
        self._ma60_btn.setCheckable(True)
        self._ma60_btn.setChecked(False)
        self._ma60_btn.setFixedWidth(55)
        self._ma60_btn.clicked.connect(self._on_toggle_indicators)
        toolbar.addWidget(self._ma60_btn)

        self._boll_btn = QPushButton("BOLL")
        self._boll_btn.setCheckable(True)
        self._boll_btn.setChecked(False)
        self._boll_btn.setFixedWidth(55)
        self._boll_btn.clicked.connect(self._on_toggle_indicators)
        toolbar.addWidget(self._boll_btn)

        layout.addLayout(toolbar)

        # ---- K 线图表 ----
        self._chart = CandlestickChart()
        layout.addWidget(self._chart, 3)

        # ---- 技术指标面板 ----
        indicators_widget = self._create_indicators_panel()
        layout.addWidget(indicators_widget, 0)

        return widget

    def _create_indicators_panel(self):
        """创建技术指标面板"""
        widget = QFrame()
        widget.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_PANEL};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
        """)
        widget.setMaximumHeight(140)
        widget.setMinimumHeight(100)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        title = QLabel("技术指标")
        title.setObjectName("sectionLabel")
        title.setStyleSheet(f"color: {COLOR_BLUE}; font-weight: bold; font-size: 13px; background: transparent;")
        layout.addWidget(title)

        # 指标网格
        grid = QGridLayout()
        grid.setSpacing(8)

        # MA 指标
        self._ind_labels = {}
        indicators = [
            ("MA5", 0, 0), ("MA10", 0, 1), ("MA20", 0, 2), ("MA60", 0, 3),
            ("RSI(14)", 0, 4), ("MACD", 1, 0),
            ("布林上轨", 1, 1), ("布林中轨", 1, 2), ("布林下轨", 1, 3),
            ("信号", 1, 4),
        ]
        for name, row, col in indicators:
            lbl_title = QLabel(name)
            lbl_title.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 11px; background: transparent;")
            lbl_value = QLabel("--")
            lbl_value.setStyleSheet(f"color: {COLOR_TEXT}; font-weight: bold; font-size: 13px; background: transparent;")
            container = QVBoxLayout()
            container.setSpacing(0)
            container.addWidget(lbl_title)
            container.addWidget(lbl_value)
            cell_widget = QWidget()
            cell_widget.setLayout(container)
            cell_widget.setStyleSheet("background: transparent;")
            grid.addWidget(cell_widget, row, col)
            self._ind_labels[name] = lbl_value

        layout.addLayout(grid)

        return widget

    def _create_right_panel(self):
        """创建右侧下单 + 订单历史面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # ---- 手动下单面板 ----
        order_panel = self._create_order_panel()
        layout.addWidget(order_panel, 0)

        # ---- 订单历史 ----
        history_panel = self._create_order_history_panel()
        layout.addWidget(history_panel, 1)

        return widget

    def _create_order_panel(self):
        """创建手动下单面板"""
        group = QGroupBox("手动下单")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        # 股票代码
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("代码:"))
        self._order_symbol = QLineEdit(self._current_symbol)
        self._order_symbol.setMaximumWidth(120)
        row1.addWidget(self._order_symbol)
        row1.addStretch()

        # 实时价格
        self._price_label = QLabel("现价: --")
        self._price_label.setStyleSheet(f"color: {COLOR_YELLOW}; font-weight: bold;")
        row1.addWidget(self._price_label)
        layout.addLayout(row1)

        # 买卖方向
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        self._buy_button = QPushButton("买入")
        self._buy_button.setObjectName("buyButton")
        self._buy_button.setCheckable(True)
        self._buy_button.setChecked(True)
        self._buy_button.clicked.connect(lambda: self._on_side_changed("buy"))

        self._sell_button = QPushButton("卖出")
        self._sell_button.setObjectName("sellButton")
        self._sell_button.setCheckable(True)
        self._sell_button.clicked.connect(lambda: self._on_side_changed("sell"))

        row2.addWidget(self._buy_button)
        row2.addWidget(self._sell_button)
        layout.addLayout(row2)

        # 数量
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("数量:"))
        self._qty_spin = QSpinBox()
        self._qty_spin.setRange(1, 100000)
        self._qty_spin.setValue(1)
        self._qty_spin.setSingleStep(1)
        row3.addWidget(self._qty_spin)

        # 快捷数量按钮
        for qty in [10, 50, 100]:
            btn = QPushButton(str(qty))
            btn.setFixedWidth(40)
            btn.clicked.connect(lambda checked, q=qty: self._qty_spin.setValue(q))
            row3.addWidget(btn)
        row3.addStretch()
        layout.addLayout(row3)

        # 订单类型
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("类型:"))
        self._order_type_combo = QComboBox()
        self._order_type_combo.addItem("市价", "market")
        self._order_type_combo.addItem("限价", "limit")
        self._order_type_combo.addItem("止损", "stop")
        self._order_type_combo.currentIndexChanged.connect(self._on_order_type_changed)
        row4.addWidget(self._order_type_combo)
        row4.addStretch()
        layout.addLayout(row4)

        # 限价/止损价格
        self._price_input_row = QHBoxLayout()
        self._price_input_row.addWidget(QLabel("价格:"))
        self._limit_price_spin = QDoubleSpinBox()
        self._limit_price_spin.setRange(0.01, 99999.99)
        self._limit_price_spin.setDecimals(2)
        self._limit_price_spin.setSingleStep(0.10)
        self._limit_price_spin.setValue(100.00)
        self._price_input_row.addWidget(self._limit_price_spin)
        self._price_input_row.addStretch()
        self._price_input_widget = QWidget()
        self._price_input_widget.setLayout(self._price_input_row)
        self._price_input_widget.setVisible(False)
        layout.addWidget(self._price_input_widget)

        # 下单按钮
        self._place_order_button = QPushButton("提交买入订单")
        self._place_order_button.setObjectName("buyButton")
        self._place_order_button.clicked.connect(self._on_place_order)
        layout.addWidget(self._place_order_button)

        # 快捷操作
        row5 = QHBoxLayout()
        row5.setSpacing(4)
        self._close_position_btn = QPushButton("平仓")
        self._close_position_btn.clicked.connect(self._on_close_position)
        row5.addWidget(self._close_position_btn)

        self._flatten_btn = QPushButton("全平")
        self._flatten_btn.setStyleSheet(f"background-color: {COLOR_RED}; color: white; font-weight: bold;")
        self._flatten_btn.clicked.connect(self._on_flatten_all)
        row5.addWidget(self._flatten_btn)
        layout.addLayout(row5)

        return group

    def _create_order_history_panel(self):
        """创建订单历史面板"""
        group = QGroupBox("订单历史")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)

        headers = ["订单ID", "代码", "方向", "数量", "类型", "状态", "成交价", "时间"]
        self._order_history_table = QTableWidget()
        setup_table(self._order_history_table, headers)
        layout.addWidget(self._order_history_table)

        return group

    # ============================================================
    # 事件处理
    # ============================================================

    def _on_side_changed(self, side):
        """买卖方向切换"""
        self._current_side = side
        if side == "buy":
            self._buy_button.setChecked(True)
            self._sell_button.setChecked(False)
            self._place_order_button.setText("提交买入订单")
            self._place_order_button.setObjectName("buyButton")
            self._place_order_button.setStyleSheet("")  # 重置样式以应用 objectName
        else:
            self._buy_button.setChecked(False)
            self._sell_button.setChecked(True)
            self._place_order_button.setText("提交卖出订单")
            self._place_order_button.setObjectName("sellButton")
            self._place_order_button.setStyleSheet("")

        # 强制刷新样式
        self._place_order_button.style().unpolish(self._place_order_button)
        self._place_order_button.style().polish(self._place_order_button)

    def _on_order_type_changed(self):
        """订单类型切换，显示/隐藏价格输入"""
        order_type = self._order_type_combo.currentData()
        self._price_input_widget.setVisible(order_type != "market")

    def _on_load_chart(self):
        """加载 K 线图"""
        symbol = self._symbol_input.text().strip().upper()
        if not symbol:
            QMessageBox.warning(self, "提示", "请输入股票代码")
            return

        self._current_symbol = symbol
        self._order_symbol.setText(symbol)
        self._load_chart_data()

    def _on_timeframe_changed(self):
        """时间周期切换"""
        self._current_timeframe = self._timeframe_combo.currentData()
        self._load_chart_data()

    def _on_toggle_indicators(self):
        """切换指标显示"""
        self._load_chart_data()

    def _load_chart_data(self):
        """加载 K 线数据并更新图表"""
        try:
            df = self._engine.get_bars(self._current_symbol, self._current_timeframe, limit=100)
            if df is None or len(df) == 0:
                QMessageBox.information(self, "提示", f"未获取到 {self._current_symbol} 的K线数据")
                return

            # 计算技术指标
            df = self._calc_indicators(df)

            # 根据用户选择过滤要显示的指标
            display_df = df.copy()
            if not self._ma5_btn.isChecked() and 'MA5' in display_df.columns:
                display_df = display_df.drop(columns=['MA5'])
            if not self._ma10_btn.isChecked() and 'MA10' in display_df.columns:
                display_df = display_df.drop(columns=['MA10'])
            if not self._ma20_btn.isChecked() and 'MA20' in display_df.columns:
                display_df = display_df.drop(columns=['MA20'])
            if not self._ma60_btn.isChecked() and 'MA60' in display_df.columns:
                display_df = display_df.drop(columns=['MA60'])
            if not self._boll_btn.isChecked():
                for col in ['BOLL_UPPER', 'BOLL_LOWER', 'BOLL_MID']:
                    if col in display_df.columns:
                        display_df = display_df.drop(columns=[col])

            # 更新图表
            self._chart.set_data(display_df)

            # 更新指标面板
            self._update_indicators_panel(df)

            # 更新价格
            self._update_current_price()

        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载K线数据失败:\n{str(e)}")

    def _calc_indicators(self, df):
        """
        计算技术指标。

        参数:
            df: 含 OHLCV 的 DataFrame

        返回:
            添加了指标列的 DataFrame
        """
        try:
            # 尝试使用项目的指标模块
            from indicators import calc_all_indicators
            df = calc_all_indicators(df)
        except ImportError:
            # 内置计算
            df = self._calc_indicators_builtin(df)
        return df

    def _calc_indicators_builtin(self, df):
        """内置技术指标计算（当 indicators 模块不可用时使用）"""
        # MA 均线
        for period in [5, 10, 20, 60]:
            df[f'MA{period}'] = df['Close'].rolling(window=period).mean()

        # 布林带
        boll_period = 20
        boll_std = 2
        df['BOLL_MID'] = df['Close'].rolling(window=boll_period).mean()
        boll_std_val = df['Close'].rolling(window=boll_period).std()
        df['BOLL_UPPER'] = df['BOLL_MID'] + boll_std * boll_std_val
        df['BOLL_LOWER'] = df['BOLL_MID'] - boll_std * boll_std_val

        # RSI
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1.0 / 14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0 / 14, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        df['RSI'] = 100 - (100 / (1 + rs))
        df['RSI'] = df['RSI'].fillna(100)

        # MACD
        ema_fast = df['Close'].ewm(span=12, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=26, adjust=False).mean()
        df['DIF'] = ema_fast - ema_slow
        df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
        df['MACD_HIST'] = 2 * (df['DIF'] - df['DEA'])

        return df

    def _update_indicators_panel(self, df):
        """
        更新技术指标面板显示。

        参数:
            df: 含指标列的 DataFrame
        """
        if df is None or len(df) == 0:
            return

        last = df.iloc[-1]

        def get_val(col):
            """安全获取指标值"""
            if col in df.columns:
                val = last.get(col)
                if val is not None and not (isinstance(val, float) and np.isnan(val)):
                    return float(val)
            return None

        def set_ind(name, col, fmt="{:.2f}", color=None):
            """设置指标显示"""
            val = get_val(col)
            label = self._ind_labels.get(name)
            if label is None:
                return
            if val is not None:
                label.setText(fmt.format(val))
                if color:
                    label.setStyleSheet(
                        f"color: {color}; font-weight: bold; font-size: 13px; background: transparent;"
                    )
            else:
                label.setText("--")
                label.setStyleSheet(
                    f"color: {COLOR_TEXT_DIM}; font-weight: bold; font-size: 13px; background: transparent;"
                )

        # MA
        set_ind("MA5", "MA5")
        set_ind("MA10", "MA10")
        set_ind("MA20", "MA20")
        set_ind("MA60", "MA60")

        # RSI
        rsi_val = get_val("RSI")
        if rsi_val is not None:
            rsi_color = COLOR_RED if rsi_val > 70 else (COLOR_GREEN if rsi_val < 30 else COLOR_TEXT)
            set_ind("RSI(14)", "RSI", "{:.1f}", rsi_color)

        # MACD
        dif_val = get_val("DIF")
        dea_val = get_val("DEA")
        hist_val = get_val("MACD_HIST")
        if dif_val is not None and dea_val is not None:
            macd_text = f"DIF:{dif_val:.2f} DEA:{dea_val:.2f}"
            self._ind_labels["MACD"].setText(macd_text)
            macd_color = COLOR_GREEN if hist_val and hist_val > 0 else COLOR_RED
            self._ind_labels["MACD"].setStyleSheet(
                f"color: {macd_color}; font-weight: bold; font-size: 12px; background: transparent;"
            )

        # 布林带
        set_ind("布林上轨", "BOLL_UPPER")
        set_ind("布林中轨", "BOLL_MID")
        set_ind("布林下轨", "BOLL_LOWER")

        # 综合信号
        signal_text = self._generate_signal(df)
        signal_label = self._ind_labels.get("信号")
        if signal_label:
            signal_label.setText(signal_text["text"])
            signal_label.setStyleSheet(
                f"color: {signal_text['color']}; font-weight: bold; font-size: 12px; background: transparent;"
            )

    def _generate_signal(self, df):
        """
        根据技术指标生成综合信号。

        参数:
            df: 含指标列的 DataFrame

        返回:
            {"text": 信号文本, "color": 颜色}
        """
        if df is None or len(df) < 2:
            return {"text": "--", "color": COLOR_TEXT_DIM}

        last = df.iloc[-1]
        prev = df.iloc[-2]

        score = 0
        signals = []

        # RSI 信号
        rsi = last.get("RSI")
        if rsi is not None and not (isinstance(rsi, float) and np.isnan(rsi)):
            if rsi < 30:
                score += 1
                signals.append("RSI超卖")
            elif rsi > 70:
                score -= 1
                signals.append("RSI超买")

        # MACD 信号
        dif = last.get("DIF")
        dea = last.get("DEA")
        prev_dif = prev.get("DIF")
        prev_dea = prev.get("DEA")
        if all(v is not None and not (isinstance(v, float) and np.isnan(v))
               for v in [dif, dea, prev_dif, prev_dea]):
            if prev_dif < prev_dea and dif > dea:
                score += 1
                signals.append("MACD金叉")
            elif prev_dif > prev_dea and dif < dea:
                score -= 1
                signals.append("MACD死叉")

        # MA 趋势
        ma5 = last.get("MA5")
        ma20 = last.get("MA20")
        if ma5 is not None and ma20 is not None:
            if not (isinstance(ma5, float) and np.isnan(ma5)):
                if not (isinstance(ma20, float) and np.isnan(ma20)):
                    if ma5 > ma20:
                        score += 0.5
                    else:
                        score -= 0.5

        # 布林带
        boll_up = last.get("BOLL_UPPER")
        boll_low = last.get("BOLL_LOWER")
        close = last.get("Close")
        if all(v is not None and not (isinstance(v, float) and np.isnan(v))
               for v in [boll_up, boll_low, close]):
            if close > boll_up:
                score -= 0.5
                signals.append("突破布林上轨")
            elif close < boll_low:
                score += 0.5
                signals.append("跌破布林下轨")

        # 综合判断
        if score >= 1.5:
            return {"text": "看多", "color": COLOR_GREEN}
        elif score >= 0.5:
            return {"text": "偏多", "color": COLOR_GREEN}
        elif score <= -1.5:
            return {"text": "看空", "color": COLOR_RED}
        elif score <= -0.5:
            return {"text": "偏空", "color": COLOR_RED}
        else:
            return {"text": "震荡", "color": COLOR_YELLOW}

    def _update_current_price(self):
        """更新当前股票的实时价格"""
        try:
            price = self._engine.get_latest_price(self._current_symbol)
            if price:
                self._price_label.setText(f"现价: ${format_price(price)}")
                # 更新限价输入框默认值
                self._limit_price_spin.setValue(float(price))
        except Exception:
            pass

    def _on_place_order(self):
        """提交订单"""
        symbol = self._order_symbol.text().strip().upper()
        if not symbol:
            QMessageBox.warning(self, "提示", "请输入股票代码")
            return

        qty = self._qty_spin.value()
        if qty <= 0:
            QMessageBox.warning(self, "提示", "数量必须大于0")
            return

        side = self._current_side
        order_type = self._order_type_combo.currentData()
        side_text = "买入" if side == "buy" else "卖出"

        # 构建确认信息
        msg_lines = [f"确认提交以下订单？", "", f"代码: {symbol}", f"方向: {side_text}", f"数量: {qty}"]
        if order_type == "market":
            msg_lines.append(f"类型: 市价")
        elif order_type == "limit":
            limit_price = self._limit_price_spin.value()
            msg_lines.append(f"类型: 限价")
            msg_lines.append(f"限价: ${format_price(limit_price)}")
        elif order_type == "stop":
            stop_price = self._limit_price_spin.value()
            msg_lines.append(f"类型: 止损")
            msg_lines.append(f"止损价: ${format_price(stop_price)}")

        reply = QMessageBox.question(
            self, "确认下单", "\n".join(msg_lines),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # 提交订单
        try:
            if order_type == "market":
                result = self._engine.place_market_order(symbol, qty, side)
            elif order_type == "limit":
                limit_price = self._limit_price_spin.value()
                result = self._engine.place_limit_order(symbol, qty, side, limit_price)
            elif order_type == "stop":
                stop_price = self._limit_price_spin.value()
                result = self._engine.place_stop_order(symbol, qty, side, stop_price)
            else:
                QMessageBox.warning(self, "错误", "未知订单类型")
                return

            if result:
                QMessageBox.information(self, "成功", f"订单已提交\n{str(result)}")
                self._refresh_order_history()
            else:
                QMessageBox.warning(self, "失败", "订单提交失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"下单失败:\n{str(e)}")

    def _on_close_position(self):
        """平仓当前股票"""
        symbol = self._order_symbol.text().strip().upper()
        if not symbol:
            QMessageBox.warning(self, "提示", "请输入股票代码")
            return

        reply = QMessageBox.question(
            self, "确认平仓",
            f"确认平仓 {symbol} 的全部持仓？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            result = self._engine.close_position(symbol)
            if result:
                QMessageBox.information(self, "成功", f"平仓指令已提交\n{str(result)}")
                self._refresh_order_history()
            else:
                QMessageBox.warning(self, "失败", "平仓失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"平仓失败:\n{str(e)}")

    def _on_flatten_all(self):
        """全平所有持仓"""
        reply = QMessageBox.question(
            self, "确认全平",
            "确认平仓所有持仓？此操作不可撤销！",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            results = self._engine.flatten_all()
            if results:
                QMessageBox.information(self, "成功", f"已提交 {len(results)} 个平仓指令")
                self._refresh_order_history()
            else:
                QMessageBox.information(self, "提示", "没有需要平仓的持仓")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"全平失败:\n{str(e)}")

    # ============================================================
    # 数据刷新
    # ============================================================

    def refresh(self):
        """
        刷新交易标签页数据。

        由主窗口 QTimer 定时调用。刷新订单历史和当前价格。
        K 线图不自动刷新（需要用户手动加载），避免频繁请求。
        """
        self._refresh_order_history()
        self._update_current_price()

    def _refresh_order_history(self):
        """刷新订单历史表格"""
        try:
            orders = self._engine.get_orders(status='all')
            if not orders:
                orders = []

            orders = orders[:50]  # 最多显示50条

            clear_table(self._order_history_table)
            self._order_history_table.setRowCount(len(orders))

            for row, order in enumerate(orders):
                order_id = str(order.get('id', '--'))[-8:]
                symbol = order.get('symbol', '--')
                side = order.get('side', '--')
                qty = order.get('qty', 0)
                order_type = order.get('type', '--')
                status = order.get('status', '--')
                filled_price = order.get('filled_price', 0)
                updated_at = order.get('updated_at', order.get('created_at', ''))

                set_cell(self._order_history_table, row, 0, order_id)
                set_cell(self._order_history_table, row, 1, symbol)

                side_color = color_for_side(side)
                set_cell(self._order_history_table, row, 2, side.upper() if side else '--',
                         brush=QBrush(side_color))
                set_cell(self._order_history_table, row, 3, format_number(qty),
                         sort_key=qty, alignment=Qt.AlignRight | Qt.AlignVCenter)
                set_cell(self._order_history_table, row, 4, str(order_type))

                # 状态颜色
                status_lower = str(status).lower()
                if status_lower in ('filled', 'complete', 'done'):
                    status_brush = QBrush(QColor(COLOR_GREEN))
                elif status_lower in ('cancelled', 'canceled', 'rejected', 'expired'):
                    status_brush = QBrush(QColor(COLOR_RED))
                elif status_lower in ('pending', 'new', 'open', 'partial'):
                    status_brush = QBrush(QColor(COLOR_YELLOW))
                else:
                    status_brush = QBrush(QColor(COLOR_TEXT_DIM))
                set_cell(self._order_history_table, row, 5, str(status),
                         brush=status_brush)

                set_cell(self._order_history_table, row, 6,
                         format_price(filled_price) if filled_price else "--",
                         sort_key=filled_price if filled_price else 0,
                         alignment=Qt.AlignRight | Qt.AlignVCenter)
                set_cell(self._order_history_table, row, 7, format_datetime(updated_at))

            self._order_history_table.setSortingEnabled(True)
        except Exception:
            pass

    def load_default_chart(self):
        """加载默认股票的K线图"""
        self._load_chart_data()
