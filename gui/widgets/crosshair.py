# -*- coding: utf-8 -*-
"""
K 线图十字光标 + 数据提示（CrosshairOverlay）

用法:
    from gui.widgets.crosshair import CrosshairOverlay
    overlay = CrosshairOverlay(plot_widget, label_text_fn=lambda x, y: "...")
    overlay.set_data(df['Datetime'].tolist(), df['Close'].tolist())

不影响 chart_widget.py 的现有签名；通过外挂挂到 PyQtGraph plot 上。
"""

from typing import Callable, Optional

import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class CrosshairOverlay:
    """在 plot_widget 上添加十字光标 + 跟随 Label。"""

    def __init__(
        self,
        plot_widget: pg.PlotWidget,
        label_text_fn: Optional[Callable[[int], str]] = None,
        line_color: str = "#58a6ff",
    ):
        self.plot = plot_widget
        self.label_text_fn = label_text_fn or (lambda i: f"#{i}")

        self.v_line = pg.InfiniteLine(angle=90, movable=False,
                                      pen=pg.mkPen(line_color, width=1, style=Qt.DashLine))
        self.h_line = pg.InfiniteLine(angle=0, movable=False,
                                      pen=pg.mkPen(line_color, width=1, style=Qt.DashLine))
        self.plot.addItem(self.v_line, ignoreBounds=True)
        self.plot.addItem(self.h_line, ignoreBounds=True)
        self.v_line.setVisible(False)
        self.h_line.setVisible(False)

        self.text_label = pg.TextItem(anchor=(0, 1), color=QColor("#c9d1d9"))
        self.text_label.setParentItem(self.plot.getPlotItem())
        self.text_label.setVisible(False)

        self.x_data: list = []
        self.y_data: list = []
        self.proxy = pg.SignalProxy(
            self.plot.scene().sigMouseMoved,
            rateLimit=60,
            slot=self._on_mouse_moved,
        )

    # ---------- 数据 ----------

    def set_data(self, x_axis: list, y_axis: list) -> None:
        self.x_data = x_axis
        self.y_data = y_axis

    # ---------- 事件 ----------

    def _on_mouse_moved(self, evt) -> None:
        pos = evt[0]
        if not self.plot.sceneBoundingRect().contains(pos):
            return
        vb = self.plot.getPlotItem().getViewBox()
        mouse_point = vb.mapSceneToView(pos)
        x = mouse_point.x()
        y = mouse_point.y()

        # 找最接近的 idx
        if not self.x_data:
            return
        # 线性搜索也足够快（< 500 点）
        idx = min(range(len(self.x_data)),
                  key=lambda i: abs(self.x_data[i] - x))
        if idx < 0 or idx >= len(self.x_data):
            return
        anchor_x = self.x_data[idx]
        anchor_y = self.y_data[idx]
        self.v_line.setPos(anchor_x)
        self.h_line.setPos(y)
        self.text_label.setPos(anchor_x, anchor_y)
        self.text_label.setHtml(self.label_text_fn(idx))
        self.v_line.setVisible(True)
        self.h_line.setVisible(True)
        self.text_label.setVisible(True)


__all__ = ["CrosshairOverlay"]
