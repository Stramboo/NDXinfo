# -*- coding: utf-8 -*-
"""
美股交易系统 - 图形化主窗口

包含4个功能标签页：
- 仪表盘: 账户概览、持仓汇总、资产曲线
- 交易:   手动买卖、K线图表、订单历史
- 策略:   策略选择与参数配置、信号监控
- 日志:   实时运行日志输出
"""

import sys
import threading
import time
from datetime import datetime

import pandas as pd

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QGroupBox,
    QPlainTextEdit, QStatusBar, QSplitter, QFrame, QGridLayout,
    QMessageBox, QApplication, QCheckBox, QRadioButton, QButtonGroup,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor, QIcon

from gui.styles import (
    BG_DARK, BG_PANEL, BG_CARD, BG_INPUT, BG_HOVER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ACCENT,
    GREEN, RED, YELLOW, ORANGE, BORDER,
    BTN_PRIMARY, BTN_PRIMARY_HOVER, BTN_DANGER, BTN_DANGER_HOVER,
    BTN_DEFAULT, BTN_DEFAULT_HOVER,
    GLOBAL_STYLESHEET,
)
from gui.chart_widget import StockChartWidget
from trading.trading_engine import TradingEngine
from trading.strategy import Signal, SignalAction, STRATEGY_REGISTRY
from indicators import calc_all_indicators


