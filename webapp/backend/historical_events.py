# -*- coding: utf-8 -*-
"""
historical_events.py — 历史事件回放库 (v2.5 Phase 1c)

重大金融历史事件交互式回放：2008 金融危机、2020 COVID、2021 Meme 股等
每个事件含时间轴、关键决策点、历史走势对比、教学复盘
"""

HISTORICAL_EVENTS = [
    {
        "id": "he01", "title": "2008 全球金融危机",
        "subtitle": "雷曼倒下与全球熊市",
        "start_date": "2008-09-01", "end_date": "2009-03-01",
        "severity": "extreme",
        "symbols": ["SPY", "LEHMQ"],
        "summary": "次贷危机引发全球金融海啸，雷曼兄弟破产，标普500 跌逾 50%。",
        "key_dates": [
            {"date": "2008-09-15", "title": "雷曼兄弟破产", "desc": "美国第四大投行破产，引发全球恐慌"},
            {"date": "2008-10-06", "title": "全球股市单周暴跌", "desc": "道指单周跌 18%，创历史"},
            {"date": "2008-11-20", "title": "标普触及 11 年低点", "desc": "市场极度恐慌"},
            {"date": "2009-03-09", "title": "市场见底", "desc": "标普 666 点，随后开启 10 年牛市"},
        ],
        "decision_points": [
            {
                "date": "2008-09-15", "title": "雷曼破产当天",
                "question": "雷曼倒下，你持有银行股。你？",
                "options": [
                    {"id": "a", "text": "立即清仓所有股票", "result": "partial",
                     "feedback": "恐慌性清仓。短期避险但可能错过 2009 年的反弹。",
                     "historical_outcome": "如果你当天清仓，错过了 2009 年 3 月开始的 10 年牛市。"},
                    {"id": "b", "text": "检查持仓，卖出基本面恶化的，保留优质股", "result": "good",
                     "feedback": "理性筛选。区分「系统性风险」和「公司特定风险」。",
                     "historical_outcome": "优质公司如苹果、强生在危机后快速恢复并创新高。"},
                    {"id": "c", "text": "全部加仓抄底", "result": "bad",
                     "feedback": "接飞刀。危机刚开始，底部还很远（2009 年 3 月才见底）。",
                     "historical_outcome": "2008 年 9 月到 2009 年 3 月，标普又跌了 40%。"},
                ],
            },
            {
                "date": "2008-11-20", "title": "市场创新低",
                "question": "标普跌到 11 年低点，新闻全是「大萧条重来」。你？",
                "options": [
                    {"id": "a", "text": "把剩余股票全部卖掉", "result": "bad",
                     "feedback": "恐慌性割肉在最低点附近。这正是底部特征。",
                     "historical_outcome": "2008 年 11 月到 2009 年 3 月还有最后一跌，但已接近底部。"},
                    {"id": "b", "text": "定投指数，分批建仓", "result": "good",
                     "feedback": "理性抄底策略。分批建仓降低择时风险。",
                     "historical_outcome": "从 2008 年 11 月定投到 2009 年底，收益约 30%。"},
                    {"id": "c", "text": "完全离场，等「明确信号」", "result": "partial",
                     "feedback": "看似稳妥，但「明确信号」往往在牛市走了一半才出现。",
                     "historical_outcome": "等到 2009 年底确认牛市，已错过 50% 涨幅。"},
                ],
            },
            {
                "date": "2009-03-09", "title": "市场见底",
                "question": "标普跌到 666 点，所有人都在说「这次不同」。你？",
                "options": [
                    {"id": "a", "text": "相信「这次不同」，继续离场", "result": "bad",
                     "feedback": "「这次不同」是史上最贵的四个字。",
                     "historical_outcome": "错过 10 年牛市，标普从 666 涨到 4800+。"},
                    {"id": "b", "text": "开始定投，慢慢建仓", "result": "good",
                     "feedback": "正确的底部策略。无法精确抄底，但定投能抓住底部区域。",
                     "historical_outcome": "从 666 定投 5 年，年化收益约 20%。"},
                    {"id": "c", "text": "一次性全仓抄底", "result": "partial",
                     "feedback": "事后看是对的，但当时无法确认底部。运气好不代表策略对。",
                     "historical_outcome": "这次运气好，但如果继续跌 20% 你能承受吗？"}],
            },
        ],
        "lessons": [
            "危机是机会的伪装：恐慌达到极致时，往往是底部",
            "「这次不同」是投资史上最贵的四个字",
            "定投是普通人对付危机的最佳武器——不需要精确抄底",
            "区分系统性风险和公司风险：优质公司会穿越危机",
        ],
        "xp": 100,
    },
    {
        "id": "he02", "title": "2020 COVID 暴跌与反弹",
        "subtitle": "史上最快熊市与最快反弹",
        "start_date": "2020-02-19", "end_date": "2020-08-01",
        "severity": "severe",
        "symbols": ["SPY", "ZM"],
        "summary": "新冠疫情引发恐慌，标普 33 天跌 34%，随后 5 个月收复全部失地。",
        "key_dates": [
            {"date": "2020-02-19", "title": "标普创历史新高", "desc": "疫情尚未引起市场重视"},
            {"date": "2020-03-12", "title": "黑色星期四", "desc": "标普跌 9.5%，触发熔断"},
            {"date": "2020-03-23", "title": "市场见底", "desc": "美联储无限 QE 宣布"},
            {"date": "2020-08-18", "title": "标普收复失地", "desc": "创历史新高"},
        ],
        "decision_points": [
            {
                "date": "2020-02-25", "title": "疫情开始扩散",
                "question": "新闻开始报道疫情扩散，但市场只跌了 3%。你？",
                "options": [
                    {"id": "a", "text": "不以为然，继续满仓", "result": "partial",
                     "feedback": "低估了黑天鹅的威力。",
                     "historical_outcome": "随后 3 周市场跌了 34%。"},
                    {"id": "b", "text": "减仓至 50%，保留现金", "result": "good",
                     "feedback": "谨慎的风险管理。黑天鹅初期减仓是合理的。",
                     "historical_outcome": "减仓让你在暴跌中少亏一半。"},
                    {"id": "c", "text": "清仓离场", "result": "partial",
                     "feedback": "过度反应。疫情可能被控制，清仓会错过反弹。",
                     "historical_outcome": "如果你不在 3 月底买回，会错过 V 型反弹。"}],
            },
            {
                "date": "2020-03-12", "title": "熔断日",
                "question": "标普单日跌 9.5%，触发熔断。你？",
                "options": [
                    {"id": "a", "text": "恐慌清仓，保命要紧", "result": "bad",
                     "feedback": "恐慌性割肉在最低点附近。",
                     "historical_outcome": "3 月 23 日就是底，清仓在底部区域。"},
                    {"id": "b", "text": "按计划持有，不动", "result": "good",
                     "feedback": "纪律性。如果买入理由还在，暴跌不是卖出理由。",
                     "historical_outcome": "持有到 8 月，不仅回本还赚了。"},
                    {"id": "c", "text": "逆势小仓位抄底", "result": "good",
                     "feedback": "理性抄底。小仓位控制风险，抓住反弹机会。",
                     "historical_outcome": "3 月 12 日买入，到 8 月赚 50%+。"}],
            },
            {
                "date": "2020-03-23", "title": "美联储无限 QE",
                "question": "美联储宣布无限 QE，市场当天见底。你？",
                "options": [
                    {"id": "a", "text": "不相信「干预有用」，继续空仓", "result": "bad",
                     "feedback": "不要与央行作对。QE 是最强支撑信号。",
                     "historical_outcome": "错过 V 型反弹，标普 5 个月涨 50%。"},
                    {"id": "b", "text": "逐步加仓，跟随政策", "result": "good",
                     "feedback": "顺势而为。央行大动作后通常会有反弹。",
                     "historical_outcome": "3 月底加仓，收益巨大。"},
                    {"id": "c", "text": "全仓 All in", "result": "partial",
                     "feedback": "方向对但仓位过重。无法确认是底，分批更稳。",
                     "historical_outcome": "这次对了，但风险管理的角度分批更合理。"}],
            },
        ],
        "lessons": [
            "暴跌速度越快，反弹可能越快（V 型 vs L 型）",
            "不要与央行作对：大规模政策干预通常是转折信号",
            "熔断/恐慌日往往是情绪底，但需要基本面配合",
            "保留现金让你在暴跌中有抄底能力",
        ],
        "xp": 90,
    },
    {
        "id": "he03", "title": "2021 Meme 股狂潮",
        "subtitle": "GME 与散户 vs 华尔街",
        "start_date": "2021-01-01", "end_date": "2021-02-01",
        "severity": "moderate",
        "symbols": ["GME", "AMC"],
        "summary": "散户抱团爆炒 GME，股价从 20 美元飙到 480 美元，做空机构巨亏。",
        "key_dates": [
            {"date": "2021-01-11", "title": "散户开始抱团", "desc": "Reddit 论坛呼吁买入 GME"},
            {"date": "2021-01-25", "title": "GME 暴涨", "desc": "单日涨 18%，逼空开始"},
            {"date": "2021-01-28", "title": "GME 触及 480", "desc": "历史最高点"},
            {"date": "2021-02-02", "title": "GME 跌回 90", "desc": "一周跌 80%"},
        ],
        "decision_points": [
            {
                "date": "2021-01-20", "title": "GME 涨到 40",
                "question": "你看到 GME 一周翻倍，论坛里都是「起飞」。你？",
                "options": [
                    {"id": "a", "text": "立即买入，不能错过", "result": "bad",
                     "feedback": "FOMO。这是典型炒作，基本面不支持。",
                     "historical_outcome": "如果在 40 买入并在 480 卖，赚 11 倍。但谁能在 480 卖？多数人拿到 90。"},
                    {"id": "b", "text": "研究为什么涨，基本面如何", "result": "good",
                     "feedback": "理性。GME 基本面很差，上涨纯靠资金博弈。",
                     "historical_outcome": "研究后你会发现这是赌博，不参与。"},
                    {"id": "c", "text": "小仓位搏短线，设紧止损", "result": "partial",
                     "feedback": "如果一定要参与，小仓位+止损是唯一合理方式。",
                     "historical_outcome": "小仓位搏短线可能赚到，但风险极高。"}],
            },
            {
                "date": "2021-01-28", "title": "GME 触及 480",
                "question": "GME 到 480 美元，你持有 10 股（成本 40）。你？",
                "options": [
                    {"id": "a", "text": "全部卖出，落袋为安", "result": "good",
                     "feedback": "11 倍利润，完美的止盈。这种机会不会持续。",
                     "historical_outcome": "卖在最高点附近，赚 4400 美元。"},
                    {"id": "b", "text": "持有，目标 1000", "result": "bad",
                     "feedback": "贪婪。暴涨必然伴随暴跌，见好就收。",
                     "historical_outcome": "一周后跌到 90，利润回吐 80%。"},
                    {"id": "c", "text": "加仓，这是一生一次的机会", "result": "bad",
                     "feedback": "极度危险。追高加仓在顶部是毁灭性的。",
                     "historical_outcome": "加仓后亏损巨大。"}],
            },
            {
                "date": "2021-02-02", "title": "GME 跌回 90",
                "question": "GME 从 480 跌到 90。你？",
                "options": [
                    {"id": "a", "text": "抄底，还会涨回去", "result": "bad",
                     "feedback": "幻想。炒作退潮后不会再来。",
                     "historical_outcome": "GME 此后再未回到 480。"},
                    {"id": "b", "text": "庆幸没在高位买", "result": "good",
                     "feedback": "正确心态。不参与看不懂的行情是智慧。"},
                    {"id": "c", "text": "复盘整个过程，学习炒作股特征", "result": "good",
                     "feedback": "把别人的闹剧变成自己的教材。"}],
            },
        ],
        "lessons": [
            "炒作股的特征：基本面差、社交媒体驱动、暴涨暴跌",
            "不参与看不懂的行情，错过不可怕，追高才可怕",
            "如果一定要参与炒作，小仓位+紧止损+明确止盈",
            "11 倍利润时卖出是理性的，不要幻想 100 倍",
        ],
        "xp": 80,
    },
    {
        "id": "he04", "title": "2023 硅谷银行倒闭",
        "subtitle": "区域性银行危机",
        "start_date": "2023-03-08", "end_date": "2023-03-20",
        "severity": "moderate",
        "symbols": ["SIVB", "SPY"],
        "summary": "硅谷银行因存款挤兑+债券浮亏 48 小时倒闭，引发区域性银行恐慌。",
        "key_dates": [
            {"date": "2023-03-08", "title": "SVB 宣布增资", "desc": "市场担忧加剧"},
            {"date": "2023-03-10", "title": "SVB 被接管", "desc": "美国史上第二大银行倒闭"},
            {"date": "2023-03-13", "title": "签名银行倒闭", "desc": "恐慌蔓延"},
            {"date": "2023-03-17", "title": "大行救助", "desc": "11 家大行注资 First Republic"},
        ],
        "decision_points": [
            {
                "date": "2023-03-09", "title": "SVB 暴雷前夜",
                "question": "你持有区域性银行股。SVB 宣布增资引发担忧。你？",
                "options": [
                    {"id": "a", "text": "立即清仓所有银行股", "result": "partial",
                     "feedback": "谨慎。但大型银行与区域性银行风险不同。",
                     "historical_outcome": "大行受影响较小，清仓可能过度反应。"},
                    {"id": "b", "text": "检查持仓银行的存款结构和债券敞口", "result": "good",
                     "feedback": "理性分析。SVB 问题特定：存款集中+未对冲债券。",
                     "historical_outcome": "基本面健康的大行很快恢复。"},
                    {"id": "c", "text": "不以为然，银行股都安全", "result": "bad",
                     "feedback": "盲目乐观。不同银行风险差异巨大。",
                     "historical_outcome": "持有问题银行股会巨亏。"}],
            },
            {
                "date": "2023-03-13", "title": "签名银行倒闭",
                "question": "第二个银行倒闭，恐慌蔓延。你？",
                "options": [
                    {"id": "a", "text": "全部清仓，金融危机会重演", "result": "bad",
                     "feedback": "过度反应。2008 和 2023 的银行问题机制不同。",
                     "historical_outcome": "区域性银行危机未演变为系统性危机。"},
                    {"id": "b", "text": "区分系统性风险和局部风险", "result": "good",
                     "feedback": "理性。SVB 问题是特定的，不是系统性的。",
                     "historical_outcome": "大盘在 2 周后企稳反弹。"},
                    {"id": "c", "text": "抄底问题银行股", "result": "bad",
                     "feedback": "接飞刀。倒闭银行不要碰。",
                     "historical_outcome": "问题银行股继续下跌甚至退市。"}],
            },
        ],
        "lessons": [
            "区分系统性风险和局部风险：不是所有银行暴雷都是 2008",
            "检查持仓公司的基本面（存款结构、债券敞口）是危机中的第一要务",
            "恐慌蔓延时，优质资产往往被错杀，是机会",
            "不要在危机中做「全部」决策（全仓/清仓）",
        ],
        "xp": 70,
    },
]


