# -*- coding: utf-8 -*-
"""
美股自动交易系统 - 策略标签页模块

提供策略选择、参数配置、启停控制和运行状态监控，
同时展示策略产生的信号日志和交易日志。

布局结构:
    +------------------------+---------------------------+
    |  策略选择面板           |                           |
    |  (下拉/描述/参数/标的)  |    信号日志表格           |
    +------------------------+                           |
    |  策略运行状态           +---------------------------+
    |  (指示灯/名称/标的/    |    交易日志表格           |
    |   信号数/交易数)        |                           |
    +------------------------+---------------------------+
"""

from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton,
    QTableWidget, QSplitter, QFrame, QSizePolicy, QGroupBox,
    QMessageBox, QCheckBox, QScrollArea, QHeaderView,
    QListWidget, QListWidgetItem,
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


class StrategyTab(QWidget):
    """
    策略标签页。

    管理自动化交易策略的配置、启停和监控。
    """

    def __init__(self, engine, parent=None):
        """
        初始化策略标签页。

        参数:
            engine: TradingEngine 实例
            parent: 父控件
        """
        super().__init__(parent)
        self._engine = engine
        self._strategies = []           # 可用策略列表
        self._current_strategy = None   # 当前选中的策略
        self._param_widgets = {}        # 策略参数控件 {param_name: widget}

        # 获取默认股票池
        try:
            from config import STOCK_UNIVERSE
            self._all_symbols, self._sector_map = flatten_stock_universe(STOCK_UNIVERSE)
        except ImportError:
            self._all_symbols = []
            self._sector_map = {}

        self._init_ui()

    def _init_ui(self):
        """构建 UI 布局"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        main_splitter = QSplitter(Qt.Horizontal)

        # ---- 左侧：策略选择 + 运行状态 ----
        left_widget = self._create_left_panel()
        main_splitter.addWidget(left_widget)

        # ---- 右侧：信号日志 + 交易日志 ----
        right_widget = self._create_right_panel()
        main_splitter.addWidget(right_widget)

        main_splitter.setStretchFactor(0, 2)
        main_splitter.setStretchFactor(1, 3)
        main_splitter.setSizes([500, 700])

        main_layout.addWidget(main_splitter)

    def _create_left_panel(self):
        """创建左侧面板（策略选择 + 运行状态）"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 策略选择面板
        config_panel = self._create_strategy_config_panel()
        layout.addWidget(config_panel, 3)

        # 运行状态面板
        status_panel = self._create_status_panel()
        layout.addWidget(status_panel, 2)

        return widget

    def _create_strategy_config_panel(self):
        """创建策略配置面板"""
        group = QGroupBox("策略配置")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        # 策略选择
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("策略:"))
        self._strategy_combo = QComboBox()
        self._strategy_combo.currentIndexChanged.connect(self._on_strategy_selected)
        row1.addWidget(self._strategy_combo, 1)
        layout.addLayout(row1)

        # 策略描述
        self._strategy_desc = QLabel("请选择策略")
        self._strategy_desc.setWordWrap(True)
        self._strategy_desc.setStyleSheet(
            f"color: {COLOR_TEXT_DIM}; font-size: 12px; padding: 4px; "
            f"background-color: {COLOR_BG}; border: 1px solid {COLOR_BORDER}; border-radius: 3px;"
        )
        self._strategy_desc.setMinimumHeight(40)
        layout.addWidget(self._strategy_desc)

        # 策略参数区域（滚动）
        params_label = QLabel("参数设置:")
        params_label.setStyleSheet(f"color: {COLOR_TEXT}; font-weight: bold;")
        layout.addWidget(params_label)

        self._params_container = QWidget()
        self._params_layout = QGridLayout(self._params_container)
        self._params_layout.setSpacing(6)
        self._params_layout.setContentsMargins(0, 0, 0, 0)

        params_scroll = QScrollArea()
        params_scroll.setWidgetResizable(True)
        params_scroll.setWidget(self._params_container)
        params_scroll.setFrameShape(QFrame.NoFrame)
        params_scroll.setStyleSheet(f"background: transparent; border: none;")
        params_scroll.setMinimumHeight(80)
        params_scroll.setMaximumHeight(200)
        layout.addWidget(params_scroll)

        # 交易标的
        symbols_label = QLabel("交易标的:")
        symbols_label.setStyleSheet(f"color: {COLOR_TEXT}; font-weight: bold;")
        layout.addWidget(symbols_label)

        self._symbols_list = QListWidget()
        self._symbols_list.setSelectionMode(QListWidget.MultiSelection)
        self._symbols_list.setMaximumHeight(120)
        for symbol in self._all_symbols:
            item = QListWidgetItem(symbol)
            item.setData(Qt.UserRole, symbol)
            self._symbols_list.addItem(item)
        layout.addWidget(self._symbols_list)

        # 检查间隔
        row_interval = QHBoxLayout()
        row_interval.addWidget(QLabel("检查间隔(秒):"))
        self._interval_spin = QSpinBox()
        self._interval_spin.setRange(5, 3600)
        self._interval_spin.setValue(60)
        row_interval.addWidget(self._interval_spin)
        row_interval.addStretch()
        layout.addLayout(row_interval)

        # 启动/停止按钮
        btn_row = QHBoxLayout()
        self._start_btn = QPushButton("启动策略")
        self._start_btn.setObjectName("startButton")
        self._start_btn.setMinimumHeight(36)
        self._start_btn.clicked.connect(self._on_start_strategy)

        self._stop_btn = QPushButton("停止策略")
        self._stop_btn.setObjectName("stopButton")
        self._stop_btn.setMinimumHeight(36)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._on_stop_strategy)

        btn_row.addWidget(self._start_btn)
        btn_row.addWidget(self._stop_btn)
        layout.addLayout(btn_row)

        return group

    def _create_status_panel(self):
        """创建策略运行状态面板"""
        group = QGroupBox("运行状态")
        layout = QGridLayout(group)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 16, 12, 12)

        # 运行状态指示灯
        lbl_status = QLabel("运行状态:")
        layout.addWidget(lbl_status, 0, 0)
        self._status_light = QLabel("  停止  ")
        self._status_light.setStyleSheet(
            f"background-color: {COLOR_GRAY}; color: white; "
            f"font-weight: bold; padding: 4px 12px; border-radius: 10px; font-size: 13px;"
        )
        self._status_light.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._status_light, 0, 1)

        # 当前策略名称
        layout.addWidget(QLabel("当前策略:"), 1, 0)
        self._status_name = QLabel("--")
        self._status_name.setStyleSheet(f"color: {COLOR_BLUE}; font-weight: bold;")
        layout.addWidget(self._status_name, 1, 1)

        # 监控标的
        layout.addWidget(QLabel("监控标的:"), 2, 0)
        self._status_symbols = QLabel("--")
        self._status_symbols.setWordWrap(True)
        self._status_symbols.setStyleSheet(f"color: {COLOR_TEXT};")
        layout.addWidget(self._status_symbols, 2, 1)

        # 最后检查时间
        layout.addWidget(QLabel("最后检查:"), 3, 0)
        self._status_last_check = QLabel("--")
        self._status_last_check.setStyleSheet(f"color: {COLOR_TEXT_DIM};")
        layout.addWidget(self._status_last_check, 3, 1)

        # 今日信号数
        layout.addWidget(QLabel("今日信号:"), 4, 0)
        self._status_signals = QLabel("0")
        self._status_signals.setStyleSheet(f"color: {COLOR_YELLOW}; font-weight: bold; font-size: 16px;")
        layout.addWidget(self._status_signals, 4, 1)

        # 今日交易数
        layout.addWidget(QLabel("今日交易:"), 5, 0)
        self._status_trades = QLabel("0")
        self._status_trades.setStyleSheet(f"color: {COLOR_GREEN}; font-weight: bold; font-size: 16px;")
        layout.addWidget(self._status_trades, 5, 1)

        return group

    def _create_right_panel(self):
        """创建右侧面板（信号日志 + 交易日志）"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 信号日志
        signal_group = QGroupBox("信号日志")
        signal_layout = QVBoxLayout(signal_group)
        signal_headers = ["时间", "代码", "方向", "原因", "强度"]
        self._signal_table = QTableWidget()
        setup_table(self._signal_table, signal_headers)
        signal_layout.addWidget(self._signal_table)
        layout.addWidget(signal_group, 1)

        # 交易日志
        trade_group = QGroupBox("交易日志")
        trade_layout = QVBoxLayout(trade_group)
        trade_headers = ["时间", "代码", "方向", "数量", "价格", "状态"]
        self._trade_table = QTableWidget()
        setup_table(self._trade_table, trade_headers)
        trade_layout.addWidget(self._trade_table)
        layout.addWidget(trade_group, 1)

        return widget

    # ============================================================
    # 策略管理
    # ============================================================

    def load_strategies(self):
        """从引擎加载可用策略列表"""
        try:
            strategies = self._engine.get_available_strategies()
            if not strategies:
                strategies = []

            self._strategies = strategies
            self._strategy_combo.clear()

            for s in strategies:
                name = s.get('name', 'unknown')
                display = s.get('display_name', name)
                self._strategy_combo.addItem(display, name)

            if strategies:
                self._on_strategy_selected(0)
        except Exception as e:
            pass

    def _on_strategy_selected(self, index):
        """
        策略选择变更回调。

        参数:
            index: 下拉框索引
        """
        if index < 0 or index >= len(self._strategies):
            return

        strategy = self._strategies[index]
        self._current_strategy = strategy

        # 显示描述
        desc = strategy.get('description', '无描述')
        self._strategy_desc.setText(desc)

        # 生成参数控件
        self._generate_param_controls(strategy.get('params', {}))

    def _generate_param_controls(self, params):
        """
        根据策略的参数定义动态生成输入控件。

        参数:
            params: 参数定义字典 {param_name: {default, type, min, max, description}}
        """
        # 清除旧控件
        self._param_widgets.clear()
        # 清除布局中的所有项
        while self._params_layout.count():
            item = self._params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not params:
            placeholder = QLabel("该策略没有可配置参数")
            placeholder.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-style: italic;")
            self._params_layout.addWidget(placeholder, 0, 0)
            return

        row = 0
        for param_name, param_def in params.items():
            # 参数标签
            desc = param_def.get('description', param_name)
            label = QLabel(f"{desc}:")
            label.setStyleSheet(f"color: {COLOR_TEXT};")
            self._params_layout.addWidget(label, row, 0)

            # 参数输入控件
            param_type = param_def.get('type', 'float')
            default_val = param_def.get('default', 0)
            min_val = param_def.get('min', None)
            max_val = param_def.get('max', None)

            if param_type == 'int':
                widget = QSpinBox()
                widget.setRange(int(min_val) if min_val is not None else -999999,
                                int(max_val) if max_val is not None else 999999)
                widget.setValue(int(default_val) if default_val is not None else 0)
            elif param_type == 'bool':
                widget = QCheckBox()
                widget.setChecked(bool(default_val) if default_val is not None else False)
            elif param_type == 'str':
                widget = QLineEdit(str(default_val) if default_val is not None else "")
            else:  # float 或未知类型默认为浮点
                widget = QDoubleSpinBox()
                widget.setRange(float(min_val) if min_val is not None else -999999.99,
                                float(max_val) if max_val is not None else 999999.99)
                widget.setDecimals(4)
                widget.setValue(float(default_val) if default_val is not None else 0.0)
                widget.setSingleStep(0.1)

            self._params_layout.addWidget(widget, row, 1)
            self._param_widgets[param_name] = widget
            row += 1

        # 添加弹性空间
        self._params_layout.setRowStretch(row, 1)

    def _get_selected_symbols(self):
        """
        获取选中的交易标的列表。

        返回:
            选中的股票代码列表
        """
        selected = []
        for item in self._symbols_list.selectedItems():
            symbol = item.data(Qt.UserRole)
            if symbol:
                selected.append(symbol)

        if not selected and self._all_symbols:
            # 如果没选，默认选全部
            selected = self._all_symbols[:4]  # 默认选前4个

        return selected

    def _get_param_values(self):
        """
        收集所有参数控件的当前值。

        返回:
            参数字典 {param_name: value}
        """
        values = {}
        for name, widget in self._param_widgets.items():
            if isinstance(widget, QSpinBox):
                values[name] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                values[name] = widget.value()
            elif isinstance(widget, QCheckBox):
                values[name] = widget.isChecked()
            elif isinstance(widget, QLineEdit):
                values[name] = widget.text()
            else:
                values[name] = None
        return values

    def _on_start_strategy(self):
        """启动策略"""
        if not self._current_strategy:
            QMessageBox.warning(self, "提示", "请先选择一个策略")
            return

        strategy_name = self._current_strategy.get('name', '')
        display_name = self._current_strategy.get('display_name', strategy_name)
        symbols = self._get_selected_symbols()
        params = self._get_param_values()
        interval = self._interval_spin.value()

        if not symbols:
            QMessageBox.warning(self, "提示", "请至少选择一个交易标的")
            return

        # 确认对话框
        params_str = "\n".join(f"  {k}: {v}" for k, v in params.items())
        msg = (
            f"确认启动以下策略？\n\n"
            f"策略: {display_name}\n"
            f"标的: {', '.join(symbols)}\n"
            f"检查间隔: {interval}秒\n"
            f"参数:\n{params_str if params_str else '  (默认)'}"
        )
        reply = QMessageBox.question(
            self, "确认启动策略", msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # 启动策略
        try:
            success = self._engine.start_strategy(strategy_name, symbols, **params)
            if success:
                self._start_btn.setEnabled(False)
                self._stop_btn.setEnabled(True)
                self._status_light.setText("  运行中  ")
                self._status_light.setStyleSheet(
                    f"background-color: {COLOR_GREEN}; color: white; "
                    f"font-weight: bold; padding: 4px 12px; border-radius: 10px; font-size: 13px;"
                )
                QMessageBox.information(self, "成功", f"策略 '{display_name}' 已启动")
                self.refresh()
            else:
                QMessageBox.warning(self, "失败", "策略启动失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动策略失败:\n{str(e)}")

    def _on_stop_strategy(self):
        """停止策略"""
        reply = QMessageBox.question(
            self, "确认停止策略",
            "确认停止当前运行的策略？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            success = self._engine.stop_strategy()
            if success:
                self._start_btn.setEnabled(True)
                self._stop_btn.setEnabled(False)
                self._status_light.setText("  停止  ")
                self._status_light.setStyleSheet(
                    f"background-color: {COLOR_GRAY}; color: white; "
                    f"font-weight: bold; padding: 4px 12px; border-radius: 10px; font-size: 13px;"
                )
                QMessageBox.information(self, "成功", "策略已停止")
                self.refresh()
            else:
                QMessageBox.warning(self, "失败", "策略停止失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"停止策略失败:\n{str(e)}")

    # ============================================================
    # 数据刷新
    # ============================================================

    def refresh(self):
        """
        刷新策略标签页数据。

        由主窗口 QTimer 定时调用。刷新策略运行状态、信号日志和交易日志。
        """
        self._refresh_status()
        self._refresh_signal_log()
        self._refresh_trade_log()

    def _refresh_status(self):
        """刷新策略运行状态"""
        try:
            status = self._engine.get_strategy_status()
            if not status:
                return

            running = status.get('running', False)
            name = status.get('name', '--')
            symbols = status.get('symbols', [])
            last_check = status.get('last_check', '')
            signals_today = status.get('signals_today', 0)
            trades_today = status.get('trades_today', 0)

            # 运行状态
            if running:
                self._status_light.setText("  运行中  ")
                self._status_light.setStyleSheet(
                    f"background-color: {COLOR_GREEN}; color: white; "
                    f"font-weight: bold; padding: 4px 12px; border-radius: 10px; font-size: 13px;"
                )
                self._start_btn.setEnabled(False)
                self._stop_btn.setEnabled(True)
            else:
                self._status_light.setText("  停止  ")
                self._status_light.setStyleSheet(
                    f"background-color: {COLOR_GRAY}; color: white; "
                    f"font-weight: bold; padding: 4px 12px; border-radius: 10px; font-size: 13px;"
                )
                self._start_btn.setEnabled(True)
                self._stop_btn.setEnabled(False)

            # 策略名称
            self._status_name.setText(name)

            # 监控标的
            if symbols:
                self._status_symbols.setText(", ".join(symbols))
            else:
                self._status_symbols.setText("--")

            # 最后检查时间
            self._status_last_check.setText(format_datetime(last_check))

            # 信号数和交易数
            self._status_signals.setText(str(signals_today))
            self._status_trades.setText(str(trades_today))

        except Exception:
            pass

    def _refresh_signal_log(self):
        """刷新信号日志表格"""
        try:
            # 尝试从引擎获取信号日志
            status = self._engine.get_strategy_status()
            signals = []

            if status and isinstance(status.get('signals'), list):
                signals = status['signals']

            clear_table(self._signal_table)
            self._signal_table.setRowCount(len(signals))

            for row, signal in enumerate(signals):
                time = signal.get('time', signal.get('created_at', ''))
                symbol = signal.get('symbol', '--')
                direction = signal.get('direction', signal.get('side', '--'))
                reason = signal.get('reason', signal.get('type', '--'))
                strength = signal.get('strength', '--')

                set_cell(self._signal_table, row, 0, format_datetime(time))

                dir_color = color_for_side(direction)
                set_cell(self._signal_table, row, 1, symbol)
                set_cell(self._signal_table, row, 2, str(direction).upper() if direction else '--',
                         brush=QBrush(dir_color))
                set_cell(self._signal_table, row, 3, str(reason))

                # 强度颜色
                strength_str = str(strength).lower()
                if strength_str in ('high', 'strong', '高'):
                    strength_brush = QBrush(QColor(COLOR_RED))
                elif strength_str in ('medium', '中'):
                    strength_brush = QBrush(QColor(COLOR_YELLOW))
                elif strength_str in ('low', 'weak', '低'):
                    strength_brush = QBrush(QColor(COLOR_TEXT_DIM))
                else:
                    strength_brush = QBrush(QColor(COLOR_TEXT))
                set_cell(self._signal_table, row, 4, str(strength),
                         brush=strength_brush)

            self._signal_table.setSortingEnabled(True)
        except Exception:
            pass

    def _refresh_trade_log(self):
        """刷新交易日志表格"""
        try:
            status = self._engine.get_strategy_status()
            trades = []

            if status and isinstance(status.get('trades'), list):
                trades = status['trades']

            clear_table(self._trade_table)
            self._trade_table.setRowCount(len(trades))

            for row, trade in enumerate(trades):
                time = trade.get('time', trade.get('created_at', ''))
                symbol = trade.get('symbol', '--')
                side = trade.get('side', trade.get('direction', '--'))
                qty = trade.get('qty', 0)
                price = trade.get('price', trade.get('filled_price', 0))
                status_val = trade.get('status', '--')

                set_cell(self._trade_table, row, 0, format_datetime(time))
                set_cell(self._trade_table, row, 1, symbol)

                side_color = color_for_side(side)
                set_cell(self._trade_table, row, 2, str(side).upper() if side else '--',
                         brush=QBrush(side_color))
                set_cell(self._trade_table, row, 3, format_number(qty),
                         sort_key=qty, alignment=Qt.AlignRight | Qt.AlignVCenter)
                set_cell(self._trade_table, row, 4, format_price(price) if price else "--",
                         sort_key=price if price else 0,
                         alignment=Qt.AlignRight | Qt.AlignVCenter)

                # 状态颜色
                status_lower = str(status_val).lower()
                if status_lower in ('filled', 'complete', 'done', 'success'):
                    status_brush = QBrush(QColor(COLOR_GREEN))
                elif status_lower in ('failed', 'rejected', 'cancelled', 'canceled'):
                    status_brush = QBrush(QColor(COLOR_RED))
                elif status_lower in ('pending', 'new', 'open'):
                    status_brush = QBrush(QColor(COLOR_YELLOW))
                else:
                    status_brush = QBrush(QColor(COLOR_TEXT_DIM))
                set_cell(self._trade_table, row, 5, str(status_val),
                         brush=status_brush)

            self._trade_table.setSortingEnabled(True)
        except Exception:
            pass