class TraderMainWindow(QMainWindow):
    """交易系统主窗口"""

    def __init__(self, engine: TradingEngine = None):
        super().__init__()
        self.setWindowTitle("美股自动交易系统 v1.0")
        self.resize(1400, 900)
        self.setMinimumSize(1100, 700)

        # 交易引擎
        self.engine = engine or TradingEngine(broker_type="simulation")
        self._dashboard_timer = QTimer(self)
        self._dashboard_timer.timeout.connect(self._refresh_dashboard)
        self._dashboard_timer.start(3000)  # 每3秒刷新

        # 日志缓存
        self._log_buffer: list[str] = []
        self._max_log_lines = 500

        # 当前选中的股票（用于图表）
        self._selected_symbol: str = ""

        # 初始化UI
        self._init_ui()
        self._connect_engine()

        # 加载初始数据
        QTimer.singleShot(500, self._initial_load)

    # ----------------------------------------------------------
    # UI 初始化
    # ----------------------------------------------------------

    def _init_ui(self):
        """初始化界面"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # 顶部标题栏
        header = self._create_header()
        main_layout.addWidget(header)

        # 标签页
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_dashboard_tab(), " 仪表盘 ")
        self.tabs.addTab(self._create_trading_tab(), " 交易 ")
        self.tabs.addTab(self._create_strategy_tab(), " 策略 ")
        self.tabs.addTab(self._create_log_tab(), " 日志 ")
        main_layout.addWidget(self.tabs, 1)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)

        # 应用主题
        self.setStyleSheet(GLOBAL_STYLESHEET)

    def _create_header(self):
        """创建顶部标题栏"""
        frame = QFrame()
        frame.setObjectName("panel")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 8, 16, 8)

        title = QLabel("美股自动交易系统")
        title.setObjectName("title")
        title.setStyleSheet(f"color: {TEXT_ACCENT}; font-size: 20px;")

        subtitle = QLabel("  |  模拟券商  |  多指标综合策略")
        subtitle.setObjectName("subtitle")

        self.auto_status = QLabel("● 手动模式")
        self.auto_status.setStyleSheet(f"color: {TEXT_MUTED}; font-weight: bold; font-size: 14px;")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()
        layout.addWidget(self.auto_status)
        return frame

    # ----------------------------------------------------------
    # 仪表盘标签页
    # ----------------------------------------------------------

    def _create_dashboard_tab(self) -> QWidget:
        """创建仪表盘"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 账户概览卡片
        account_group = QGroupBox("账户概览")
        account_grid = QGridLayout(account_group)
        account_grid.setVerticalSpacing(8)

        self.dash_equity = self._dash_value_label("$0")
        self.dash_cash = self._dash_value_label("$0")
        self.dash_market_value = self._dash_value_label("$0")
        self.dash_return = self._dash_value_label("0%")
        self.dash_daily_pnl = self._dash_value_label("$0")
        self.dash_positions_count = self._dash_value_label("0")

        account_grid.addWidget(QLabel("总资产"), 0, 0)
        account_grid.addWidget(self.dash_equity, 0, 1)
        account_grid.addWidget(QLabel("可用现金"), 0, 2)
        account_grid.addWidget(self.dash_cash, 0, 3)
        account_grid.addWidget(QLabel("持仓市值"), 0, 4)
        account_grid.addWidget(self.dash_market_value, 0, 5)

        account_grid.addWidget(QLabel("总收益率"), 1, 0)
        account_grid.addWidget(self.dash_return, 1, 1)
        account_grid.addWidget(QLabel("未实现盈亏"), 1, 2)
        account_grid.addWidget(self.dash_daily_pnl, 1, 3)
        account_grid.addWidget(QLabel("持仓数量"), 1, 4)
        account_grid.addWidget(self.dash_positions_count, 1, 5)

        # 控制按钮
        btn_layout = QHBoxLayout()
        self.btn_auto_start = QPushButton("▶ 启动自动交易")
        self.btn_auto_start.setObjectName("primary")
        self.btn_auto_start.clicked.connect(self._toggle_auto)

        self.btn_refresh = QPushButton("↻ 刷新")
        self.btn_refresh.clicked.connect(self._refresh_dashboard)

        self.btn_reset = QPushButton("重置账户")
        self.btn_reset.setObjectName("danger")
        self.btn_reset.clicked.connect(self._reset_account)

        btn_layout.addWidget(self.btn_auto_start)
        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_reset)

        # 持仓表格
        pos_group = QGroupBox("当前持仓")
        pos_layout = QVBoxLayout(pos_group)

        self.pos_table = QTableWidget()
        self.pos_table.setColumnCount(8)
        self.pos_table.setHorizontalHeaderLabels([
            "代码", "数量", "成本价", "现价", "市值", "盈亏", "盈亏%", "操作"
        ])
        self.pos_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.pos_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.pos_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.pos_table.clicked.connect(self._on_position_clicked)
        pos_layout.addWidget(self.pos_table)

        layout.addWidget(account_group)
        layout.addLayout(btn_layout)
        layout.addWidget(pos_group, 1)
        return widget

    def _dash_value_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("value")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"color: {TEXT_ACCENT}; font-size: 18px; font-weight: bold;")
        return label

    # ----------------------------------------------------------
    # 交易标签页
    # ----------------------------------------------------------

    def _create_trading_tab(self) -> QWidget:
        """创建交易标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 上下分割
        splitter = QSplitter(Qt.Vertical)

        # 上半部分：K线图
        chart_panel = QFrame()
        chart_panel.setObjectName("panel")
        chart_layout = QVBoxLayout(chart_panel)
        self.chart_widget = StockChartWidget()
        chart_layout.addWidget(self.chart_widget)
        splitter.addWidget(chart_panel)

        # 下半部分：交易面板 + 订单历史
        bottom = QWidget()
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(0, 4, 0, 0)
        bottom_layout.setSpacing(8)

        # 交易面板
        trade_panel = QGroupBox("手动交易")
        trade_layout = QVBoxLayout(trade_panel)

        # 股票选择
        trade_layout.addWidget(QLabel("股票代码"))
        self.trade_symbol = QComboBox()
        self.trade_symbol.setEditable(True)
        self.trade_symbol.setMinimumHeight(32)
        self.trade_symbol.lineEdit().setPlaceholderText("输入代码, 如 AAPL")
        self.trade_symbol.currentTextChanged.connect(self._on_trade_symbol_changed)
        trade_layout.addWidget(self.trade_symbol)

        # 数量
        trade_layout.addWidget(QLabel("交易数量"))
        qty_layout = QHBoxLayout()
        self.trade_qty = QSpinBox()
        self.trade_qty.setMinimum(1)
        self.trade_qty.setMaximum(99999)
        self.trade_qty.setValue(10)
        self.trade_qty.setMinimumHeight(32)

        self.trade_price_label = QLabel("市价: --")
        self.trade_price_label.setObjectName("muted")
        qty_layout.addWidget(self.trade_qty)
        qty_layout.addWidget(self.trade_price_label)
        trade_layout.addLayout(qty_layout)

        # 买入/卖出按钮
        trade_layout.addSpacing(8)
        self.btn_buy = QPushButton("买入")
        self.btn_buy.setObjectName("buy")
        self.btn_buy.clicked.connect(self._manual_buy)

        self.btn_sell = QPushButton("卖出")
        self.btn_sell.setObjectName("sell")
        self.btn_sell.clicked.connect(self._manual_sell)

        trade_layout.addWidget(self.btn_buy)
        trade_layout.addWidget(self.btn_sell)

        # 全部卖出
        self.btn_sell_all = QPushButton("全部清仓")
        self.btn_sell_all.setObjectName("danger")
        self.btn_sell_all.clicked.connect(self._sell_all)
        trade_layout.addWidget(self.btn_sell_all)
        trade_layout.addStretch()

        # 订单历史面板
        order_panel = QGroupBox("订单历史")
        order_layout = QVBoxLayout(order_panel)

        self.order_table = QTableWidget()
        self.order_table.setColumnCount(7)
        self.order_table.setHorizontalHeaderLabels([
            "时间", "代码", "方向", "数量", "成交价", "状态", "备注"
        ])
        self.order_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.order_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.order_table.setSelectionBehavior(QTableWidget.SelectRows)
        order_layout.addWidget(self.order_table)

        bottom_layout.addWidget(trade_panel, 1)
        bottom_layout.addWidget(order_panel, 3)

        splitter.addWidget(bottom)
        splitter.setSizes([500, 300])

        layout.addWidget(splitter)
        return widget

    # ----------------------------------------------------------
    # 策略标签页
    # ----------------------------------------------------------

    def _create_strategy_tab(self) -> QWidget:
        """创建策略标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 策略选择
        strategy_group = QGroupBox("策略配置")
        strategy_layout = QVBoxLayout(strategy_group)

        sel_layout = QHBoxLayout()
        sel_layout.addWidget(QLabel("当前策略:"))
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "多指标综合 (推荐)", "MACD金叉死叉", "RSI超买超卖",
            "均线趋势跟踪", "布林带突破"
        ])
        self.strategy_combo.currentIndexChanged.connect(self._on_strategy_changed)
        sel_layout.addWidget(self.strategy_combo)
        sel_layout.addStretch()
        strategy_layout.addLayout(sel_layout)

        # 策略描述
        self.strategy_desc = QLabel(
            "综合MACD、RSI、均线趋势、布林带四个子策略，通过加权投票机制生成交易信号。\n"
            "权重: MACD 30%, RSI 25%, 均线 25%, 布林带 20%"
        )
        self.strategy_desc.setWordWrap(True)
        self.strategy_desc.setStyleSheet(f"color: {TEXT_MUTED}; padding: 8px;")
        strategy_layout.addWidget(self.strategy_desc)

        # 策略状态
        status_layout = QHBoxLayout()
        self.strategy_enabled_check = QCheckBox("启用策略")
        self.strategy_enabled_check.setChecked(True)
        self.strategy_enabled_check.toggled.connect(self._toggle_strategy)
        self.strategy_status = QLabel("运行中")
        self.strategy_status.setStyleSheet(f"color: {GREEN}; font-weight: bold;")
        status_layout.addWidget(self.strategy_enabled_check)
        status_layout.addWidget(self.strategy_status)
        status_layout.addStretch()
        strategy_layout.addLayout(status_layout)

        layout.addWidget(strategy_group)

        # 风险参数
        risk_group = QGroupBox("风险管理")
        risk_layout = QGridLayout(risk_group)
        risk_layout.setVerticalSpacing(6)

        risk_params = [
            ("单只最大仓位", "25%", "止损比例", "-8%"),
            ("总仓位上限", "80%", "止盈比例", "+20%"),
            ("最大持仓数", "8只", "追踪止损", "-5%"),
            ("单日最大亏损", "$5,000", "单笔最大金额", "$50,000"),
        ]
        for r, row in enumerate(risk_params):
            for c in range(0, 4, 2):
                key_btn = QPushButton(row[c])
                key_btn.setEnabled(False)
                key_btn.setStyleSheet(f"background: {BG_CARD}; border: 1px solid {BORDER};")
                val = QLabel(row[c + 1])
                val.setStyleSheet(f"color: {TEXT_ACCENT}; font-weight: bold; font-size: 14px;")
                val.setAlignment(Qt.AlignCenter)
                sub_layout = QHBoxLayout()
                sub_layout.addWidget(key_btn)
                sub_layout.addWidget(val)
                risk_layout.addLayout(sub_layout, r, c // 2)

        layout.addWidget(risk_group)

        # 信号监控
        signal_group = QGroupBox("最近信号 (自动刷新)")
        signal_layout = QVBoxLayout(signal_group)

        self.signal_table = QTableWidget()
        self.signal_table.setColumnCount(5)
        self.signal_table.setHorizontalHeaderLabels([
            "时间", "代码", "信号", "强度", "原因"
        ])
        self.signal_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.signal_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        signal_layout.addWidget(self.signal_table)

        layout.addWidget(signal_group, 1)
        return widget

    # ----------------------------------------------------------
    # 日志标签页
    # ----------------------------------------------------------

    def _create_log_tab(self) -> QWidget:
        """创建日志标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumBlockCount(self._max_log_lines)

        layout.addWidget(self.log_output)
        return widget

    # ----------------------------------------------------------
    # 引擎连接
    # ----------------------------------------------------------

    def _connect_engine(self):
        """连接交易引擎回调"""
        self.engine.on_status_changed(self._on_engine_status)
        self.engine.on_signal(self._on_engine_signal)
        self.engine.on_log(self._on_engine_log)

    def _on_engine_status(self, status: dict):
        """引擎状态更新回调（后台线程）"""
        # 使用 QTimer 安全跨线程
        QTimer.singleShot(0, lambda: self._refresh_dashboard())

    def _on_engine_signal(self, signal: Signal):
        """策略信号回调"""
        row_data = [
            signal.timestamp,
            signal.symbol,
            signal.action.value,
            f"{signal.strength:.2f}",
            signal.reason,
        ]
        QTimer.singleShot(0, lambda: self._add_signal_row(row_data))

    def _on_engine_log(self, msg: str):
        """日志回调"""
        self._log_buffer.append(msg)
        if len(self._log_buffer) > 50:
            self._log_buffer = self._log_buffer[-50:]

    # ----------------------------------------------------------
    # 初始数据加载
    # ----------------------------------------------------------

    def _initial_load(self):
        """初始数据加载（异步）"""
        self._append_log("正在加载历史数据...")
        self.status_label.setText("加载数据中...")

        def _load():
            # 加载标的列表到下拉框
            symbols = self.engine.market_data.get_symbols()
            for sym in symbols:
                self.trade_symbol.addItem(sym)

            # 加载第一只股票的图表
            if symbols:
                self._selected_symbol = symbols[0]
                df = self.engine.market_data.fetch_history(symbols[0])
                if not df.empty:
                    df = calc_all_indicators(df)
                    self.chart_widget.set_data(df.tail(120), symbols[0])

            self._append_log("数据加载完成，系统就绪。")
            self.status_label.setText("就绪")

        threading.Thread(target=_load, daemon=True).start()

    # ----------------------------------------------------------
    # 仪表盘刷新
    # ----------------------------------------------------------

    def _refresh_dashboard(self):
        """刷新仪表盘数据"""
        try:
            data = self.engine.get_dashboard_data()

            self.dash_equity.setText(f"${data['equity']:,.2f}")
            self.dash_cash.setText(f"${data['cash']:,.2f}")
            self.dash_market_value.setText(f"${data['market_value']:,.2f}")

            ret = data['total_return_pct']
            color = GREEN if ret >= 0 else RED
            self.dash_return.setText(f"{ret:+.2f}%")
            self.dash_return.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold;")

            pnl = data['daily_pnl']
            pnl_color = GREEN if pnl >= 0 else RED
            self.dash_daily_pnl.setText(f"${pnl:+,.2f}")
            self.dash_daily_pnl.setStyleSheet(f"color: {pnl_color}; font-size: 18px; font-weight: bold;")

            self.dash_positions_count.setText(str(data['position_count']))

            # 发动机状态
            if self.engine.is_auto_running:
                self.auto_status.setText("● 自动交易中")
                self.auto_status.setStyleSheet(f"color: {GREEN}; font-weight: bold; font-size: 14px;")
                self.btn_auto_start.setText("■ 停止自动交易")
                self.btn_auto_start.setObjectName("danger")
            else:
                self.auto_status.setText("● 手动模式")
                self.auto_status.setStyleSheet(f"color: {TEXT_MUTED}; font-weight: bold; font-size: 14px;")
                self.btn_auto_start.setText("▶ 启动自动交易")
                self.btn_auto_start.setObjectName("primary")

            # 刷新持仓表
            self._refresh_positions()

            # 刷新订单表
            self._refresh_orders()

            # 刷新日志
            self._flush_logs()

        except Exception as e:
            self._append_log(f"刷新异常: {e}")

    def _refresh_positions(self):
        """刷新持仓表格"""
        status = self.engine.get_status()
        positions = status["positions"]
        self.pos_table.setRowCount(len(positions))

        for i, pos in enumerate(positions):
            self.pos_table.setItem(i, 0, self._table_item(pos["symbol"]))
            self.pos_table.setItem(i, 1, self._table_item(str(pos["quantity"]), Qt.AlignRight))
            self.pos_table.setItem(i, 2, self._table_item(f"${pos['avg_cost']:.2f}", Qt.AlignRight))
            self.pos_table.setItem(i, 3, self._table_item(f"${pos['current_price']:.2f}", Qt.AlignRight))
            self.pos_table.setItem(i, 4, self._table_item(f"${pos['market_value']:,.0f}", Qt.AlignRight))

            pnl = pos["unrealized_pnl"]
            pnl_pct = pos["unrealized_pnl_pct"]
            pnl_item = self._table_item(f"${pnl:+,.2f}", Qt.AlignRight)
            pnl_item.setForeground(QColor(GREEN if pnl >= 0 else RED))
            self.pos_table.setItem(i, 5, pnl_item)

            pnl_pct_item = self._table_item(f"{pnl_pct:+.2f}%", Qt.AlignRight)
            pnl_pct_item.setForeground(QColor(GREEN if pnl >= 0 else RED))
            self.pos_table.setItem(i, 6, pnl_pct_item)

            sell_btn = QPushButton("卖出")
            sell_btn.setObjectName("danger")
            sell_btn.setMaximumHeight(28)
            symbol = pos["symbol"]
            sell_btn.clicked.connect(lambda checked, s=symbol: self._quick_sell(s))
            self.pos_table.setCellWidget(i, 7, sell_btn)

    def _refresh_orders(self):
        """刷新订单历史表格"""
        status = self.engine.get_status()
        orders = status["recent_orders"]
        self.order_table.setRowCount(len(orders))

        for i, o in enumerate(orders):
            self.order_table.setItem(i, 0, self._table_item(o["created_at"]))
            self.order_table.setItem(i, 1, self._table_item(o["symbol"]))
            self.order_table.setItem(i, 2, self._table_item(o["side"].upper()))
            self.order_table.setItem(i, 3, self._table_item(str(o["quantity"]), Qt.AlignRight))
            self.order_table.setItem(i, 4, self._table_item(f"${o['avg_fill_price']:.2f}", Qt.AlignRight))

            status_item = self._table_item(o["status"])
            status_color = GREEN if o["status"] == "filled" else (RED if o["status"] == "rejected" else YELLOW)
            status_item.setForeground(QColor(status_color))
            self.order_table.setItem(i, 5, status_item)

            self.order_table.setItem(i, 6, self._table_item(o.get("note", "")))

    def _table_item(self, text: str, alignment=Qt.AlignLeft) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(alignment | Qt.AlignVCenter)
        return item

    # ----------------------------------------------------------
    # 交易操作
    # ----------------------------------------------------------

    def _manual_buy(self):
        """手动买入"""
        symbol = self.trade_symbol.currentText().strip().upper()
        if not symbol:
            QMessageBox.warning(self, "错误", "请选择或输入股票代码")
            return

        quantity = self.trade_qty.value()
        if quantity <= 0:
            QMessageBox.warning(self, "错误", "请输入有效的交易数量")
            return

        reply = QMessageBox.question(
            self, "确认买入",
            f"确认买入 {symbol} x{quantity} 股？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self._append_log(f"手动下单: BUY {symbol} x{quantity}")
        self.engine.manual_buy(symbol, quantity)
        self._refresh_dashboard()

    def _manual_sell(self):
        """手动卖出"""
        symbol = self.trade_symbol.currentText().strip().upper()
        if not symbol:
            QMessageBox.warning(self, "错误", "请选择或输入股票代码")
            return

        pos = self.engine.broker.get_position(symbol)
        if pos is None:
            QMessageBox.warning(self, "无持仓", f"没有 {symbol} 的持仓")
            return

        quantity = self.trade_qty.value()
        quantity = min(quantity, pos.quantity)

        reply = QMessageBox.question(
            self, "确认卖出",
            f"确认卖出 {symbol} x{quantity} 股？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self._append_log(f"手动下单: SELL {symbol} x{quantity}")
        self.engine.manual_sell(symbol, quantity)
        self._refresh_dashboard()

    def _quick_sell(self, symbol: str):
        """从持仓表快速卖出"""
        pos = self.engine.broker.get_position(symbol)
        if pos is None:
            return
        self._append_log(f"快速卖出: {symbol} x{pos.quantity}")
        self.engine.manual_sell(symbol, pos.quantity)
        self._refresh_dashboard()

    def _sell_all(self):
        """清空所有持仓"""
        positions = self.engine.broker.get_positions()
        if not positions:
            QMessageBox.information(self, "提示", "当前无持仓")
            return

        reply = QMessageBox.question(
            self, "确认清仓",
            f"确认卖出全部 {len(positions)} 个持仓？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self._append_log("开始清仓全部持仓...")
        for pos in positions:
            self.engine.manual_sell(pos.symbol, pos.quantity)
        self._refresh_dashboard()

    def _on_trade_symbol_changed(self, symbol: str):
        """交易股票选择变更"""
        if not symbol:
            return
        symbol = symbol.strip().upper()
        self._selected_symbol = symbol

        # 更新当前价格
        import threading
        def _fetch():
            price = self.engine.market_data.get_price(symbol)
            if price:
                self.trade_price_label.setText(f"市价: ${price:.2f}")

            df = self.engine.market_data.fetch_history(symbol)
            if not df.empty:
                df = calc_all_indicators(df)
                self.chart_widget.set_data(df.tail(120), symbol)

        threading.Thread(target=_fetch, daemon=True).start()

    def _on_position_clicked(self, index):
        """点击持仓行"""
        row = index.row()
        symbol_item = self.pos_table.item(row, 0)
        if symbol_item:
            symbol = symbol_item.text()
            self.trade_symbol.setCurrentText(symbol)

    # ----------------------------------------------------------
    # 自动交易控制
    # ----------------------------------------------------------

    def _toggle_auto(self):
        """切换自动交易"""
        if self.engine.is_auto_running:
            self.engine.stop_auto()
            self._append_log("自动交易已停止")
        else:
            self.engine.start_auto(interval_seconds=60)
            self._append_log("自动交易已启动")
        self._refresh_dashboard()

    def _reset_account(self):
        """重置模拟账户"""
        reply = QMessageBox.question(
            self, "确认重置",
            "确认重置模拟账户？所有持仓和订单将被清除。",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        if hasattr(self.engine.broker, 'reset'):
            self.engine.broker.reset()
        self.engine.risk_manager.reset_daily()
        self._append_log("模拟账户已重置")
        self._refresh_dashboard()

    # ----------------------------------------------------------
    # 策略控制
    # ----------------------------------------------------------

    def _on_strategy_changed(self, index: int):
        """策略切换"""
        strategies = ["multi", "macd", "rsi", "ma_trend", "bollinger"]
        if index < len(strategies):
            from trading.strategy import create_strategy
            self.engine.strategy = create_strategy(strategies[index])

        descs = [
            "综合MACD、RSI、均线趋势、布林带四个子策略，通过加权投票机制生成交易信号。\n"
            "权重: MACD 30%, RSI 25%, 均线 25%, 布林带 20%",
            "基于MACD金叉买入、死叉卖出。适合趋势行情。",
            "基于RSI超卖(<30)买入、超买(>70)卖出。适合震荡行情。",
            "基于MA5与MA20交叉判断趋势。MA5上穿MA20买入，下穿卖出。",
            "基于布林带突破。突破上轨买入，跌破中轨卖出。",
        ]
        self.strategy_desc.setText(descs[index] if index < len(descs) else "")
        self._append_log(f"策略已切换: {self.strategy_combo.currentText()}")

    def _toggle_strategy(self, enabled: bool):
        """切换策略启停"""
        if enabled:
            self.engine.strategy.enable()
            self.strategy_status.setText("运行中")
            self.strategy_status.setStyleSheet(f"color: {GREEN}; font-weight: bold;")
        else:
            self.engine.strategy.disable()
            self.strategy_status.setText("已暂停")
            self.strategy_status.setStyleSheet(f"color: {RED}; font-weight: bold;")

    # ----------------------------------------------------------
    # 信号 / 日志
    # ----------------------------------------------------------

    def _add_signal_row(self, row_data: list):
        """添加信号行到表格"""
        self.signal_table.insertRow(0)
        for c, val in enumerate(row_data):
            item = self._table_item(val)
            if c == 2:  # 信号列着色
                if val == "BUY":
                    item.setForeground(QColor(GREEN))
                elif val == "SELL":
                    item.setForeground(QColor(RED))
            self.signal_table.setItem(0, c, item)
        # 保持最多20行
        while self.signal_table.rowCount() > 20:
            self.signal_table.removeRow(20)

    def _append_log(self, msg: str):
        """追加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_output.appendPlainText(f"[{timestamp}] {msg}")

    def _flush_logs(self):
        """刷新日志缓冲区"""
        while self._log_buffer:
            msg = self._log_buffer.pop(0)
            self.log_output.appendPlainText(msg)

    # ----------------------------------------------------------
    # 生命周期
    # ----------------------------------------------------------

    def closeEvent(self, event):
        """关闭窗口"""
        self._dashboard_timer.stop()
        self.engine.stop()
        event.accept()
