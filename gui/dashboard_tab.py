# -*- coding: utf-8 -*-
"""
美股自动交易系统 - 仪表盘标签页模块

展示账户概览、持仓详情、自选股实时报价、风险指标和最近订单。
所有数据通过 refresh() 方法由主窗口 QTimer 定时刷新。

布局结构:
    +--------------------------------------------------+
    |          账户概览卡片（总权益/现金/购买力/盈亏）      |
    +------------------------+-------------------------+
    |                        |    自选股实时报价         |
    |     持仓表格            +-------------------------+
    |                        |    风险指标面板           |
    +------------------------+-------------------------+
    |              最近订单表格                          |
    +--------------------------------------------------+
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QTableWidget, QProgressBar, QSplitter, QFrame, QSizePolicy,
    QHeaderView,
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
    color_for_pnl, color_for_change, color_for_risk_level,
    color_for_side, setup_table, set_cell, clear_table,
    flatten_stock_universe, NumericTableWidgetItem,
)


class InfoCard(QFrame):
    """
    信息卡片控件。

    显示一个标题和一个大字号数值，用于账户概览。
    盈亏类卡片可动态切换红绿色。
    """

    def __init__(self, title, value="--", parent=None, is_pnl=False):
        """
        初始化信息卡片。

        参数:
            title: 卡片标题（如 "总权益"）
            value: 初始数值文本
            parent: 父控件
            is_pnl: 是否为盈亏卡片（True 时根据正负切换颜色）
        """
        super().__init__(parent)
        self._is_pnl = is_pnl
        self._setup_ui(title, value)

    def _setup_ui(self, title, value):
        """构建卡片 UI"""
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet(f"""
            InfoCard {{
                background-color: {COLOR_PANEL};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
            }}
        """)
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(4)

        # 标题
        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 12px; background: transparent;")
        layout.addWidget(self._title_label)

        # 数值
        self._value_label = QLabel(value)
        label_style = "cardValueLabelGreen" if self._is_pnl else "cardValueLabel"
        self._value_label.setObjectName(label_style)
        layout.addWidget(self._value_label)

    def set_value(self, value, pnl_value=None):
        """
        设置卡片显示的数值。

        参数:
            value: 显示文本
            pnl_value: 可选的盈亏数值，用于决定颜色（正绿负红）
        """
        self._value_label.setText(value)

        if self._is_pnl and pnl_value is not None:
            try:
                v = float(pnl_value)
                if v > 0:
                    self._value_label.setStyleSheet(
                        f"font-size: 22px; font-weight: bold; color: {COLOR_GREEN}; background: transparent;"
                    )
                elif v < 0:
                    self._value_label.setStyleSheet(
                        f"font-size: 22px; font-weight: bold; color: {COLOR_RED}; background: transparent;"
                    )
                else:
                    self._value_label.setStyleSheet(
                        f"font-size: 22px; font-weight: bold; color: {COLOR_TEXT}; background: transparent;"
                    )
            except (ValueError, TypeError):
                pass


class DashboardTab(QWidget):
    """
    仪表盘标签页。

    汇总展示账户、持仓、行情、风险和订单信息。
    """

    def __init__(self, engine, parent=None):
        """
        初始化仪表盘标签页。

        参数:
            engine: TradingEngine 实例
            parent: 父控件
        """
        super().__init__(parent)
        self._engine = engine

        # 获取自选股列表
        try:
            from config import STOCK_UNIVERSE
            self._watchlist, self._sector_map = flatten_stock_universe(STOCK_UNIVERSE)
        except ImportError:
            self._watchlist = []
            self._sector_map = {}

        self._init_ui()

    def _init_ui(self):
        """构建 UI 布局"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # ---- 顶部：账户概览卡片 ----
        account_layout = QHBoxLayout()
        account_layout.setSpacing(8)

        self._card_equity = InfoCard("总权益", is_pnl=False)
        self._card_cash = InfoCard("可用现金", is_pnl=False)
        self._card_buying_power = InfoCard("购买力", is_pnl=False)
        self._card_day_pnl = InfoCard("当日盈亏", is_pnl=True)
        self._card_day_pnl_pct = InfoCard("当日盈亏%", is_pnl=True)

        account_layout.addWidget(self._card_equity)
        account_layout.addWidget(self._card_cash)
        account_layout.addWidget(self._card_buying_power)
        account_layout.addWidget(self._card_day_pnl)
        account_layout.addWidget(self._card_day_pnl_pct)

        main_layout.addLayout(account_layout, 0)

        # ---- 中间区域：左侧持仓 + 右侧报价/风险 ----
        mid_splitter = QSplitter(Qt.Horizontal)

        # 左侧：持仓表格
        positions_widget = self._create_positions_panel()
        mid_splitter.addWidget(positions_widget)

        # 右侧：上报价 + 下风险
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        watchlist_widget = self._create_watchlist_panel()
        right_layout.addWidget(watchlist_widget, 3)

        risk_widget = self._create_risk_panel()
        right_layout.addWidget(risk_widget, 2)

        mid_splitter.addWidget(right_widget)
        mid_splitter.setStretchFactor(0, 3)
        mid_splitter.setStretchFactor(1, 2)
        mid_splitter.setSizes([600, 400])

        main_layout.addWidget(mid_splitter, 1)

        # ---- 底部：最近订单 ----
        orders_widget = self._create_orders_panel()
        main_layout.addWidget(orders_widget, 0)

    def _create_positions_panel(self):
        """创建持仓表格面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title = QLabel("持仓")
        title.setObjectName("sectionLabel")
        layout.addWidget(title)

        headers = ["股票代码", "数量", "成本价", "现价", "市值", "浮动盈亏", "浮亏%"]
        self._positions_table = QTableWidget()
        setup_table(self._positions_table, headers)
        layout.addWidget(self._positions_table)

        return widget

    def _create_watchlist_panel(self):
        """创建自选股报价面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title = QLabel("自选股行情")
        title.setObjectName("sectionLabel")
        layout.addWidget(title)

        headers = ["代码", "最新价", "涨跌额", "涨跌幅", "成交量", "最高", "最低"]
        self._watchlist_table = QTableWidget()
        setup_table(self._watchlist_table, headers)
        layout.addWidget(self._watchlist_table)

        return widget

    def _create_risk_panel(self):
        """创建风险指标面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title = QLabel("风险指标")
        title.setObjectName("sectionLabel")
        layout.addWidget(title)

        # 风险内容区域
        content = QFrame()
        content.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_PANEL};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
        """)
        content_layout = QGridLayout(content)
        content_layout.setContentsMargins(12, 8, 12, 8)
        content_layout.setSpacing(6)

        # 总敞口
        lbl_exposure = QLabel("总敞口")
        lbl_exposure.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 12px; background: transparent;")
        content_layout.addWidget(lbl_exposure, 0, 0)
        self._risk_exposure_label = QLabel("--")
        self._risk_exposure_label.setStyleSheet(f"color: {COLOR_TEXT}; font-weight: bold; background: transparent;")
        content_layout.addWidget(self._risk_exposure_label, 0, 1)

        # 持仓数
        lbl_count = QLabel("持仓数")
        lbl_count.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 12px; background: transparent;")
        content_layout.addWidget(lbl_count, 1, 0)
        self._risk_count_label = QLabel("--")
        self._risk_count_label.setStyleSheet(f"color: {COLOR_TEXT}; font-weight: bold; background: transparent;")
        content_layout.addWidget(self._risk_count_label, 1, 1)

        # 当日亏损
        lbl_loss = QLabel("当日亏损")
        lbl_loss.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 12px; background: transparent;")
        content_layout.addWidget(lbl_loss, 2, 0)
        self._risk_loss_label = QLabel("--")
        self._risk_loss_label.setStyleSheet(f"color: {COLOR_TEXT}; font-weight: bold; background: transparent;")
        content_layout.addWidget(self._risk_loss_label, 2, 1)

        # 风控等级
        lbl_level = QLabel("风控等级")
        lbl_level.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 12px; background: transparent;")
        content_layout.addWidget(lbl_level, 3, 0)
        self._risk_level_label = QLabel("--")
        self._risk_level_label.setStyleSheet(f"color: {COLOR_TEXT}; font-weight: bold; background: transparent;")
        content_layout.addWidget(self._risk_level_label, 3, 1)

        # 敞口进度条
        lbl_bar = QLabel("敞口占比")
        lbl_bar.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 12px; background: transparent;")
        content_layout.addWidget(lbl_bar, 4, 0)
        self._risk_bar = QProgressBar()
        self._risk_bar.setRange(0, 100)
        self._risk_bar.setValue(0)
        self._risk_bar.setFormat("%v%")
        content_layout.addWidget(self._risk_bar, 4, 1)

        # 日亏损进度条
        lbl_loss_bar = QLabel("日亏损占比")
        lbl_loss_bar.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 12px; background: transparent;")
        content_layout.addWidget(lbl_loss_bar, 5, 0)
        self._risk_loss_bar = QProgressBar()
        self._risk_loss_bar.setRange(0, 100)
        self._risk_loss_bar.setValue(0)
        self._risk_loss_bar.setFormat("%v%")
        content_layout.addWidget(self._risk_loss_bar, 5, 1)

        layout.addWidget(content)

        return widget

    def _create_orders_panel(self):
        """创建最近订单面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title = QLabel("最近订单")
        title.setObjectName("sectionLabel")
        layout.addWidget(title)

        headers = ["订单ID", "代码", "方向", "数量", "类型", "状态", "限价", "成交价", "创建时间"]
        self._orders_table = QTableWidget()
        setup_table(self._orders_table, headers)
        self._orders_table.setMaximumHeight(160)
        layout.addWidget(self._orders_table)

        return widget

    def refresh(self):
        """
        刷新仪表盘所有数据。

        由主窗口 QTimer 定时调用。依次刷新：
        账户概览 -> 持仓 -> 自选股报价 -> 风险指标 -> 最近订单。
        每个部分独立 try/except，单点失败不影响其他部分。
        """
        # 账户概览
        self._refresh_account()

        # 持仓
        self._refresh_positions()

        # 自选股报价
        self._refresh_watchlist()

        # 风险指标
        self._refresh_risk()

        # 最近订单
        self._refresh_orders()

    def _refresh_account(self):
        """刷新账户概览卡片"""
        try:
            account = self._engine.get_account()
            if not account:
                return

            equity = account.get('equity', 0)
            cash = account.get('cash', 0)
            buying_power = account.get('buying_power', 0)
            day_pnl = account.get('day_pnl', 0)
            day_pnl_pct = account.get('day_pnl_pct', 0)

            self._card_equity.set_value(f"${format_price(equity)}")
            self._card_cash.set_value(f"${format_price(cash)}")
            self._card_buying_power.set_value(f"${format_price(buying_power)}")
            self._card_day_pnl.set_value(
                f"${format_signed(day_pnl)}", pnl_value=day_pnl
            )
            self._card_day_pnl_pct.set_value(
                format_pct(day_pnl_pct), pnl_value=day_pnl_pct
            )
        except Exception as e:
            pass

    def _refresh_positions(self):
        """刷新持仓表格"""
        try:
            positions = self._engine.get_positions()
            if not positions:
                positions = []

            clear_table(self._positions_table)
            self._positions_table.setRowCount(len(positions))

            for row, pos in enumerate(positions):
                symbol = pos.get('symbol', '--')
                qty = pos.get('qty', 0)
                avg_price = pos.get('avg_price', 0)
                current_price = pos.get('current_price', 0)
                market_value = pos.get('market_value', 0)
                unrealized_pl = pos.get('unrealized_pl', 0)
                unrealized_pl_pct = pos.get('unrealized_pl_pct', 0)

                set_cell(self._positions_table, row, 0, symbol)
                set_cell(self._positions_table, row, 1, format_number(qty),
                         sort_key=qty, alignment=Qt.AlignRight | Qt.AlignVCenter)
                set_cell(self._positions_table, row, 2, format_price(avg_price),
                         sort_key=avg_price, alignment=Qt.AlignRight | Qt.AlignVCenter)
                set_cell(self._positions_table, row, 3, format_price(current_price),
                         sort_key=current_price, alignment=Qt.AlignRight | Qt.AlignVCenter)
                set_cell(self._positions_table, row, 4, f"${format_price(market_value)}",
                         sort_key=market_value, alignment=Qt.AlignRight | Qt.AlignVCenter)

                pnl_brush = color_for_pnl(unrealized_pl)
                set_cell(self._positions_table, row, 5, f"${format_signed(unrealized_pl)}",
                         brush=pnl_brush, sort_key=unrealized_pl,
                         alignment=Qt.AlignRight | Qt.AlignVCenter)
                set_cell(self._positions_table, row, 6, format_pct(unrealized_pl_pct),
                         brush=pnl_brush, sort_key=unrealized_pl_pct,
                         alignment=Qt.AlignRight | Qt.AlignVCenter)

            self._positions_table.setSortingEnabled(True)
        except Exception as e:
            pass

    def _refresh_watchlist(self):
        """刷新自选股报价表格"""
        if not self._watchlist:
            return

        try:
            clear_table(self._watchlist_table)
            self._watchlist_table.setRowCount(len(self._watchlist))

            for row, symbol in enumerate(self._watchlist):
                try:
                    quote = self._engine.get_quote(symbol)
                    if not quote:
                        for col in range(7):
                            set_cell(self._watchlist_table, row, col, "--")
                        continue

                    last = quote.get('last', 0)
                    change = quote.get('change', 0)
                    change_pct = quote.get('change_pct', 0)
                    volume = quote.get('volume', 0)
                    high = quote.get('high', 0)
                    low = quote.get('low', 0)

                    set_cell(self._watchlist_table, row, 0, symbol)
                    set_cell(self._watchlist_table, row, 1, format_price(last),
                             sort_key=last, alignment=Qt.AlignRight | Qt.AlignVCenter)

                    change_brush = color_for_change(change)
                    set_cell(self._watchlist_table, row, 2, format_signed(change),
                             brush=change_brush, sort_key=change,
                             alignment=Qt.AlignRight | Qt.AlignVCenter)
                    set_cell(self._watchlist_table, row, 3, format_pct(change_pct),
                             brush=change_brush, sort_key=change_pct,
                             alignment=Qt.AlignRight | Qt.AlignVCenter)
                    set_cell(self._watchlist_table, row, 4, format_volume(volume),
                             sort_key=volume, alignment=Qt.AlignRight | Qt.AlignVCenter)
                    set_cell(self._watchlist_table, row, 5, format_price(high),
                             sort_key=high, alignment=Qt.AlignRight | Qt.AlignVCenter)
                    set_cell(self._watchlist_table, row, 6, format_price(low),
                             sort_key=low, alignment=Qt.AlignRight | Qt.AlignVCenter)
                except Exception:
                    for col in range(7):
                        set_cell(self._watchlist_table, row, col, "--")

            self._watchlist_table.setSortingEnabled(True)
        except Exception as e:
            pass

    def _refresh_risk(self):
        """刷新风险指标面板"""
        try:
            risk = self._engine.get_risk_metrics()
            if not risk:
                return

            exposure = risk.get('current_exposure', 0)
            current_loss = risk.get('current_loss', 0)
            risk_level = risk.get('risk_level', '--')
            position_count = risk.get('position_count', 0)
            max_exposure = risk.get('max_total_exposure', 100)
            daily_loss_limit = risk.get('daily_loss_limit', 0)

            # 总敞口
            self._risk_exposure_label.setText(f"{format_pct(exposure)}")

            # 持仓数
            self._risk_count_label.setText(format_int(position_count))

            # 当日亏损
            loss_brush = color_for_pnl(current_loss)
            self._risk_loss_label.setText(f"${format_signed(current_loss)}")
            self._risk_loss_label.setStyleSheet(
                f"color: {loss_brush.color().name()}; font-weight: bold; background: transparent;"
            )

            # 风控等级
            level_color = color_for_risk_level(risk_level)
            level_text = str(risk_level).upper() if risk_level else "--"
            level_map = {
                "low": "低风险", "medium": "中风险", "moderate": "中等",
                "high": "高风险", "extreme": "极高风险", "critical": "危险",
            }
            level_display = level_map.get(level_text.lower(), level_text)
            self._risk_level_label.setText(level_display)
            self._risk_level_label.setStyleSheet(
                f"color: {level_color.name()}; font-weight: bold; font-size: 14px; background: transparent;"
            )

            # 敞口进度条
            try:
                exposure_pct = min(100, abs(float(exposure)))
                self._risk_bar.setValue(int(exposure_pct))
                if exposure_pct > 80:
                    self._risk_bar.setStyleSheet(
                        f"QProgressBar::chunk {{ background-color: {COLOR_RED}; border-radius: 2px; }}"
                    )
                elif exposure_pct > 60:
                    self._risk_bar.setStyleSheet(
                        f"QProgressBar::chunk {{ background-color: {COLOR_ORANGE}; border-radius: 2px; }}"
                    )
                else:
                    self._risk_bar.setStyleSheet(
                        f"QProgressBar::chunk {{ background-color: {COLOR_GREEN}; border-radius: 2px; }}"
                    )
            except (ValueError, TypeError):
                pass

            # 日亏损进度条
            try:
                if daily_loss_limit and daily_loss_limit > 0:
                    loss_pct = min(100, abs(float(current_loss)) / abs(float(daily_loss_limit)) * 100)
                    self._risk_loss_bar.setValue(int(loss_pct))
                    if loss_pct > 80:
                        self._risk_loss_bar.setStyleSheet(
                            f"QProgressBar::chunk {{ background-color: {COLOR_RED}; border-radius: 2px; }}"
                        )
                    elif loss_pct > 50:
                        self._risk_loss_bar.setStyleSheet(
                            f"QProgressBar::chunk {{ background-color: {COLOR_ORANGE}; border-radius: 2px; }}"
                        )
                    else:
                        self._risk_loss_bar.setStyleSheet(
                            f"QProgressBar::chunk {{ background-color: {COLOR_GREEN}; border-radius: 2px; }}"
                        )
                else:
                    self._risk_loss_bar.setValue(0)
            except (ValueError, TypeError):
                pass

        except Exception as e:
            pass

    def _refresh_orders(self):
        """刷新最近订单表格"""
        try:
            orders = self._engine.get_orders(status='all')
            if not orders:
                orders = []

            # 只显示最近 20 条
            orders = orders[:20]

            clear_table(self._orders_table)
            self._orders_table.setRowCount(len(orders))

            for row, order in enumerate(orders):
                order_id = str(order.get('id', '--'))[-8:]  # 只显示后8位
                symbol = order.get('symbol', '--')
                side = order.get('side', '--')
                qty = order.get('qty', 0)
                order_type = order.get('type', '--')
                status = order.get('status', '--')
                limit_price = order.get('limit_price', 0)
                filled_price = order.get('filled_price', 0)
                created_at = order.get('created_at', '')

                set_cell(self._orders_table, row, 0, order_id)
                set_cell(self._orders_table, row, 1, symbol)

                side_color = color_for_side(side)
                set_cell(self._orders_table, row, 2, side.upper() if side else '--',
                         brush=QBrush(side_color))
                set_cell(self._orders_table, row, 3, format_number(qty),
                         sort_key=qty, alignment=Qt.AlignRight | Qt.AlignVCenter)
                set_cell(self._orders_table, row, 4, order_type)

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
                set_cell(self._orders_table, row, 5, str(status),
                         brush=status_brush)

                set_cell(self._orders_table, row, 6, format_price(limit_price) if limit_price else "--",
                         sort_key=limit_price if limit_price else 0,
                         alignment=Qt.AlignRight | Qt.AlignVCenter)
                set_cell(self._orders_table, row, 7, format_price(filled_price) if filled_price else "--",
                         sort_key=filled_price if filled_price else 0,
                         alignment=Qt.AlignRight | Qt.AlignVCenter)
                set_cell(self._orders_table, row, 8, format_datetime(created_at))

            self._orders_table.setSortingEnabled(True)
        except Exception as e:
            pass
