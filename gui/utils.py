# -*- coding: utf-8 -*-
"""
美股自动交易系统 - GUI 共享工具函数模块

提供数值格式化、颜色辅助、表格操作等通用功能，
供所有标签页和组件复用。
"""

from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView

from gui.styles import COLOR_GREEN, COLOR_RED, COLOR_GRAY, COLOR_TEXT_DIM


# ============================================================
# 数值格式化函数
# ============================================================

def format_price(value, decimals=2):
    """
    格式化价格显示。

    参数:
        value: 价格数值
        decimals: 小数位数，默认2位

    返回:
        格式化后的字符串，如 "152.30" 或 "--"
    """
    if value is None:
        return "--"
    try:
        v = float(value)
        if v != v:  # NaN 检查
            return "--"
        return f"{v:,.{decimals}f}"
    except (ValueError, TypeError):
        return "--"


def format_pct(value, decimals=2):
    """
    格式化百分比显示。

    参数:
        value: 百分比数值（如 3.14 表示 3.14%）
        decimals: 小数位数，默认2位

    返回:
        格式化后的字符串，如 "+3.14%" 或 "-1.20%"
    """
    if value is None:
        return "--"
    try:
        v = float(value)
        if v != v:  # NaN 检查
            return "--"
        sign = "+" if v >= 0 else ""
        return f"{sign}{v:.{decimals}f}%"
    except (ValueError, TypeError):
        return "--"


def format_signed(value, decimals=2):
    """
    格式化带符号数值（用于涨跌额）。

    参数:
        value: 数值
        decimals: 小数位数

    返回:
        如 "+1.50" 或 "-0.75"
    """
    if value is None:
        return "--"
    try:
        v = float(value)
        if v != v:
            return "--"
        sign = "+" if v >= 0 else ""
        return f"{sign}{v:,.{decimals}f}"
    except (ValueError, TypeError):
        return "--"


def format_number(value):
    """
    格式化大数字，使用万/亿单位。

    参数:
        value: 数值

    返回:
        如 "1.00万", "3.50亿", "999" 或 "--"
    """
    if value is None:
        return "--"
    try:
        v = float(value)
        if v != v:
            return "--"
        abs_v = abs(v)
        if abs_v >= 1e8:
            return f"{v / 1e8:.2f}亿"
        elif abs_v >= 1e4:
            return f"{v / 1e4:.2f}万"
        else:
            return f"{v:,.0f}"
    except (ValueError, TypeError):
        return "--"


def format_volume(value):
    """
    格式化成交量，使用 K/M/B 单位。

    参数:
        value: 成交量数值

    返回:
        如 "1.50M", "3.20B", "999K" 或 "--"
    """
    if value is None:
        return "--"
    try:
        v = float(value)
        if v != v:
            return "--"
        abs_v = abs(v)
        if abs_v >= 1e9:
            return f"{v / 1e9:.2f}B"
        elif abs_v >= 1e6:
            return f"{v / 1e6:.2f}M"
        elif abs_v >= 1e3:
            return f"{v / 1e3:.2f}K"
        else:
            return f"{v:,.0f}"
    except (ValueError, TypeError):
        return "--"


def format_int(value):
    """
    格式化整数显示。

    参数:
        value: 数值

    返回:
        如 "1,500" 或 "--"
    """
    if value is None:
        return "--"
    try:
        v = int(value)
        return f"{v:,}"
    except (ValueError, TypeError):
        return "--"


def format_datetime(dt_str):
    """
    格式化时间字符串，只保留日期和时间部分。

    参数:
        dt_str: ISO 格式时间字符串，如 "2024-01-15T10:30:00Z"

    返回:
        如 "01-15 10:30" 或原始字符串
    """
    if not dt_str:
        return "--"
    s = str(dt_str)
    # 尝试提取日期和时间
    try:
        # 处理 ISO 格式
        if "T" in s:
            date_part, time_part = s.split("T")
            date_part = date_part[5:] if len(date_part) >= 10 else date_part  # MM-DD
            time_part = time_part[:5]  # HH:MM
            return f"{date_part} {time_part}"
        elif " " in s:
            date_part, time_part = s.split(" ")
            date_part = date_part[5:] if len(date_part) >= 10 else date_part
            time_part = time_part[:5]
            return f"{date_part} {time_part}"
        else:
            return s[:16] if len(s) >= 16 else s
    except Exception:
        return s


# ============================================================
# 颜色辅助函数
# ============================================================

def color_for_pnl(value):
    """
    根据盈亏值返回对应颜色的 QBrush。

    正数返回绿色，负数返回红色，零返回灰色。

    参数:
        value: 盈亏数值

    返回:
        QBrush 对象
    """
    if value is None:
        return QBrush(QColor(COLOR_GRAY))
    try:
        v = float(value)
        if v != v:  # NaN
            return QBrush(QColor(COLOR_GRAY))
        if v > 0:
            return QBrush(QColor(COLOR_GREEN))
        elif v < 0:
            return QBrush(QColor(COLOR_RED))
        else:
            return QBrush(QColor(COLOR_TEXT_DIM))
    except (ValueError, TypeError):
        return QBrush(QColor(COLOR_GRAY))


