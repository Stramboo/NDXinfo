# -*- coding: utf-8 -*-
"""pytest 公共配置：把项目根加进 sys.path，免 pip install -e。"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
