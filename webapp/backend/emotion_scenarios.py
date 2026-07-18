# -*- coding: utf-8 -*-
"""
emotion_scenarios.py — 情绪训练场景库 (v2.5 Phase 1b)

FOMO/FUD/恐慌/贪婪等情绪场景，复用 ScenarioTraining 分支决策引擎
新增 emotion_context 字段：压力等级、时间限制、行情剧变
"""

EMOTION_SCENARIOS = [
    {
        "id": "em01", "title": "FOMO：错过的暴涨",
        "description": "你关注的股票一周涨了 40%，朋友圈晒单无数。你空仓，焦虑感爆棚。",
        "emotion_type": "fomo",
        "difficulty": "easy",
        "emotion_context": {"stress_level": 7, "time_pressure": "low", "market_state": "euphoric"},
        "context": {"stock": "AI 概念股", "gain": "+40% 一周", "social_hype": "极高"},
        "steps": [
            {"id": "step1", "question": "看到别人晒单赚 40%，你的第一感觉是？",
             "options": [
                 {"id": "a", "text": "焦虑+嫉妒，必须马上买入", "result": "bad", "feedback": "这是典型 FOMO。别人的盈利与你无关，追高大概率买在顶部。"},
                 {"id": "b", "text": "承认错过，但不行动", "result": "good", "feedback": "成熟的投资者懂得：错过机会不可怕，追高亏钱才可怕。市场永远有下一个机会。"},
                 {"id": "c", "text": "研究上涨原因，评估是否还有机会", "result": "good", "feedback": "理性分析。区分「真实利好」和「纯炒作」，再决定是否参与。"}]},
            {"id": "step2", "question": "你决定研究。发现上涨是因为一个未证实的传闻。你？",
             "options": [
                 {"id": "a", "text": "传闻也可能是真的，小仓位搏一下", "result": "partial", "feedback": "如果一定要参与，小仓位+紧止损是相对合理的。但本质是赌博。"},
                 {"id": "b", "text": "传闻未证实，放弃这个机会", "result": "good", "feedback": "纪律性决策。基于传闻交易是韭菜行为，错过不可怕。"},
                 {"id": "c", "text": "全仓 All in，不能错过", "result": "bad", "feedback": "极度危险。基于未证实传闻全仓，一旦传闻被否认将血本无归。"}]},
            {"id": "step3", "question": "三天后股价暴跌 25%，回到上涨前。你的感受？",
             "options": [
                 {"id": "a", "text": "庆幸没买，但反思为什么想追", "result": "good", "feedback": "完美的复盘心态。识别自己的 FOMO 情绪，是克服它的第一步。"},
                 {"id": "b", "text": "后悔没早点买", "result": "bad", "feedback": "你还在 FOMO。事实是：如果在顶部买入，你会亏 25%。庆幸才是正确反应。"},
                 {"id": "c", "text": "现在跌了，可以抄底了", "result": "bad", "feedback": "下跌不是买入理由。需要重新评估基本面，而不是因为「便宜了」。"}]},
        ],
        "takeaway": "FOMO 是散户最大的敌人之一。记住：你看到的「别人赚钱」是幸存者偏差，亏钱的人不会晒单。错过机会永远比追高亏钱好。",
        "emotion_lesson": "识别 FOMO 的身体信号：心跳加速、焦虑、反复看行情、嫉妒。出现这些信号时，强制自己 24 小时再决策。",
        "xp": 60,
    },
    {
        "id": "em02", "title": "恐慌：黑天鹅暴跌",
        "description": "突发重大利空，大盘一天跌 8%，你的持仓一片惨绿。恐慌情绪蔓延。",
        "emotion_type": "panic",
        "difficulty": "medium",
        "emotion_context": {"stress_level": 9, "time_pressure": "high", "market_state": "panic"},
        "context": {"portfolio": "-12% 单日", "news": "重大利空", "vix": "飙升 80%"},
        "steps": [
            {"id": "step1", "question": "开盘看到持仓 -12%，心跳加速。你的第一反应是？",
             "options": [
                 {"id": "a", "text": "立即全部清仓，止损出局", "result": "bad", "feedback": "恐慌性清仓往往卖在最低点。黑天鹅暴跌后常有反弹，情绪化决策最危险。"},
                 {"id": "b", "text": "关闭行情软件，冷静 30 分钟", "result": "good", "feedback": "优秀的做法。识别恐慌情绪，强制冷静，避免冲动决策。"},
                 {"id": "c", "text": "立即加仓抄底", "result": "bad", "feedback": "暴跌中抄底=接飞刀。你不知道这是刚开始跌还是快见底。"}]},
            {"id": "step2", "question": "冷静后，你应该检查什么？（思考后选择）",
             "options": [
                 {"id": "a", "text": "检查止损是否被触发，仓位是否超标", "result": "good", "feedback": "正确的优先级。先看风控，再看基本面，最后决策。"},
                 {"id": "b", "text": "刷新闻看还会跌多少", "result": "partial", "feedback": "新闻只会加剧恐慌。应该看数据而非情绪化报道。"},
                 {"id": "c", "text": "算算自己亏了多少钱", "result": "bad", "feedback": "沉没成本思维。关注「未来会怎样」而非「亏了多少」。"}]},
            {"id": "step3", "question": "检查后发现：止损未触发，买入理由依然成立，仓位合理。你？",
             "options": [
                 {"id": "a", "text": "按计划持有，等市场恢复", "result": "good", "feedback": "纪律的胜利。信任自己的研究和计划，不被恐慌带偏。"},
                 {"id": "b", "text": "还是害怕，卖一半心里踏实", "result": "partial", "feedback": "可以理解，但说明你对计划信心不足。记录这次情绪，下次建立更强信念。"},
                 {"id": "c", "text": "既然便宜了，全仓加", "result": "bad", "feedback": "贪婪伪装成「抄底」。加仓需要新理由，不能因为「跌了」就加。"}]},
        ],
        "takeaway": "暴跌时的第一原则：不要在恐慌中做决策。识别情绪→强制冷静→检查风控→评估逻辑→按计划行动。",
        "emotion_lesson": "恐慌的身体信号：胸闷、手抖、反复刷新、想立刻行动。出现时执行「30 分钟冷静期」规则。",
        "xp": 80,
    },
    {
        "id": "em03", "title": "贪婪：该止盈时不止盈",
        "description": "你的股票涨了 50%，分析师说还能涨到 100%。落袋为安还是让利润奔跑？",
        "emotion_type": "greed",
        "difficulty": "medium",
        "emotion_context": {"stress_level": 5, "time_pressure": "low", "market_state": "bullish"},
        "context": {"position": "+50%", "analyst_target": "+100%", "temptation": "高"},
        "steps": [
            {"id": "step1", "question": "持仓 +50%，分析师说还能翻倍。你的内心 OS？",
             "options": [
                 {"id": "a", "text": "赚翻了，必须拿到翻倍", "result": "bad", "feedback": "贪婪。分析师不是神仙，他们的目标价经常不准。浮盈不是真利润。"},
                 {"id": "b", "text": "卖一半锁利，剩一半设跟踪止损", "result": "good", "feedback": "成熟的策略。既锁定部分利润，又保留上涨参与权，风险可控。"},
                 {"id": "c", "text": "全部卖出，落袋为安", "result": "partial", "feedback": "保守但合理。如果公司基本面依然强劲，全部卖出可能错过后续上涨。"}]},
            {"id": "step2", "question": "你卖了一半。一周后股价又涨 15%。你的感受？",
             "options": [
                 {"id": "a", "text": "后悔卖早了，应该全仓拿到现在", "result": "bad", "feedback": "事后诸葛亮。你做出了当时最理性的决策，这就够了。完美主义是投资大敌。"},
                 {"id": "b", "text": "不后悔，剩下一半还在赚", "result": "good", "feedback": "健康的复盘心态。没有完美操作，只有当时最优决策。"},
                 {"id": "c", "text": "把卖掉的再买回来", "result": "bad", "feedback": "情绪化操作。已经涨了 15%，现在买入是追高。坚持原计划。"}]},
            {"id": "step3", "question": "股价从最高点回撤 15%，触发你的跟踪止损。你？",
             "options": [
                 {"id": "a", "text": "按纪律卖出剩余仓位", "result": "good", "feedback": "完美的纪律执行。跟踪止损让你锁住了大部分利润。"},
                 {"id": "b", "text": "止损太死了，再给它点空间", "result": "bad", "feedback": "随意调宽止损=没有止损。利润回撤时最容易贪心，要警惕。"},
                 {"id": "c", "text": "全部卖掉，再也不看了", "result": "partial", "feedback": "情绪化逃避。应该按计划执行，然后复盘总结。"}]},
        ],
        "takeaway": "贪婪比恐惧更难识别。止盈策略：分批锁利+跟踪止损。记住：没落袋的利润都是数字，卖出的才是真钱。",
        "emotion_lesson": "贪婪的信号：觉得「还能涨更多」、不愿止盈、加仓加杠杆。出现时回顾原计划，问自己「如果现在没持仓，我会买入吗？」",
        "xp": 70,
    },
    {
        "id": "em04", "title": "报复性交易：亏损后的愤怒",
        "description": "你刚亏了 8% 止损出局，心情烦躁，想立刻「赚回来」。",
        "emotion_type": "revenge",
        "difficulty": "hard",
        "emotion_context": {"stress_level": 8, "time_pressure": "high", "market_state": "normal"},
        "context": {"recent_loss": "-8%", "emotion": "愤怒+不甘", "temptation": "立即重仓搏一把"},
        "steps": [
            {"id": "step1", "question": "刚止损亏了 8%，你的第一反应是？",
             "options": [
                 {"id": "a", "text": "立刻找下一只股票重仓搏回", "result": "bad", "feedback": "报复性交易！亏损后的冲动决策是散户破产的最快路径。"},
                 {"id": "b", "text": "关闭软件，今天不再交易", "result": "good", "feedback": "明智的选择。亏损后强制冷却，避免情绪化决策扩大损失。"},
                 {"id": "c", "text": "复盘这笔交易，记录教训", "result": "good", "feedback": "成熟的反应。把亏损转化为学习机会，是长期盈利的关键。"}]},
            {"id": "step2", "question": "冷静后你复盘发现：止损是对的，但买入理由有问题。你？",
             "options": [
                 {"id": "a", "text": "承认错误，改进买入标准", "result": "good", "feedback": "高手思维。亏损是学费，复盘是收获。"},
                 {"id": "b", "text": "还是觉得是市场错了，不是我的问题", "result": "bad", "feedback": "推卸责任。市场永远是对的，你只能改进自己。"},
                 {"id": "c", "text": "从此不再相信止损", "result": "bad", "feedback": "因噎废食。止损本身是对的，问题在买入逻辑。"}]},
            {"id": "step3", "question": "第二天，你看到一只「看起来很好」的股票。你？",
             "options": [
                 {"id": "a", "text": "昨天亏了，今天必须赚回来，重仓", "result": "bad", "feedback": "报复性交易升级。昨天的亏损与今天的决策无关，每笔交易独立。"},
                 {"id": "b", "text": "按正常流程研究，符合标准才小仓位试", "result": "good", "feedback": "纪律性回归。每笔交易独立评估，不受前一笔盈亏影响。"},
                 {"id": "c", "text": "再观察几天，空仓不是坏事", "result": "good", "feedback": "耐心是美德。空仓等待符合标准的机会，远胜于为了交易而交易。"}]},
        ],
        "takeaway": "报复性交易是散户最危险的行为之一。亏损后的 24 小时是「危险期」，强制冷却+复盘是最佳策略。记住：每笔交易独立，前一笔的亏损不是这一笔必须赚回来的理由。",
        "emotion_lesson": "报复性交易的信号：愤怒、想「赚回来」、重仓冲动、频繁交易。出现时执行「24 小时冷静期」+ 复盘上一笔交易。",
        "xp": 90,
    },
]


