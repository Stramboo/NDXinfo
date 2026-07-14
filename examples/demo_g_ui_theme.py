"""Demo F: 主题切换（dark / light）+ GUI widgets 不依赖实例化即可 import"""
import sys
sys.path.insert(0, r'e:\Projects\NDXinfo')

from gui.styles import get_palette, apply_theme, GLOBAL_STYLESHEET, LIGHT_PALETTE

print('=== Demo F: 主题切换 ===')

# F-1: 调色板
print('\n[F-1] 调色板')
dark = get_palette('dark')
light = get_palette('light')
print('  dark BG_DARK       = ' + dark['BG_DARK']      + '  text=' + dark['TEXT_PRIMARY'])
print('  light BG_DARK      = ' + light['BG_DARK']     + '  text=' + light['TEXT_PRIMARY'])
assert dark['BG_DARK'] == '#0d1117'
assert light['BG_DARK'] == '#ffffff'

# F-2: QSS 渲染
print('\n[F-2] apply_theme 生成 QSS')
qss_d = apply_theme(None, 'dark')
qss_l = apply_theme(None, 'light')
print('  dark qss length: ' + str(len(qss_d)))
print('  light qss length: ' + str(len(qss_l)))
print('  dark has  #0d1117 -> ' + str('#0d1117' in qss_d))
print('  light has #ffffff -> ' + str('#ffffff' in qss_l))
print('  dark has  crosshair? no, that is widget class')

# F-3: GUI 子模块 import 链（不需要 QApplication，只是语法 + import）
print('\n[F-3] GUI 子模块 import')
from gui.widgets.crosshair import CrosshairOverlay
from gui.widgets.filter_proxy import FilteredTable, TextFilterProxy
from gui.notify import Notifier
from gui.state_store import StateStore
print('  CrosshairOverlay, FilteredTable, Notifier, StateStore 全部 import OK')
print('F_OK')