def get_historical_event(event_id: str) -> dict | None:
    """获取历史事件（不含答案）"""
    e = next((e for e in HISTORICAL_EVENTS if e["id"] == event_id), None)
    if not e:
        return None
    safe = {
        "id": e["id"], "title": e["title"], "subtitle": e.get("subtitle", ""),
        "start_date": e["start_date"], "end_date": e["end_date"],
        "severity": e["severity"], "symbols": e["symbols"], "summary": e["summary"],
        "key_dates": e["key_dates"],
        "decision_points": [{
            "date": dp["date"], "title": dp["title"], "question": dp["question"],
            "options": [{"id": o["id"], "text": o["text"]} for o in dp["options"]],
        } for dp in e["decision_points"]],
    }
    return safe


def get_historical_event_full(event_id: str) -> dict | None:
    """获取完整历史事件（含答案）"""
    return next((e for e in HISTORICAL_EVENTS if e["id"] == event_id), None)


def list_historical_events() -> list[dict]:
    """列出所有历史事件"""
    return [{"id": e["id"], "title": e["title"], "subtitle": e.get("subtitle", ""),
             "severity": e["severity"], "xp": e["xp"],
             "start_date": e["start_date"], "end_date": e["end_date"]} for e in HISTORICAL_EVENTS]


