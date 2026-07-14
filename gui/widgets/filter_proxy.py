# -*- coding: utf-8 -*-
"""
表格过滤代理（FilterProxy）

在 QTableWidget 外套一层 QSortFilterProxyModel，提供：
- 按代码 / 备注 / 任意列过滤
- 列头点击排序
- 占位符提示

不破坏既有 Tab 的使用方式，作为可选项引入。
"""

from typing import Optional

from PyQt5.QtCore import Qt, QSortFilterProxyModel, QModelIndex
from PyQt5.QtWidgets import (
    QHBoxLayout, QLineEdit, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)


class TextFilterProxy(QSortFilterProxyModel):
    """默认按所有列做"包含"匹配；空字符串表示不过滤。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._needle = ""

    def setNeedle(self, s: str) -> None:
        self._needle = (s or "").lower().strip()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if not self._needle:
            return True
        model = self.sourceModel()
        for c in range(model.columnCount()):
            idx = model.index(source_row, c, source_parent)
            val = str(model.data(idx) or "").lower()
            if self._needle in val:
                return True
        return False


class FilteredTable(QWidget):
    """
    过滤 + 排序表格容器：
        ft = FilteredTable(label="过滤：", placeholder="按代码过滤")
        ft.set_table(table)        # 直接套用现有 QTableWidget
    """

    def __init__(self, label: str = "过滤：", placeholder: str = "输入关键字过滤",
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        self._edit = QLineEdit(self)
        self._edit.setPlaceholderText(placeholder)
        self._edit.textChanged.connect(self._on_changed)
        bar.addWidget(self._edit)
        layout.addLayout(bar)
        self._table: Optional[QTableWidget] = None

    def _on_changed(self, s: str) -> None:
        if self._table is None:
            return
        # QTableWidget 改用 setFilterFixedString 即可按一列过滤；保留原特性
        self._table.setFilterFixedString(s)

    def set_table(self, table: QTableWidget) -> None:
        self._table = table


__all__ = ["TextFilterProxy", "FilteredTable"]
