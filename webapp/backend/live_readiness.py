# -*- coding: utf-8 -*-
"""
live_readiness.py — 实盘 readiness 考核 (v2.5 Phase 3a)

模拟→实盘的心理过渡考核，不做全自动实盘交易。
4 维度考核：知识/纪律/情绪/风控，全部通过才建议进入实盘。
"""

READINESS_DIMENSIONS = {
    "knowledge": {
        "name": "知识储备",
        "description": "完成 24 课时 + 至少 2 个阶段考试通过",
        "pass_score": 70,
        "check": lambda store: _check_knowledge(store),
    },
    "discipline": {
        "name": "交易纪律",
        "description": "至少 10 笔模拟交易 + 5 次复盘 + 交易计划使用率>50%",
        "pass_score": 70,
        "check": lambda store: _check_discipline(store),
    },
    "emotion": {
        "name": "情绪管理",
        "description": "完成 3+ 情绪训练 + 理性度>60",
        "pass_score": 70,
        "check": lambda store: _check_emotion(store),
    },
    "risk_control": {
        "name": "风控能力",
        "description": "模拟盘最大回撤<20% + 无恐慌卖出记录",
        "pass_score": 70,
        "check": lambda store: _check_risk(store),
    },
}


def _check_knowledge(store) -> dict:
    """知识维度考核"""
    try:
        progress = store.learning_progress_list()
        completed = sum(1 for p in progress if p.get("completed"))
        # 阶段考试通过数
        passed_exams = store.quiz_results_passed("stage_exam")

        score = 0
        # 24 课完成度
        score += min(50, completed / 24 * 50)
        # 阶段考试通过数（至少 2 个）
        score += min(50, len(passed_exams) / 2 * 50)

        return {
            "score": int(score),
            "passed": score >= 70,
            "evidence": f"完成 {completed}/24 课，通过 {len(passed_exams)} 个阶段考试",
        }
    except Exception as e:
        return {"score": 0, "passed": False, "evidence": f"考核失败: {e}"}


def _check_discipline(store) -> dict:
    """纪律维度考核"""
    try:
        orders = store.sandbox_orders_list(100)
        reviews = store.review_list(100)
        plans = store.trade_plan_list(100)

        score = 0
        # 10 笔交易
        trades = len(orders)
        score += min(40, trades / 10 * 40)
        # 5 次复盘
        review_count = len(reviews)
        score += min(30, review_count / 5 * 30)
        # 交易计划使用率
        if trades > 0:
            plan_rate = min(len(plans), trades) / trades
            score += min(30, plan_rate * 30)

        return {
            "score": int(score),
            "passed": score >= 70,
            "evidence": f"{trades} 笔交易，{review_count} 次复盘，{len(plans)} 个交易计划",
        }
    except Exception as e:
        return {"score": 0, "passed": False, "evidence": f"考核失败: {e}"}


def _check_emotion(store) -> dict:
    """情绪维度考核"""
    try:
        journals = store.emotion_journal_list(100)
        if not journals:
            return {"score": 0, "passed": False, "evidence": "无情绪训练记录"}

        avg_rationality = sum(j["rationality_score"] for j in journals) / len(journals)
        score = int(min(100, avg_rationality))

        return {
            "score": score,
            "passed": score >= 70 and len(journals) >= 3,
            "evidence": f"{len(journals)} 次情绪训练，平均理性度 {score}",
        }
    except Exception as e:
        return {"score": 0, "passed": False, "evidence": f"考核失败: {e}"}


def _check_risk(store) -> dict:
    """风控维度考核"""
    try:
        reviews = store.review_list(50)
        # 检查恐慌卖出
        panic_count = sum(1 for r in reviews
                          if any(m.get("pattern") == "panic_sell" for m in r.get("mistakes", [])))

        # 模拟盘净值（简化：用快照）
        snapshots = store.sandbox_snapshots_list(100)
        max_drawdown = 0
        if len(snapshots) >= 2:
            peak = snapshots[0]["equity"]
            for s in snapshots:
                if s["equity"] > peak:
                    peak = s["equity"]
                dd = (peak - s["equity"]) / peak * 100 if peak > 0 else 0
                max_drawdown = max(max_drawdown, dd)

        score = 100
        # 回撤扣分
        if max_drawdown > 20:
            score -= (max_drawdown - 20) * 2
        # 恐慌卖出扣分
        score -= panic_count * 15
        score = max(0, min(100, int(score)))

        return {
            "score": score,
            "passed": score >= 70,
            "evidence": f"最大回撤 {max_drawdown:.1f}%，恐慌卖出 {panic_count} 次",
        }
    except Exception as e:
        return {"score": 0, "passed": False, "evidence": f"考核失败: {e}"}


def evaluate_readiness(store) -> dict:
    """完整实盘 readiness 评估"""
    results = {}
    all_passed = True
    for dim_id, dim in READINESS_DIMENSIONS.items():
        result = dim["check"](store)
        results[dim_id] = {
            "name": dim["name"],
            "description": dim["description"],
            "score": result["score"],
            "passed": result["passed"],
            "evidence": result["evidence"],
        }
        if not result["passed"]:
            all_passed = False

        # 保存到 userstore
        try:
            store.live_readiness_save(dim_id, result["score"], result["passed"], result["evidence"])
        except Exception:
            pass

    overall = int(sum(r["score"] for r in results.values()) / len(results))

    return {
        "dimensions": results,
        "all_passed": all_passed,
        "overall_score": overall,
        "recommendation": _get_recommendation(all_passed, results, overall),
    }


def _get_recommendation(all_passed: bool, results: dict, overall: int) -> str:
    """生成实盘建议"""
    if all_passed:
        return ("🎉 恭喜！你已具备进入实盘的基础能力。建议从小资金开始（不超过可承受亏损的 10%），"
                "继续严格执行模拟盘学到的纪律。记住：实盘的心理压力是模拟盘的 10 倍。")
    elif overall >= 60:
        weak = [r["name"] for r in results.values() if not r["passed"]]
        return f"⚠️ 你在以下方面还需加强：{', '.join(weak)}。建议补强后再考虑实盘。"
    else:
        return ("❌ 你还未准备好进入实盘。继续在模拟盘练习，完成更多课程和情绪训练。"
                "记住：模拟盘赚不到钱，实盘更赚不到。")


__all__ = ["READINESS_DIMENSIONS", "evaluate_readiness"]