def evaluate_historical_replay(event_id: str, decisions: list) -> dict:
    """评估历史事件回放决策"""
    e = get_historical_event_full(event_id)
    if not e:
        return {"error": "事件不存在"}

    result_map = {"good": 100, "partial": 50, "bad": 0}
    scores = []
    feedback = []
    for i, dp in enumerate(e["decision_points"]):
        if i >= len(decisions):
            break
        choice_id = decisions[i].get("choice", "")
        opt = next((o for o in dp["options"] if o["id"] == choice_id), None)
        if not opt:
            scores.append(0)
            continue
        scores.append(result_map.get(opt["result"], 0))
        feedback.append({
            "date": dp["date"], "title": dp["title"],
            "your_choice": opt["text"], "result": opt["result"],
            "feedback": opt["feedback"], "historical_outcome": opt.get("historical_outcome", ""),
        })

    score = int(sum(scores) / len(scores)) if scores else 0
    return {
        "event_id": event_id, "score": score,
        "passed": score >= 60,
        "feedback": feedback,
        "lessons": e.get("lessons", []),
        "xp_earned": e["xp"] if score >= 60 else 0,
    }


__all__ = [
    "HISTORICAL_EVENTS", "get_historical_event", "get_historical_event_full",
    "list_historical_events", "evaluate_historical_replay",
]