def color_for_change(value):
    """
    根据涨跌幅返回对应颜色的 QBrush（与 color_for_pnl 相同逻辑）。

    参数:
        value: 涨跌幅数值

    返回:
        QBrush 对象
    """
    return color_for_pnl(value)


def color_for_risk_level(level):
    """
    根据风险等级返回对应颜色。

    参数:
        level: 风险等级字符串，如 'low', 'medium', 'high', 'extreme'

    返回:
        QColor 对象
    """
    level_lower = str(level).lower() if level else "unknown"
    color_map = {
        "low": QColor(COLOR_GREEN),
        "medium": QColor(COLOR_GRAY),
        "moderate": QColor(COLOR_GRAY),
        "high": QColor("#ff9800"),
        "extreme": QColor(COLOR_RED),
        "critical": QColor(COLOR_RED),
    }
    return color_map.get(level_lower, QColor(COLOR_TEXT_DIM))


def color_for_side(side):
    """
    根据买卖方向返回对应颜色。

    参数:
        side: 方向字符串 'buy' / 'sell'

    返回:
        QColor 对象
    """
    side_lower = str(side).lower() if side else ""
    if side_lower in ("buy", "long"):
        return QColor(COLOR_GREEN)
    elif side_lower in ("sell", "short"):
        return QColor(COLOR_RED)
    else:
        return QColor(COLOR_TEXT_DIM)


# ============================================================
# 表格辅助函数
# ============================================================

def setup_table(table, headers, stretch_last=True):
    """
    初始化 QTableWidget 的基本属性。

    设置表头、交替行颜色、排序、选择行为等通用属性。

    参数:
        table: QTableWidget 实例
        headers: 表头标题列表
        stretch_last: 最后一列是否自动拉伸
    """
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setAlternatingRowColors(True)
    table.setSortingEnabled(True)
    table.setSelectionBehavior(QTableWidget.SelectRows)
    table.setSelectionMode(QTableWidget.SingleSelection)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(28)
    table.horizontalHeader().setStretchLastSection(stretch_last)
    table.setShowGrid(False)
    # 设置表头可点击排序
    table.horizontalHeader().setSectionsClickable(True)
    # 设置表头默认排序
    table.horizontalHeader().setSortIndicatorShown(True)


def set_cell(table, row, col, text, brush=None, alignment=None, sort_key=None):
    """
    设置表格单元格内容。

    参数:
        table: QTableWidget 实例
        row: 行号
        col: 列号
        text: 显示文本
        brush: 可选的 QBrush，用于设置文字颜色
        alignment: 可选的对齐方式
        sort_key: 可选的排序键数值，用于正确的数值排序
    """
    if sort_key is not None:
        item = NumericTableWidgetItem(text, sort_key)
    else:
        item = QTableWidgetItem(text)

    if alignment is not None:
        item.setTextAlignment(alignment)
    else:
        item.setTextAlignment(Qt.AlignCenter)

    if brush is not None:
        item.setForeground(brush)

    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
    table.setItem(row, col, item)


class NumericTableWidgetItem(QTableWidgetItem):
    """
    支持数值排序的 QTableWidgetItem。

    QTableWidget 默认按字符串排序，此子类允许按数值大小排序。
    """

    def __init__(self, text, sort_value):
        """
        初始化数值排序表格项。

        参数:
            text: 显示的文本
            sort_value: 用于排序的数值
        """
        super().__init__(text)
        self._sort_value = sort_value

    def __lt__(self, other):
        """重载小于比较运算符，按数值排序"""
        if isinstance(other, NumericTableWidgetItem):
            try:
                return float(self._sort_value) < float(other._sort_value)
            except (ValueError, TypeError):
                return super().__lt__(other)
        return super().__lt__(other)


def clear_table(table):
    """
    清空表格内容但保留表头。

    参数:
        table: QTableWidget 实例
    """
    table.setSortingEnabled(False)
    table.setRowCount(0)


def resize_table_columns(table, mode="interactive"):
    """
    调整表格列宽模式。

    参数:
        table: QTableWidget 实例
        mode: 'interactive'（手动调整）、'stretch'（均匀拉伸）、
              'content'（根据内容自适应）
    """
    header = table.horizontalHeader()
    if mode == "stretch":
        header.setSectionResizeMode(QHeaderView.Stretch)
    elif mode == "content":
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
    else:
        header.setSectionResizeMode(QHeaderView.Interactive)


def flatten_stock_universe(stock_universe):
    """
    将分组的股票池字典展平为列表。

    参数:
        stock_universe: 如 config.STOCK_UNIVERSE 的字典 {板块: [代码...]}

    返回:
        (代码列表, 代码到板块的映射字典)
    """
    symbols = []
    sector_map = {}
    for sector, tickers in stock_universe.items():
        for t in tickers:
            symbols.append(t)
            sector_map[t] = sector
    return symbols, sector_map
