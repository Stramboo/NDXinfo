# -*- coding: utf-8 -*-
"""
NASDAQ 每日分析报告 - ML 价格预测模块
基于 scikit-learn 的 RandomForestRegressor 预测未来 N 日收益与方向

设计要点：
- 轻量级：单模型、少量特征、快速训练
- 优雅降级：未安装 sklearn 或数据不足时返回 None，不影响主流程
- 时序安全：特征仅使用历史信息，目标为未来收益，按时间顺序划分训练/验证集
- 可解释：输出特征重要性，辅助理解模型决策

可选依赖：scikit-learn（pip install scikit-learn）
"""

import logging
import numpy as np
import pandas as pd
from config import ML_FORECAST_HORIZON, BACKTEST_LOOKBACK

logger = logging.getLogger(__name__)

# ============================================================
# 可选依赖：scikit-learn（未安装时优雅降级，标记为不可用）
# ============================================================
try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import r2_score
    _SKLEARN_AVAILABLE = True
except ImportError:
    RandomForestRegressor = None
    r2_score = None
    _SKLEARN_AVAILABLE = False


# ============================================================
# 模块常量
# ============================================================

# 特征列定义（与 _engineer_features 中创建的列一一对应）
FEATURE_COLS = [
    "ret_1d",        # 1 日收益率
    "ret_3d",        # 3 日收益率
    "ret_5d",        # 5 日收益率
    "rsi",           # RSI(14) 数值
    "macd_hist",     # MACD 柱状图
    "vol_change",    # 成交量变化率
    "dist_ma5",      # 收盘价偏离 MA5 百分比
    "dist_ma20",     # 收盘价偏离 MA20 百分比
    "boll_pos",      # 布林带相对位置（0=下轨, 1=上轨）
]

# 方向判断阈值（百分点）：预测收益绝对值超过此值才判为上涨/下跌，否则为震荡
DIRECTION_THRESHOLD = 1.0

# 最小有效训练样本数（特征与目标均非空的行）
MIN_SAMPLES = 50

# 训练/验证划分比例（前 80% 训练，后 20% 验证）
TRAIN_RATIO = 0.8


def _engineer_features(df):
    """
    工程化 ML 特征矩阵

    输入: 已计算全部技术指标的 DataFrame（需含 Close/Volume/RSI/MACD/MA/BOLL 等列）
    返回: 新 DataFrame，包含 Close 与 9 个特征列（索引与输入一致）

    特征说明：
      - ret_1d/3d/5d : 过去 1/3/5 日收益率（滞后特征，无未来信息泄露）
      - rsi          : RSI(14) 相对强弱指标
      - macd_hist    : MACD 柱状图（优先取 MACD_HIST 列，否则用 DIF - DEA 兜底）
      - vol_change   : 成交量环比变化率
      - dist_ma5/20  : 收盘价偏离 MA5/MA20 的百分比
      - boll_pos     : 收盘价在布林带中的相对位置（0=下轨, 0.5=中轨, 1=上轨）
    """
    feat = pd.DataFrame(index=df.index)
    feat["Close"] = df["Close"]

    close = df["Close"]

    # 1. 滞后收益率（1/3/5 日）
    feat["ret_1d"] = close.pct_change(1)
    feat["ret_3d"] = close.pct_change(3)
    feat["ret_5d"] = close.pct_change(5)

    # 2. RSI 数值
    feat["rsi"] = df["RSI"] if "RSI" in df.columns else np.nan

    # 3. MACD 柱状图（优先 MACD_HIST 列，否则用 DIF - DEA 兜底）
    if "MACD_HIST" in df.columns:
        feat["macd_hist"] = df["MACD_HIST"]
    elif "DIF" in df.columns and "DEA" in df.columns:
        feat["macd_hist"] = df["DIF"] - df["DEA"]
    else:
        feat["macd_hist"] = np.nan

    # 4. 成交量变化率（环比）
    if "Volume" in df.columns:
        feat["vol_change"] = df["Volume"].pct_change(1)
    else:
        feat["vol_change"] = np.nan

    # 5. 收盘价偏离 MA5 / MA20 的百分比
    if "MA5" in df.columns:
        feat["dist_ma5"] = (close - df["MA5"]) / df["MA5"] * 100
    else:
        feat["dist_ma5"] = np.nan
    if "MA20" in df.columns:
        feat["dist_ma20"] = (close - df["MA20"]) / df["MA20"] * 100
    else:
        feat["dist_ma20"] = np.nan

    # 6. 布林带相对位置（归一化到 [0, 1]，0=下轨, 1=上轨）
    if "BOLL_UPPER" in df.columns and "BOLL_LOWER" in df.columns:
        boll_width = (df["BOLL_UPPER"] - df["BOLL_LOWER"]).replace(0, np.nan)
        feat["boll_pos"] = (close - df["BOLL_LOWER"]) / boll_width
    else:
        feat["boll_pos"] = np.nan

    # 清理可能的 inf（如成交量为 0 导致的除零），统一转为 NaN 便于后续 dropna
    feat = feat.replace([np.inf, -np.inf], np.nan)

    return feat