def get_emotion_scenario(scenario_id: str) -> dict | None:
    """获取情绪训练场景（不含答案）"""
    s = next((s for s in EMOTION_SCENARIOS if s["id"] == scenario_id), None)
    if not s:
        return None
    # 返回时移除 result 字段（前端不显示）
    safe = {
        "id": s["id"], "title": s["title"], "description": s["description"],
        "emotion_type": s["emotion_type"], "difficulty": s["difficulty"],
        "emotion_context": s["emotion_context"], "context": s["context"],
        "steps": [{
            "id": step["id"], "question": step["question"],
            "options": [{"id": o["id"], "text": o["text"]} for o in step["options"]],
        } for step in s["steps"]],
    }
    return safe


def get_emotion_scenario_with_answers(scenario_id: str) -> dict | None:
    """获取完整情绪场景（含答案，用于评估）"""
    return next((s for s in EMOTION_SCENARIOS if s["id"] == scenario_id), None)


def list_emotion_scenarios() -> list[dict]:
    """列出情绪训练场景"""
    return [{"id": s["id"], "title": s["title"], "emotion_type": s["emotion_type"],
             "difficulty": s["difficulty"], "xp": s["xp"]} for s in EMOTION_SCENARIOS]


__all__ = [
    "EMOTION_SCENARIOS", "get_emotion_scenario",
    "get_emotion_scenario_with_answers", "list_emotion_scenarios",
]
