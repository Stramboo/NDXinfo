# -*- coding: utf-8 -*-
"""
scenario_questions.py — 情景判断题库 (v2.5 Phase 1a)

扩展题型：multi（多选）/ sort（排序）/ match（匹配）/ branching（分支）
每题含 knowledge_point（知识点标签）+ difficulty（难度 1-3）
"""

# 知识点图谱：60 个知识点节点（按阶段分组）
KNOWLEDGE_POINTS = {
    # 阶段 1：股票基础
    "stock_ownership": {"name": "股票所有权", "stage": 1, "chapter": "ch01"},
    "ipo_reason": {"name": "上市目的", "stage": 1, "chapter": "ch01"},
    "price_driver": {"name": "股价驱动因素", "stage": 1, "chapter": "ch02"},
    "long_term_value": {"name": "长期价值", "stage": 1, "chapter": "ch02"},
    "retail_vs_inst": {"name": "散户vs机构", "stage": 1, "chapter": "ch03"},
    "retail_advantage": {"name": "散户优势", "stage": 1, "chapter": "ch03"},
    "floating_pnl": {"name": "浮动盈亏", "stage": 1, "chapter": "ch04"},
    "market_diff": {"name": "市场差异", "stage": 1, "chapter": "ch04"},
    # 阶段 2：全球市场
    "nyse_nasdaq": {"name": "纽交所/纳斯达克", "stage": 2, "chapter": "ch05"},
    "us_trading_hours": {"name": "美股交易时段", "stage": 2, "chapter": "ch05"},
    "a_share_limit": {"name": "A股涨跌幅", "stage": 2, "chapter": "ch06"},
    "stock_connect": {"name": "港股通", "stage": 2, "chapter": "ch06"},
    "global_index": {"name": "全球指数", "stage": 2, "chapter": "ch07"},
    "diversification": {"name": "全球分散", "stage": 2, "chapter": "ch07"},
    "exchange_role": {"name": "交易所功能", "stage": 2, "chapter": "ch08"},
    "liquidity": {"name": "流动性", "stage": 2, "chapter": "ch08"},
    # 阶段 3：认识公司
    "business_model": {"name": "商业模式", "stage": 3, "chapter": "ch09"},
    "moat": {"name": "护城河", "stage": 3, "chapter": "ch09"},
    "pe_ratio": {"name": "市盈率", "stage": 3, "chapter": "ch10"},
    "valuation_compare": {"name": "估值比较", "stage": 3, "chapter": "ch10"},
    "revenue": {"name": "营收", "stage": 3, "chapter": "ch11"},
    "profit_margin": {"name": "利润率", "stage": 3, "chapter": "ch11"},
    "gross_margin": {"name": "毛利率", "stage": 3, "chapter": "ch12"},
    "free_cash_flow": {"name": "自由现金流", "stage": 3, "chapter": "ch12"},
    # 阶段 4：股价图表
    "kline_basic": {"name": "K线基础", "stage": 4, "chapter": "ch13"},
    "volume_price": {"name": "量价关系", "stage": 4, "chapter": "ch13"},
    "moving_average": {"name": "移动平均线", "stage": 4, "chapter": "ch14"},
    "golden_cross": {"name": "金叉", "stage": 4, "chapter": "ch14"},
    "ta_limitation": {"name": "技术分析局限", "stage": 4, "chapter": "ch15"},
    "support_resistance": {"name": "支撑阻力", "stage": 4, "chapter": "ch16"},
    "breakout": {"name": "突破", "stage": 4, "chapter": "ch16"},
    # 阶段 5：风险意识
    "position_sizing": {"name": "仓位管理", "stage": 5, "chapter": "ch19"},
    "stop_loss": {"name": "止损", "stage": 5, "chapter": "ch18"},
    "discipline": {"name": "交易纪律", "stage": 5, "chapter": "ch18"},
    "sunk_cost": {"name": "沉没成本", "stage": 5, "chapter": "ch20"},
    "fomo": {"name": "FOMO", "stage": 5, "chapter": "ch20"},
    "diversify_position": {"name": "分散持仓", "stage": 5, "chapter": "ch17"},
    "leverage_risk": {"name": "杠杆风险", "stage": 5, "chapter": "ch17"},
    # 阶段 6：模拟与复盘
    "sim_vs_real": {"name": "模拟vs实盘", "stage": 6, "chapter": "ch21"},
    "trade_journal": {"name": "交易日志", "stage": 6, "chapter": "ch22"},
    "review_method": {"name": "复盘方法", "stage": 6, "chapter": "ch22"},
    "good_trade": {"name": "好交易标准", "stage": 6, "chapter": "ch23"},
    "cut_loss_run_profit": {"name": "截断亏损", "stage": 6, "chapter": "ch23"},
    "trade_plan": {"name": "交易计划", "stage": 6, "chapter": "ch24"},
}


