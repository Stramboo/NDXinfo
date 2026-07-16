# -*- coding: utf-8 -*-
"""practice.py — Phase 4+5 练习+情景模块"""

def calc_position(account_size, stock_price, stop_loss_pct, max_loss_per_trade):
    if any(v <= 0 for v in [account_size, stock_price, stop_loss_pct, max_loss_per_trade]):
        return {"error": "所有参数必须大于 0"}
    if stop_loss_pct > 20:
        return {"warning": "止损比例过大（>20%），建议控制在 5-15% 之间"}
    stop_loss_price = stock_price * (1 - stop_loss_pct / 100)
    max_loss_per_share = stock_price - stop_loss_price
    if max_loss_per_share <= 0:
        return {"error": "止损价格不能高于买入价"}
    shares = int(max_loss_per_trade // max_loss_per_share)
    position_value = shares * stock_price
    position_pct = round(position_value / account_size * 100, 1)
    result = {"shares": shares, "stop_loss_price": round(stop_loss_price, 2),
              "max_loss_per_share": round(max_loss_per_share, 2),
              "position_value": round(position_value, 2), "position_pct": position_pct}
    if position_pct > 30:
        result["warning"] = f"仓位 {position_pct}% 偏高，建议控制单票 ≤ 20-30%"
    elif position_pct < 5:
        result["warning"] = f"仓位 {position_pct}% 偏低，可适当增加"
    return result


def calc_stop_loss(entry_price, shares, max_loss):
    if any(v <= 0 for v in [entry_price, shares, max_loss]):
        return {"error": "所有参数必须大于 0"}
    max_loss_per_share = max_loss / shares
    stop_price = entry_price - max_loss_per_share
    loss_pct = round(max_loss_per_share / entry_price * 100, 1)
    return {"stop_loss_price": round(stop_price, 2),
            "max_loss_per_share": round(max_loss_per_share, 2), "loss_pct": loss_pct}


SCENARIOS = [
    {
        "id": "sc01", "title": "财报前的抉择",
        "description": "你关注的科技公司明天发布财报。分析师普遍预期乐观，但最近一个月股价已经涨了 15%。你该怎么办？",
        "difficulty": "easy",
        "context": {"company": "一家 AI 芯片公司", "price": 200, "trend": "过去一月涨了 15%，接近历史新高", "sentiment": "市场情绪极度乐观"},
        "steps": [
            {"id": "step1", "question": "面对明天发布财报的公司，你的第一步是？",
             "options": [
                {"id": "a", "text": "立即全仓买入，赶在财报前", "result": "bad", "feedback": "追涨是新手最容易犯的错误。财报数据有不确定性，即使预期好也可能差。"},
                {"id": "b", "text": "先了解这家公司的基本面和估值", "result": "good", "feedback": "正确！在不确定的事件前，你应该先做功课，而不是冲动交易。"},
                {"id": "c", "text": "问别人怎么看，跟风操作", "result": "bad", "feedback": "投资决策应该基于自己的研究，不是别人的意见。"}]},
            {"id": "step2", "question": "你看完财报发现：营收超预期 +20%，但利润率下降了 3%。技术面看，股价在阻力位附近。怎么办？",
             "options": [
                {"id": "a", "text": "营收超预期，果断买入", "result": "partial", "feedback": "营收增长是好事，但利润率下降需要关注。不能只看一个指标。"},
                {"id": "b", "text": "写好交易计划，等它突破阻力位再分批买入", "result": "good", "feedback": "优秀的做法！你在等待确认信号，并且有分批建仓的计划。"},
                {"id": "c", "text": "放弃，不碰不熟悉的股票", "result": "partial", "feedback": "放弃也是一种合理选择。不熟不做，这是保护自己的好习惯。"}]},
            {"id": "step3", "question": "你买了 100 股，价格 $200。三天后股价跌到 $185（-7.5%）。你的止损设的是 -8%。你怎么办？",
             "options": [
                {"id": "a", "text": "把止损调到 -15%，再“等一等”", "result": "bad", "feedback": "这是亏损扩大的开始。随意修改止损计划，等于没有止损。"},
                {"id": "b", "text": "还没到止损位，按兵不动", "result": "good", "feedback": "正确的纪律！你的止损还没触发，不要因为恐慌而提前行动。"},
                {"id": "c", "text": "觉得亏了 7.5% 太多，立刻卖", "result": "partial", "feedback": "情绪化操作。你应该问自己：买入的理由还成立吗？而不是只看今天的涨跌。"}]}],
        "takeaway": "买之前做好三件事：研究基本面、写好交易计划、设好止损。买之后管住手，等市场验证你的判断。", "xp": 80},
    {
        "id": "sc02", "title": "追涨的陷阱",
        "description": "你看到一只股票连续三天大涨，朋友圈都在晒“赚翻了”。你是不是也心动了？",
        "difficulty": "easy",
        "context": {"company": "一家热门电动车公司", "price": 50, "trend": "连续三天涨停/大涨，成交量暴增", "sentiment": "社交媒体狂热度极高"},
        "steps": [
            {"id": "step1", "question": "看到一只股票连涨三天，你的第一反应是？",
             "options": [
                {"id": "a", "text": "赶紧买，再不买就晚了", "result": "bad", "feedback": "FOMO（害怕错过）是投资大敌。连涨三天的股票回调概率很高。"},
                {"id": "b", "text": "查一下为什么涨，有没有实质性利好", "result": "good", "feedback": "理性的第一步！搞清楚上涨的原因，判断是真实的利好还是短期的炒作。"},
                {"id": "c", "text": "截图发朋友圈，然后分一小部分仓位试探", "result": "partial", "feedback": "小仓位试探可以，但不要因为赚了快钱就头脑发热全仓杀入。"}]},
            {"id": "step2", "question": "调查发现：上涨是因为有人在 Twitter 上发了一张跟 CEO 的合影。不是任何实质性利好。你怎么办？",
             "options": [
                {"id": "a", "text": "这不靠谱，完全不理", "result": "good", "feedback": "明智的选择。没有基本面支撑的上涨，大概率从哪里来回哪里去。"},
                {"id": "b", "text": "买一小笔，设紧止损搏短线", "result": "partial", "feedback": "勉强可以，但你要清楚这是在赌博，不是投资。"},
                {"id": "c", "text": "既然市场相信这个故事，全仓买入", "result": "bad", "feedback": "你在赌别人更傻。即使短期可能赚到，长期这个策略一定会让你亏大钱。"}]},
            {"id": "step3", "question": "三天后股价跌了 12%，跌回了涨前的价格。那些追高的人怎么办？",
             "options": [
                {"id": "a", "text": "补仓“摊低成本”", "result": "bad", "feedback": "下跌中补仓非常危险。如果你的买入理由本来就不成立，补仓只是把错误放大。"},
                {"id": "b", "text": "认错卖出，总结经验", "result": "good", "feedback": "高手和韭菜的区别：高手敢于认错。承认自己判断失误，记录教训，下次不犯。"},
                {"id": "c", "text": "删掉 App，眼不见心不烦", "result": "partial", "feedback": "逃避解决不了问题。投资需要面对亏损、反思原因，才能成长。"}]}],
        "takeaway": "不要因为别人的兴奋就跟着冲锋。搞清楚涨的理由，区分投资和赌博。小亏认错保平安，硬扛只能越亏越多。", "xp": 80},
    {
        "id": "sc03", "title": "暴跌中的冷静",
        "description": "大盘突然跌了 5%，你的持仓一片红。恐慌情绪蔓延，新闻标题全是“熊市来了”。你该如何应对？",
        "difficulty": "medium",
        "context": {"company": "你的持仓组合（2 只科技股 + 1 只指数 ETF）", "price": "下跌 5-8%", "trend": "大盘整体回调 5%，恐慌指数 VIX 飙升", "sentiment": "市场极度恐慌，新闻全是利空"},
        "steps": [
            {"id": "step1", "question": "大盘暴跌 5%，你的持仓平均跌了 7%。你首先应该？",
             "options": [
                {"id": "a", "text": "全部清仓，保住剩下的本金", "result": "bad", "feedback": "恐慌性清仓往往卖在最低点。大盘 5% 的回调在历史上是很常见的现象。"},
                {"id": "b", "text": "检查每只股票的止损位，确认没有被触发", "result": "good", "feedback": "正确的做法！先看止损是否触发、仓位是否超标，不要情绪化决策。"},
                {"id": "c", "text": "全仓买入，“抄底”", "result": "bad", "feedback": "暴跌中抄底跟赌博没区别。你不知道这是回调的开始还是结束。"}]},
            {"id": "step2", "question": "你检查后发现：所有持仓的买入理由依然成立，只是大盘整体下跌带动了它们。你怎么办？",
             "options": [
                {"id": "a", "text": "按兵不动，等市场情绪恢复", "result": "good", "feedback": "如果你的判断是对的，市场情绪最终会恢复正常。耐心是投资者最重要的品质之一。"},
                {"id": "b", "text": "趁低分批加仓看好的股票", "result": "good", "feedback": "这也是合理的策略。但注意：要按计划分批加，不要一把梭。"},
                {"id": "c", "text": "虽然理由成立，但跌得“太难受了”，卖一半", "result": "partial", "feedback": "你让情绪战胜了理性。投资中损失厌恶是人之常情，但你需要信任自己的研究。"}]},
            {"id": "step3", "question": "一周后市场反弹，你的持仓回到了买入价以上。回顾这次经历，你学到了什么？",
             "options": [
                {"id": "a", "text": "以后每次暴跌都应该抄底，稳赚", "result": "bad", "feedback": "这次只是运气好。不是每次暴跌都会快速反弹。2008 年跌了一年多才见底。"},
                {"id": "b", "text": "制定应对暴跌的方案：什么情况卖、什么情况加仓、什么情况不动", "result": "good", "feedback": "最佳的学习成果！把经验转化为规则，下次恐慌来临时你就能从容应对。"},
                {"id": "c", "text": "再也不碰股票了，太吓人", "result": "partial", "feedback": "恐惧是正常的。但如果你理解了这次经历，你会发现市场波动是常态，控制仓位和情绪才是关键。"}]}],
        "takeaway": "暴跌是市场的常态，不是灾难。关键在于：你有止损吗？你买入的理由还成立吗？你的仓位控制合理吗？提前想好这三个问题的答案。", "xp": 100},
    {
        "id": "sc04", "title": "止盈的智慧",
        "description": "你买入的股票涨了 30%，朋友都说“还能涨”。你该卖吗？",
        "difficulty": "medium",
        "context": {"company": "一只你研究了 3 个月才买入的消费股", "price": "买入价 $100，现价 $130（+30%）", "trend": "上升趋势完好，但涨幅已经比较大", "sentiment": "分析师普遍看好，上调目标价至 $150"},
        "steps": [
            {"id": "step1", "question": "你的股票从 $100 涨到 $130。买入时你没设止盈位。现在该不该卖？",
             "options": [
                {"id": "a", "text": "都涨 30% 了必须落袋为安，全卖", "result": "partial", "feedback": "落袋为安是合理的。但涨了 x% 就卖不是最理性的理由。应该看公司本身。"},
                {"id": "b", "text": "先卖一半锁定利润，剩下一半设跟踪止损", "result": "good", "feedback": "聪明的策略！既锁定了部分利润，又保留了继续上涨的参与机会。"},
                {"id": "c", "text": "分析师说还能涨到 $150，坚决不卖", "result": "bad", "feedback": "分析师不是神仙。他们的预测经常不准。靠别人的预测做决定，是最危险的操作方式。"}]},
            {"id": "step2", "question": "你卖了 50%，保留了 50%。一周后股价跌到 $115。你后悔卖少了吗？",
             "options": [
                {"id": "a", "text": "非常后悔，应该在 $130 全卖", "result": "partial", "feedback": "事后诸葛亮容易。投资中没有完美操作，你做出了当时最合理的决策就好。"},
                {"id": "b", "text": "不后悔，$130 卖一半是当时的好决定", "result": "good", "feedback": "正确的复盘心态！你做了在当时情况下最理性的决策，这就够了。"},
                {"id": "c", "text": "$115 了赶紧把剩下的一半也卖了", "result": "partial", "feedback": "从 $130 跌到 $115 相当于跌了 11.5%。如果这已经触发你的止损或止盈条件（比如从高点回撤 10%），再卖是纪律，不是恐慌。"}]}],
        "takeaway": "止盈是一门艺术，没有完美答案。批量锁利+跟踪止损是职业交易者常用的策略。记住：赚到口袋里的才算利润，浮盈只是数字。", "xp": 90},
]


def evaluate_scenario_decisions(decisions):
    if not decisions:
        return {"score": 0, "level": "未完成", "feedback": ["请完成所有决策步骤"]}
    result_map = {"good": 100, "partial": 50, "bad": 0}
    scores = []
    feedback_items = []
    for d in decisions:
        step_result = d.get("result", "bad")
        scores.append(result_map.get(step_result, 0))
        if step_result == "bad":
            feedback_items.append(f"第 {d.get('step', '?')} 步可以做得更好")
    avg_score = sum(scores) / len(scores) if scores else 0
    if avg_score >= 80:
        level = "优秀决策者"
    elif avg_score >= 50:
        level = "正在学习"
    else:
        level = "需要练习"
    return {"score": round(avg_score), "level": level, "total_steps": len(scores),
            "good_decisions": scores.count(100), "partial_decisions": scores.count(50),
            "bad_decisions": scores.count(0),
            "feedback": feedback_items if feedback_items else ["做得很好！"]}

__all__ = ["calc_position", "calc_stop_loss", "SCENARIOS", "evaluate_scenario_decisions"]