def predict_price(df, horizon=ML_FORECAST_HORIZON):
    """
    使用 RandomForest 预测未来价格走势

    参数:
      df      : 已计算技术指标的 DataFrame（含 Close/Volume/RSI/MACD/MA/BOLL 等）
      horizon : 预测天数，默认取 config.ML_FORECAST_HORIZON（5 日）

    返回:
      dict | None
      - predicted_direction : str   - "上涨" / "下跌" / "震荡"
      - predicted_return    : float - 预测未来 horizon 日收益率（百分比）
      - confidence          : float - 置信度 [0, 1]，基于验证集 R²
      - predicted_prices    : list  - 未来 horizon 日预测收盘价列表
      - feature_importance  : dict  - 前 5 重要特征及其重要性得分
      若 sklearn 未安装、数据不足或训练失败，返回 None（优雅降级）
    """
    try:
        # ---- 1. 前置检查：sklearn 可用性 ----
        if not _SKLEARN_AVAILABLE:
            logger.warning(
                "ML 预测跳过：未安装 scikit-learn。"
                "安装命令: pip install scikit-learn"
            )
            return None

        # ---- 2. 前置检查：数据有效性 ----
        if df is None or df.empty:
            logger.warning("ML 预测跳过：输入数据为空")
            return None

        if len(df) < MIN_SAMPLES:
            logger.warning(f"ML 预测跳过：数据量不足（{len(df)} < {MIN_SAMPLES}）")
            return None

        if "Close" not in df.columns:
            logger.warning("ML 预测跳过：缺少 Close 列")
            return None

        # ---- 3. 工程化特征 + 目标 ----
        # 在完整数据上计算特征，避免截取窗口后边界出现 NaN（滞后特征需引用窗口外数据）
        feat_df = _engineer_features(df)
        # 目标：未来 horizon 日的累计收益率（百分比）
        feat_df["target"] = (df["Close"].shift(-horizon) / df["Close"] - 1) * 100

        # 截取最近 BACKTEST_LOOKBACK 个交易日作为训练数据窗口
        feat_df = feat_df.tail(BACKTEST_LOOKBACK).copy()

        # 删除含 NaN 的行（指标预热期 + 缺失的未来目标）
        clean = feat_df.dropna()
        if len(clean) < MIN_SAMPLES:
            logger.warning(
                f"ML 预测跳过：有效训练样本不足（{len(clean)} < {MIN_SAMPLES}）"
            )
            return None

        # ---- 4. 时序划分训练/验证集（前 80% 训练，后 20% 验证，避免未来信息泄露）----
        split_idx = int(len(clean) * TRAIN_RATIO)
        train_df = clean.iloc[:split_idx]
        val_df = clean.iloc[split_idx:]

        X_train = train_df[FEATURE_COLS]
        y_train = train_df["target"]
        X_val = val_df[FEATURE_COLS]
        y_val = val_df["target"]

        # ---- 5. 训练 RandomForest ----
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=8,
            min_samples_leaf=5,
            random_state=42,
        )
        model.fit(X_train, y_train)
        logger.info(
            f"ML 模型训练完成：训练集 {len(train_df)} 条，验证集 {len(val_df)} 条"
        )

        # ---- 6. 验证集评估（R² → 置信度）----
        if len(val_df) >= 2:
            y_val_pred = model.predict(X_val)
            r2 = r2_score(y_val, y_val_pred)
            # R² 可能为负（模型差于均值），截断到 [0, 1] 作为置信度
            confidence = float(max(0.0, min(1.0, r2)))
            logger.info(f"ML 验证集 R²={r2:.4f}，置信度={confidence:.4f}")
        else:
            confidence = 0.0
            logger.warning("ML 验证集样本不足 2 条，置信度置 0")

        # ---- 7. 预测最新一期未来收益 ----
        # 取特征完整的最新一行进行预测（target 为 NaN 属正常，因尚无未来数据）
        predictable = feat_df.dropna(subset=FEATURE_COLS)
        if predictable.empty:
            logger.warning("ML 预测跳过：无完整特征行可用于预测")
            return None

        X_pred = predictable[FEATURE_COLS].iloc[[-1]]
        last_close = float(predictable["Close"].iloc[-1])
        raw_return = float(model.predict(X_pred)[0])

        # ---- 8. 推导预测价格路径（按日复利分解总收益）----
        # 模型预测的是 horizon 日总收益，此处按等比复利分解为逐日价格
        total_factor = max(1.0 + raw_return / 100.0, 0.01)  # 防止负底数导致 NaN
        daily_factor = total_factor ** (1.0 / horizon)
        predicted_prices = [
            round(last_close * (daily_factor ** (i + 1)), 2)
            for i in range(horizon)
        ]

        # ---- 9. 判断方向 ----
        if raw_return > DIRECTION_THRESHOLD:
            direction = "上涨"
        elif raw_return < -DIRECTION_THRESHOLD:
            direction = "下跌"
        else:
            direction = "震荡"

        # ---- 10. 提取特征重要性（前 5）----
        importances = model.feature_importances_
        feat_imp_pairs = sorted(
            zip(FEATURE_COLS, importances),
            key=lambda x: x[1],
            reverse=True,
        )[:5]
        feature_importance = {
            name: round(float(imp), 4) for name, imp in feat_imp_pairs
        }

        # ---- 11. 组装结果 ----
        prediction_result = {
            "predicted_direction": direction,
            "predicted_return": round(raw_return, 2),
            "confidence": round(confidence, 4),
            "predicted_prices": predicted_prices,
            "feature_importance": feature_importance,
        }

        logger.info(
            f"ML 预测结果：方向={direction}，收益={raw_return:.2f}%，"
            f"置信度={confidence:.2%}，预测价格={predicted_prices}"
        )

        return prediction_result

    except Exception as e:
        logger.warning(f"ML 预测失败，已优雅降级: {e}", exc_info=True)
        return None