# 情景判断题库（每课 1 道情景题，扩展题型）
SCENARIO_QUESTIONS = [
    # ---- 阶段 1 ----
    {
        "id": "sq_ch01", "chapter": "ch01", "type": "multi", "difficulty": 1,
        "knowledge_point": "stock_ownership",
        "question": "小明花 10 万元买了某公司 1000 股股票。以下哪些说法是正确的？（多选）",
        "options": [
            "小明成为该公司的部分所有者",
            "小明有权参加股东大会投票",
            "小明保证每年都能拿到固定分红",
            "如果公司破产，小明可能血本无归",
            "小明可以随时要求公司回购股票",
        ],
        "correct": [0, 1, 3],
        "explanation": "股票代表公司所有权，股东有投票权，但分红不固定、公司不承诺回购，破产时股东受偿顺序最后。",
    },
    {
        "id": "sq_ch02", "chapter": "ch02", "type": "sort", "difficulty": 2,
        "knowledge_point": "price_driver",
        "question": "以下因素对股价的影响，按「短期影响程度」从大到小排序：",
        "options": [
            "公司季度财报暴雷（利润腰斩）",
            "美联储宣布加息 0.5%",
            "CEO 在 Twitter 发了一张度假照片",
            "行业政策重大利好",
        ],
        "correct": [0, 3, 1, 2],
        "explanation": "短期冲击：财报暴雷 > 行业政策 > 加息 > CEO度假照。但长期看，公司盈利能力才是决定性因素。",
    },
    {
        "id": "sq_ch03", "chapter": "ch03", "type": "multi", "difficulty": 2,
        "knowledge_point": "retail_advantage",
        "question": "作为散户，以下哪些是你的真实优势？（多选）",
        "options": [
            "信息比机构更快",
            "没有业绩考核压力，可以长期持有",
            "资金量小，可以买小盘股",
            "可以空仓等待机会，不必满仓",
            "交易手续费更低",
        ],
        "correct": [1, 3],
        "explanation": "散户的优势在于：无考核压力可长期持有，可空仓等待。信息、费率都是机构更优。",
    },
    {
        "id": "sq_ch04", "chapter": "ch04", "type": "branching", "difficulty": 2,
        "knowledge_point": "floating_pnl",
        "question": "你买入一只股票浮盈 20%，突然传来利空消息，股价开始下跌。你的第一步是？",
        "options": [
            {"id": "a", "text": "立即全部卖出锁定利润", "next": "q1a"},
            {"id": "b", "text": "评估利空对买入理由的影响", "next": "q1b"},
            {"id": "c", "text": "加仓摊低成本", "next": "q1c"},
        ],
        "sub_questions": {
            "q1a": {"question": "全部卖出后股价反弹了 10%，你的感受？",
                    "options": [{"id": "x", "text": "后悔卖早了", "result": "partial"},
                                {"id": "y", "text": "不后悔，纪律执行了", "result": "good"}]},
            "q1b": {"question": "评估发现利空不影响长期逻辑，但短期有压力。你？",
                    "options": [{"id": "x", "text": "卖一半锁利，剩一半设跟踪止损", "result": "good"},
                                {"id": "y", "text": "全部卖出观望", "result": "partial"}]},
            "q1c": {"question": "加仓后股价继续下跌 15%，你？",
                    "options": [{"id": "x", "text": "再次加仓", "result": "bad"},
                                {"id": "y", "text": "按原止损计划执行", "result": "good"}]},
        },
        "explanation": "浮盈不是真利润。面对利空，先评估影响再决策；锁利+跟踪止损是成熟做法；下跌加仓是危险行为。",
    },
    # ---- 阶段 2 ----
    {
        "id": "sq_ch05", "chapter": "ch05", "type": "match", "difficulty": 1,
        "knowledge_point": "nyse_nasdaq",
        "question": "将交易所与其特点匹配：",
        "match_pairs": [
            {"left": "纽交所 NYSE", "right": "历史悠久，传统行业巨头多"},
            {"left": "纳斯达克 NASDAQ", "right": "科技公司聚集地"},
            {"left": "A 股上交所", "right": "人民币计价，主板±10%涨跌停"},
            {"left": "港交所 HKEX", "right": "港股通可投，无涨跌幅限制"},
        ],
        "correct": [0, 1, 2, 3],
        "explanation": "纽交所传统、纳斯达克科技、A股有涨跌停、港股通互联互通——各市场特点鲜明。",
    },
    {
        "id": "sq_ch06", "chapter": "ch06", "type": "multi", "difficulty": 2,
        "knowledge_point": "a_share_limit",
        "question": "关于 A 股涨跌幅限制，以下哪些说法正确？（多选）",
        "options": [
            "主板单日涨跌幅 ±10%",
            "科创板/创业板 ±20%",
            "ST 股票 ±5%",
            "新股上市首日有特殊规定",
            "所有股票都无涨跌幅限制",
        ],
        "correct": [0, 1, 2, 3],
        "explanation": "A 股主板±10%、科创/创业±20%、ST±5%，新股首日特殊。这是 A 股与美股的重要差异。",
    },
    {
        "id": "sq_ch07", "chapter": "ch07", "type": "sort", "difficulty": 2,
        "knowledge_point": "global_index",
        "question": "以下指数按「对应市场市值规模」从大到小排序：",
        "options": ["标普 500（美国）", "日经 225（日本）", "富时 100（英国）", "上证综指（中国）"],
        "correct": [0, 3, 1, 2],
        "explanation": "美股市值全球最大，中国 A 股次之，日本再次，英国较小。指数规模反映市场体量。",
    },
    {
        "id": "sq_ch08", "chapter": "ch08", "type": "multi", "difficulty": 2,
        "knowledge_point": "liquidity",
        "question": "以下哪些是「流动性好」的特征？（多选）",
        "options": [
            "买卖价差小",
            "大额交易不会大幅影响价格",
            "成交速度快",
            "股价天天涨",
            "每天都有大量成交",
        ],
        "correct": [0, 1, 2, 4],
        "explanation": "流动性=快速成交+小额价格冲击。价差小、深度深、成交活跃是好流动性的标志。股价涨跌与流动性无关。",
    },
    # ---- 阶段 3 ----
    {
        "id": "sq_ch09", "chapter": "ch09", "type": "multi", "difficulty": 2,
        "knowledge_point": "moat",
        "question": "以下哪些可以构成公司的「护城河」？（多选）",
        "options": [
            "强大的品牌（如苹果、可口可乐）",
            "网络效应（如微信、淘宝）",
            "成本优势（如规模制造业）",
            "转换成本高（如企业级软件）",
            "今年赚了很多钱",
        ],
        "correct": [0, 1, 2, 3],
        "explanation": "护城河是持久的竞争优势：品牌、网络效应、成本、转换成本。今年赚钱是结果不是护城河。",
    },
    {
        "id": "sq_ch10", "chapter": "ch10", "type": "branching", "difficulty": 3,
        "knowledge_point": "pe_ratio",
        "question": "你看到 A 公司 PE=50，B 公司 PE=15，同行业。你的判断是？",
        "options": [
            {"id": "a", "text": "A 一定被高估，B 一定被低估", "next": "q10a"},
            {"id": "b", "text": "需要看增长率才能判断", "next": "q10b"},
            {"id": "c", "text": "PE 没用，看市值就行", "next": "q10c"},
        ],
        "sub_questions": {
            "q10a": {"question": "如果 A 公司利润年增 50%，B 公司利润零增长呢？",
                     "options": [{"id": "x", "text": "A 可能并不贵（PEG<1）", "result": "good"},
                                 {"id": "y", "text": "还是 A 贵，PE 50 太高", "result": "partial"}]},
            "q10b": {"question": "引入 PEG（PE/增长率）后，A 的 PEG=1，B 的 PEG 无限大。结论？",
                     "options": [{"id": "x", "text": "A 实际上比 B 更有性价比", "result": "good"},
                                 {"id": "y", "text": "还是不能确定", "result": "partial"}]},
            "q10c": {"question": "市值=股价×股本。市值大说明？",
                     "options": [{"id": "x", "text": "公司规模大，但与估值无关", "result": "good"},
                                 {"id": "y", "text": "市值大=贵", "result": "bad"}]},
        },
        "explanation": "PE 不能孤立看。高 PE 可能反映高增长预期（用 PEG 判断），低 PE 可能是价值陷阱。同行业+增长率一起看。",
    },
    {
        "id": "sq_ch11", "chapter": "ch11", "type": "multi", "difficulty": 2,
        "knowledge_point": "revenue",
        "question": "一家公司营收增长 30%，但净利润下降 10%。可能的原因？（多选）",
        "options": [
            "原材料成本大幅上升",
            "打价格战抢占市场",
            "研发投入大幅增加",
            "管理层贪污",
            "并购产生一次性费用",
        ],
        "correct": [0, 1, 2, 4],
        "explanation": "增收不增利的原因：成本上升、价格战、战略性投入、一次性费用。需要区分「暂时性」和「结构性」。",
    },
    {
        "id": "sq_ch12", "chapter": "ch12", "type": "sort", "difficulty": 3,
        "knowledge_point": "free_cash_flow",
        "question": "以下指标按「反映公司真实赚钱能力」的可靠程度从高到低排序：",
        "options": ["自由现金流", "经营性现金流", "净利润", "营收"],
        "correct": [0, 1, 2, 3],
        "explanation": "自由现金流最难造假（真金白银），净利润有会计调整空间，营收最易虚增。巴菲特最看重 FCF。",
    },
    # ---- 阶段 4 ----
    {
        "id": "sq_ch13", "chapter": "ch13", "type": "multi", "difficulty": 1,
        "knowledge_point": "kline_basic",
        "question": "一根红色（实心）K 线表示？（多选，A股配色）",
        "options": [
            "收盘价低于开盘价",
            "收盘价高于开盘价",
            "当天股价下跌",
            "当天股价上涨",
            "实体部分=开盘价到收盘价",
        ],
        "correct": [0, 2, 4],
        "explanation": "A 股配色：红跌绿涨（与国际相反）。红色实心=收盘<开盘=下跌。实体长度反映波动幅度。",
    },
    {
        "id": "sq_ch14", "chapter": "ch14", "type": "branching", "difficulty": 2,
        "knowledge_point": "golden_cross",
        "question": "你看到 5 日均线上穿 20 日均线（金叉），股价站上均线。你？",
        "options": [
            {"id": "a", "text": "立即全仓买入", "next": "q14a"},
            {"id": "b", "text": "结合成交量和其他信号确认", "next": "q14b"},
            {"id": "c", "text": "金叉都是骗线，不买", "next": "q14c"},
        ],
        "sub_questions": {
            "q14a": {"question": "买入后股价立即跌破均线，你？",
                     "options": [{"id": "x", "text": "加仓摊低", "result": "bad"},
                                 {"id": "y", "text": "按预设止损执行", "result": "good"}]},
            "q14b": {"question": "成交量放大配合金叉，这是？",
                     "options": [{"id": "x", "text": "较可靠的买入信号", "result": "good"},
                                 {"id": "y", "text": "无所谓", "result": "partial"}]},
            "q14c": {"question": "完全不看技术分析，只看基本面，可以吗？",
                     "options": [{"id": "x", "text": "可以，但择时可能差", "result": "good"},
                                 {"id": "y", "text": "不行，必须看技术", "result": "partial"}]},
        },
        "explanation": "金叉是参考信号不是买卖指令。需结合成交量确认，并设好止损。技术分析是辅助工具。",
    },
    {
        "id": "sq_ch15", "chapter": "ch15", "type": "multi", "difficulty": 2,
        "knowledge_point": "ta_limitation",
        "question": "技术分析的局限包括？（多选）",
        "options": [
            "无法预测突发事件（财报暴雷、政策变化）",
            "历史模式不一定会重复",
            "存在滞后性（信号出现时行情已走一段）",
            "完全没用，是伪科学",
            "不同人对同一图形有不同解读",
        ],
        "correct": [0, 1, 2, 4],
        "explanation": "技术分析有局限：不能预测事件、有滞后、主观性强。但它是辅助择时工具，不是伪科学也不是万能。",
    },
    {
        "id": "sq_ch16", "chapter": "ch16", "type": "sort", "difficulty": 2,
        "knowledge_point": "support_resistance",
        "question": "以下价位对股价的「支撑/阻力强度」从强到弱排序：",
        "options": [
            "多次测试未破的历史低点",
            "前期高点（一次测试）",
            "整数关口（如 $100）",
            "50 日均线",
        ],
        "correct": [0, 3, 1, 2],
        "explanation": "支撑强度：多次测试的历史位 > 均线 > 前期高点 > 整数关口。测试次数越多，支撑/阻力越强。",
    },
    # ---- 阶段 5 ----
    {
        "id": "sq_ch17", "chapter": "ch17", "type": "multi", "difficulty": 2,
        "knowledge_point": "diversify_position",
        "question": "关于分散投资，以下哪些说法正确？（多选）",
        "options": [
            "持有 5-10 只不同行业的股票比较合理",
            "持有 50 只股票才能算分散",
            "分散可以降低非系统性风险",
            "分散能消除所有风险",
            "全部买同一行业的龙头也算分散",
        ],
        "correct": [0, 2],
        "explanation": "5-10 只跨行业股票即可分散非系统性风险。太多难管理，同行业不算分散，系统性风险无法靠分散消除。",
    },
    {
        "id": "sq_ch18", "chapter": "ch18", "type": "branching", "difficulty": 2,
        "knowledge_point": "stop_loss",
        "question": "你设了 -8% 止损，股价跌到 -7.5% 时反弹了一点。你？",
        "options": [
            {"id": "a", "text": "把止损调到 -12%，给它更多空间", "next": "q18a"},
            {"id": "b", "text": "维持原止损不变", "next": "q18b"},
            {"id": "c", "text": "立即手动卖出", "next": "q18c"},
        ],
        "sub_questions": {
            "q18a": {"question": "调宽止损后股价继续跌到 -12%，你？",
                     "options": [{"id": "x", "text": "再调宽到 -20%", "result": "bad"},
                                 {"id": "y", "text": "这次按 -12% 执行，下不为例", "result": "partial"}]},
            "q18b": {"question": "维持原止损，最终触发 -8% 卖出。这是？",
                     "options": [{"id": "x", "text": "纪律执行的胜利", "result": "good"},
                                 {"id": "y", "text": "亏了 8%，失败", "result": "partial"}]},
            "q18c": {"question": "提前卖出后股价继续大跌，你？",
                     "options": [{"id": "x", "text": "庆幸逃过一劫", "result": "good"},
                                 {"id": "y", "text": "后悔没等到反弹", "result": "partial"}]},
        },
        "explanation": "止损是纪律不是艺术。随意调宽=没有止损。按计划执行就是胜利，即使亏钱也是正确行为。",
    },
    {
        "id": "sq_ch19", "chapter": "ch19", "type": "sort", "difficulty": 3,
        "knowledge_point": "position_sizing",
        "question": "你有 10 万本金，单笔最大亏损设 2%（2000 元）。以下止损距离对应的买入金额从大到小排序：",
        "options": [
            "止损 -2%（买入 10 万）",
            "止损 -5%（买入 4 万）",
            "止损 -10%（买入 2 万）",
            "止损 -20%（买入 1 万）",
        ],
        "correct": [0, 1, 2, 3],
        "explanation": "仓位=可亏金额÷止损百分比。止损越宽，仓位越小。固定 2% 规则让你在任何单笔交易中最多亏 2000 元。",
    },
    {
        "id": "sq_ch20", "chapter": "ch20", "type": "multi", "difficulty": 2,
        "knowledge_point": "fomo",
        "question": "以下哪些是 FOMO（害怕错过）的表现？（多选）",
        "options": [
            "看到别人赚钱就焦虑",
            "追高买入已经大涨的股票",
            "不顾自己的计划临时决策",
            "空仓时觉得自己在亏钱",
            "坚持只买自己研究的股票",
        ],
        "correct": [0, 1, 2, 3],
        "explanation": "FOMO 表现为：焦虑、追高、临时决策、空仓焦虑。坚持计划和研究是抗 FOMO 的良药。",
    },
    # ---- 阶段 6 ----
    {
        "id": "sq_ch21", "chapter": "ch21", "type": "multi", "difficulty": 2,
        "knowledge_point": "sim_vs_real",
        "question": "模拟交易与实盘交易的区别包括？（多选）",
        "options": [
            "实盘有真实心理压力",
            "模拟盘成交总是很顺利",
            "实盘手续费和滑点真实存在",
            "模拟盘可以练习完整流程",
            "模拟盘赚钱=实盘也能赚钱",
        ],
        "correct": [0, 1, 2, 3],
        "explanation": "模拟与实盘最大区别是心理压力。模拟盘成交顺利、无真实费用，但能练流程。模拟赚钱不代表实盘能赚。",
    },
    {
        "id": "sq_ch22", "chapter": "ch22", "type": "sort", "difficulty": 2,
        "knowledge_point": "trade_journal",
        "question": "交易日志应该记录的内容，按重要性从高到低排序：",
        "options": [
            "买入理由和交易计划",
            "执行情况（是否按计划）",
            "事后反思和教训",
            "买入价格和数量",
        ],
        "correct": [0, 1, 2, 3],
        "explanation": "价格数量只是数据，理由和计划才是决策核心，反思是成长关键。日志的价值在于复盘改进。",
    },
    {
        "id": "sq_ch23", "chapter": "ch23", "type": "multi", "difficulty": 2,
        "knowledge_point": "good_trade",
        "question": "以下哪些是「好交易」的标准？（多选）",
        "options": [
            "按计划执行了",
            "赚钱了",
            "风险可控（设了止损）",
            "买入理由清晰且成立",
            "买了就涨",
        ],
        "correct": [0, 2, 3],
        "explanation": "好交易=按计划执行+风险可控+理由清晰。单次盈亏有运气成分，纪律才是长期保障。买了就涨是运气不是标准。",
    },
    {
        "id": "sq_ch24", "chapter": "ch24", "type": "branching", "difficulty": 3,
        "knowledge_point": "trade_plan",
        "question": "你要买入一只股票，先写交易计划。计划应包含？",
        "options": [
            {"id": "a", "text": "买入理由+仓位+止损+目标价+期限", "next": "q24a"},
            {"id": "b", "text": "只写买入价和目标价", "next": "q24b"},
            {"id": "c", "text": "不用写计划，看感觉", "next": "q24c"},
        ],
        "sub_questions": {
            "q24a": {"question": "五要素齐全。买入后理由不成立了，你？",
                     "options": [{"id": "x", "text": "认错卖出，理由没了就走", "result": "good"},
                                 {"id": "y", "text": "等回本再卖", "result": "bad"}]},
            "q24b": {"question": "只写了价格。跌了 10% 你不知道该不该卖，因为？",
                     "options": [{"id": "x", "text": "没设止损，无据可依", "result": "good"},
                                 {"id": "y", "text": "10% 不多，再等等", "result": "partial"}]},
            "q24c": {"question": "凭感觉交易长期结果通常是？",
                     "options": [{"id": "x", "text": "亏损，情绪化决策不可持续", "result": "good"},
                                 {"id": "y", "text": "看运气", "result": "bad"}]},
        },
        "explanation": "完整交易计划五要素：理由、仓位、止损、目标、期限。计划是冷静时的决策，执行时不受情绪干扰。",
    },
]


