@echo off
REM ============================================================
REM  Run all demos (one-shot regression for trader optimizations).
REM  Working dir: e:\Projects\NDXinfo
REM
REM  This batch uses chcp 65001 for UTF-8 echo lines; if the
REM  console still mis-decodes them, the demos themselves are
REM  unaffected (they print OK / FAIL on the last line).
REM ============================================================

setlocal
chcp 65001 >nul
cd /d "%~dp0\.."

echo.
echo ============================================================
echo  step 1/9 : pytest (29 cases + coverage)
echo ============================================================
python -m pytest tests --cov=trading --cov=backtest --cov-report=term --cov-report=xml:coverage.xml --cov-report=html:htmlcov -q
if errorlevel 1 goto fail

echo.
echo ============================================================
echo  step 2/9 : demo_a_broker_basic.py
echo ============================================================
python examples\demo_a_broker_basic.py
if errorlevel 1 goto fail

echo.
echo ============================================================
echo  step 3/9 : demo_b_broker_rules.py
echo ============================================================
python examples\demo_b_broker_rules.py
if errorlevel 1 goto fail

echo.
echo ============================================================
echo  step 4/9 : demo_c_backtest.py
echo ============================================================
python examples\demo_c_backtest.py
if errorlevel 1 goto fail

echo.
echo ============================================================
echo  step 5/9 : demo_d_config.py
echo ============================================================
python examples\demo_d_config.py
if errorlevel 1 goto fail

echo.
echo ============================================================
echo  step 6/9 : demo_e_observability.py
echo ============================================================
python examples\demo_e_observability.py
if errorlevel 1 goto fail

echo.
echo ============================================================
echo  step 7/9 : demo_f_strategies.py
echo ============================================================
python examples\demo_f_strategies.py
if errorlevel 1 goto fail

echo.
echo ============================================================
echo  step 8/9 : demo_g_ui_theme.py
echo ============================================================
python examples\demo_g_ui_theme.py
if errorlevel 1 goto fail

echo.
echo ============================================================
echo  step 9/9 : capture_gui.py  (dark/light PNG, offscreen)
echo ============================================================
set QT_QPA_PLATFORM=offscreen
python examples\capture_gui.py
if errorlevel 1 goto fail

echo.
echo ============================================================
echo  ALL DEMOS PASSED.
echo ============================================================
exit /b 0

:fail
echo.
echo *** FAILED at the step above.  See error above. ***
exit /b 1
