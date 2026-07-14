"""
capture_pages.py — 用 Playwright 给 5 个 React 页面各拍一张截图

要求：开发服务器已经在 5173 上跑着，FastAPI 后端在 8765 上跑着
执行：python -m webapp.scripts.capture_pages
输出：webapp/screenshots/{dashboard,trading,strategy,logs,settings}.png
"""

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT  = ROOT / "webapp" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

URL = "http://127.0.0.1:5173"

PAGES = [
    ("dashboard", "/"),
    ("trading",   "/trading"),
    ("strategy",  "/strategy"),
    ("logs",      "/logs"),
    ("settings",  "/settings"),
]


def main() -> int:
    from playwright.sync_api import sync_playwright

    print("=== capture_pages: 5 React pages via Playwright ===")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900},
                                  color_scheme="dark")
        page = ctx.new_page()

        # 字体加载需要时间 — 第一次访问后等久一点
        page.goto(URL + "/", wait_until="networkidle", timeout=30_000)
        time.sleep(2.0)

        for name, path in PAGES:
            url = URL + path
            print(f"  -> {name:9s}  {url}")
            page.goto(url, wait_until="networkidle", timeout=15_000)
            # 让 WS 推送几次 & React 组件 mount 完成
            time.sleep(2.0)
            # 把 K 线图设为深色（如果存在）
            out = OUT / f"{name}.png"
            page.screenshot(path=str(out), full_page=True)
            size = os.path.getsize(out)
            print(f"     saved {out.name}  {size:,} bytes")

        # 浅色主题再拍 dashboard
        print("  -> dashboard (light)")
        try:
            # 1) 先访问一次让 origin 存在
            page.goto(URL + "/", wait_until="domcontentloaded", timeout=10_000)
            time.sleep(1.0)
            # 2) 直接写 localStorage + reload
            page.evaluate("localStorage.setItem('ndxinfo.theme', 'light')")
            page.reload(wait_until="networkidle", timeout=10_000)
            time.sleep(2.0)
            out = OUT / "dashboard_light.png"
            page.screenshot(path=str(out), full_page=True)
            print(f"     saved {out.name}  {os.path.getsize(out):,} bytes")
            # 3) 恢复深色
            page.evaluate("localStorage.setItem('ndxinfo.theme', 'dark')")
        except Exception as e:
            print(f"     [warn] light theme capture failed: {e}")

        browser.close()
    print(f"\n  outputs: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