def get_scenario_question(question_id: str) -> dict | None:
    """获取情景题（不含答案）"""
    q = next((q for q in SCENARIO_QUESTIONS if q["id"] == question_id), None)
    if not q:
        return None
    # 移除答案字段
    safe = {k: v for k, v in q.items() if k not in ("correct", "explanation")}
    return safe


def get_chapter_scenario_question(chapter_id: str) -> dict | None:
    """获取某课的情景题（不含答案）"""
    q = next((q for q in SCENARIO_QUESTIONS if q["chapter"] == chapter_id), None)
    if not q:
        return None
    safe = {k: v for k, v in q.items() if k not in ("correct", "explanation")}
    return safe


def grade_scenario_question(question_id: str, answer: dict) -> dict:
    """
    批改情景题

    参数:
        question_id: 题目 ID
        answer: 答案 {type: multi/sort/match/branching, ...}
                multi: {indices: [0,1,3]}
                sort: {order: [0,3,1,2]}
                match: {pairs: [0,1,2,3]}
                branching: {choices: ["a","x"], results: ["good"]}
    """
    q = next((q for q in SCENARIO_QUESTIONS if q["id"] == question_id), None)
    if not q:
        return {"error": "题目不存在"}

    qtype = q["type"]
    correct = q.get("correct", [])  # branching 题没有 correct 字段
    is_correct = False
    score = 0

    if qtype == "multi":
        user_indices = set(answer.get("indices", []))
        correct_set = set(correct)
        if user_indices == correct_set:
            is_correct = True
            score = 100
        else:
            # 部分正确：正确选中的 - 错误选中的
            right = len(user_indices & correct_set)
            wrong = len(user_indices - correct_set)
            score = max(0, int((right - wrong) / len(correct_set) * 100))

    elif qtype == "sort":
        user_order = answer.get("order", [])
        if user_order == correct:
            is_correct = True
            score = 100
        else:
            # 计算正确位置数
            right_pos = sum(1 for i, v in enumerate(user_order) if i < len(correct) and v == correct[i])
            score = int(right_pos / len(correct) * 100)

    elif qtype == "match":
        user_pairs = answer.get("pairs", [])
        if user_pairs == correct:
            is_correct = True
            score = 100
        else:
            right = sum(1 for i, v in enumerate(user_pairs) if i < len(correct) and v == correct[i])
            score = int(right / len(correct) * 100)

    elif qtype == "branching":
        results = answer.get("results", [])
        if not results:
            return {"error": "分支题未完成"}
        result_map = {"good": 100, "partial": 50, "bad": 0}
        scores = [result_map.get(r, 0) for r in results]
        score = int(sum(scores) / len(scores)) if scores else 0
        is_correct = score >= 75

    passed = score >= 60
    # branching 题没有 correct 数组，用 results 评估
    correct_answer = correct if qtype != "branching" else answer.get("results", [])
    return {
        "score": score,
        "passed": passed,
        "is_correct": is_correct,
        "correct_answer": correct_answer,
        "explanation": q["explanation"],
        "knowledge_point": q["knowledge_point"],
        "chapter": q["chapter"],
    }


def get_knowledge_map() -> dict:
    """获取知识点图谱（节点+掌握度占位）"""
    nodes = []
    for kid, info in KNOWLEDGE_POINTS.items():
        nodes.append({
            "id": kid,
            "name": info["name"],
            "stage": info["stage"],
            "chapter": info["chapter"],
        })
    return {"nodes": nodes, "total": len(nodes)}


__all__ = [
    "KNOWLEDGE_POINTS", "SCENARIO_QUESTIONS",
    "get_scenario_question", "get_chapter_scenario_question",
    "grade_scenario_question", "get_knowledge_map",
]
