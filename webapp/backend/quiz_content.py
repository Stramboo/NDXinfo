# -*- coding: utf-8 -*-
"""
quiz_content.py — 课时测验 + 阶段考试内容 (v2.4 Phase 5)

结构:
  - LESSON_QUIZZES: 每课 3 题测验（24 课 × 3 题）
  - STAGE_EXAMS: 每阶段 10 题结业考试（6 阶段），80 分通过
"""

# ============================================================
# 课时测验（每课 3 题）
# ============================================================

LESSON_QUIZZES = {
    # ---- 阶段 1: 股票是什么 ----
    "ch01": [
        {"question": "买一只股票，本质上你买的是什么？",
         "options": ["公司的一小部分所有权", "公司发行的债券", "一种短期彩票", "银行的存款凭证"],
         "answer": 0, "explanation": "股票代表公司所有权的一部分，你成为了公司的股东。"},
        {"question": "公司为什么要上市发行股票？",
         "options": ["为了让员工开心", "为了融资（筹集发展资金）", "为了提高知名度", "为了避税"],
         "answer": 1, "explanation": "上市的主要目的是向公众募集资金，用于扩大业务。"},
        {"question": "股东和债主（债权人）的区别是？",
         "options": ["没有区别", "股东承担风险分享收益，债主固定收利息", "债主收益更高", "股东一定能拿回本金"],
         "answer": 1, "explanation": "股东与公司共担风险共享收益；债主无论公司盈亏都收固定利息。"},
    ],
    "ch02": [
        {"question": "股票价格上涨的根本原因是？",
         "options": ["买的人比卖的人多", "公司改了个好名字", "大盘涨了它必须涨", "政府规定"],
         "answer": 0, "explanation": "供需关系决定价格：买方力量强于卖方时价格上涨。"},
        {"question": "长期来看，股价主要跟随什么变化？",
         "options": ["市场情绪", "公司盈利能力", "新闻数量", "交易量"],
         "answer": 1, "explanation": "短期看情绪，长期看业绩。公司赚钱能力最终决定股价。"},
        {"question": "「股市短期是投票机，长期是称重机」是谁说的？",
         "options": ["巴菲特", "格雷厄姆", "索罗斯", "彼得·林奇"],
         "answer": 1, "explanation": "这是价值投资之父本杰明·格雷厄姆的名言。"},
    ],
    "ch03": [
        {"question": "散户和机构投资者最大的区别通常是？",
         "options": ["资金规模和专业程度", "开户券商不同", "交易时间不同", "买的股票不同"],
         "answer": 0, "explanation": "机构有专业团队、更多资金和更快信息，散户需要靠纪律弥补。"},
        {"question": "作为散户，最现实的竞争优势是？",
         "options": ["更快的网速", "更多的内幕消息", "耐心和长期视角", "更高的杠杆"],
         "answer": 2, "explanation": "散户没有业绩考核压力，可以长期持有等待价值兑现。"},
        {"question": "以下哪种行为最像「韭菜」？",
         "options": ["定期复盘总结", "追涨杀跌、听消息炒股", "控制仓位", "设好止损"],
         "answer": 1, "explanation": "追涨杀跌、盲目跟风是散户亏损的最常见原因。"},
    ],
    "ch04": [
        {"question": "股票账户里的「浮动盈亏」意味着？",
         "options": ["已经到手的钱", "卖出前只是数字，卖出后才变成实际盈亏", "券商欠你的钱", "下周会消失的钱"],
         "answer": 1, "explanation": "浮盈浮亏只有在你卖出平仓那一刻才变成真实盈亏。"},
        {"question": "A 股、港股、美股最大的区别不包括？",
         "options": ["交易时间", "涨跌幅限制", "货币单位", "股票的颜色"],
         "answer": 3, "explanation": "不同市场在交易时间、涨跌幅、货币等方面规则不同，与颜色无关。"},
        {"question": "美股和 A 股相比，一个显著特点是？",
         "options": ["有涨跌停板", "没有涨跌幅限制", "只能买不能卖", "每天只交易 1 小时"],
         "answer": 1, "explanation": "美股没有单日涨跌幅限制（但有熔断机制），波动可能更剧烈。"},
    ],
    # ---- 阶段 2: 认识全球股票市场 ----
    "ch05": [
        {"question": "纽约证券交易所（NYSE）位于哪个城市？",
         "options": ["华盛顿", "纽约", "芝加哥", "旧金山"],
         "answer": 1, "explanation": "NYSE 位于纽约华尔街，是全球市值最大的交易所。"},
        {"question": "纳斯达克（NASDAQ）以哪类公司闻名？",
         "options": ["石油公司", "科技公司", "农业公司", "纺织公司"],
         "answer": 1, "explanation": "纳斯达克聚集了苹果、微软、英伟达等科技巨头。"},
        {"question": "美股的主要交易时段（北京时间）大约是？",
         "options": ["早上 9 点到下午 3 点", "晚上 9:30 到凌晨 4 点", "中午 12 点到晚上 8 点", "全天 24 小时"],
         "answer": 1, "explanation": "美股常规时段为美东 9:30-16:00，对应北京时间 21:30-04:00（夏令时）。"},
    ],
    "ch06": [
        {"question": "A 股的涨跌幅限制（主板）通常是？",
         "options": ["无限制", "±10%", "±20%", "±5%"],
         "answer": 1, "explanation": "A 股主板单日涨跌幅限制为 ±10%（科创板/创业板为 ±20%）。"},
        {"question": "港股通允许内地投资者？",
         "options": ["直接买美股", "通过内地券商买部分港股", "在香港开户", "免除所有税费"],
         "answer": 1, "explanation": "港股通是内地与香港市场的互联互通机制，可投资部分港股标的。"},
        {"question": "A 股交易使用的货币是？",
         "options": ["美元", "港币", "人民币", "欧元"],
         "answer": 2, "explanation": "A 股以人民币计价交易。"},
    ],
    "ch07": [
        {"question": "日本股市的代表性指数是？",
         "options": ["恒生指数", "日经 225", "富时 100", "DAX"],
         "answer": 1, "explanation": "日经 225 指数是日本股市最重要的基准指数。"},
        {"question": "英国伦敦证券交易所的代表指数是？",
         "options": ["CAC 40", "DAX", "富时 100（FTSE 100）", "SMI"],
         "answer": 2, "explanation": "富时 100 指数包含伦敦交易所市值最大的 100 家公司。"},
        {"question": "投资全球市场最大的好处是？",
         "options": ["保证赚钱", "分散单一市场风险", "不用交税", "交易更方便"],
         "answer": 1, "explanation": "不同市场周期不同步，全球配置可以分散风险。"},
    ],
    "ch08": [
        {"question": "交易所的主要功能是？",
         "options": ["印刷股票", "提供买卖双方撮合交易的平台", "决定股价", "给公司贷款"],
         "answer": 1, "explanation": "交易所是撮合买卖双方订单的平台，本身不决定价格。"},
        {"question": "「流动性好」的市场意味着？",
         "options": ["水很多", "想买买得到、想卖卖得出，且价格冲击小", "股价天天涨", "交易免费"],
         "answer": 1, "explanation": "流动性好的市场订单能快速成交，且大额交易不会大幅影响价格。"},
        {"question": "做市商（Market Maker）的作用是？",
         "options": ["操纵股价", "持续提供买卖报价，维持市场流动性", "审核上市公司", "收税"],
         "answer": 1, "explanation": "做市商通过持续挂单提供流动性，赚取买卖价差。"},
    ],
    # ---- 阶段 3: 如何认识一家公司 ----
    "ch09": [
        {"question": "了解一家公司商业模式最直接的问题是？",
         "options": ["它的 logo 好看吗", "它靠什么赚钱", "它的 CEO 是谁", "它有多少员工"],
         "answer": 1, "explanation": "商业模式的核心就是：这家公司靠什么产品/服务赚钱。"},
        {"question": "苹果公司的主要收入来源是？",
         "options": ["广告", "硬件销售（iPhone 等）+ 服务", "云计算", "游戏"],
         "answer": 1, "explanation": "iPhone 等硬件是苹果最大收入来源，服务业务增长迅速。"},
        {"question": "「护城河」指的是？",
         "options": ["公司周围的河", "公司抵御竞争对手的持久优势", "公司的现金储备", "公司的专利数量"],
         "answer": 1, "explanation": "护城河是巴菲特概念，指品牌、网络效应、成本优势等持久竞争力。"},
    ],
    "ch10": [
        {"question": "市盈率（PE）的计算公式是？",
         "options": ["股价 ÷ 每股收益", "股价 × 总股本", "营收 ÷ 利润", "市值 ÷ 员工数"],
         "answer": 0, "explanation": "PE = 股价 / 每股收益（EPS），衡量投资者愿意为每元利润付多少钱。"},
        {"question": "一家 PE 为 50 倍的公司，通常意味着？",
         "options": ["很便宜", "市场预期它高增长，或可能被高估", "马上要破产", "是国企"],
         "answer": 1, "explanation": "高 PE 反映市场对其增长的高预期，但也可能意味着估值过高。"},
        {"question": "比较 PE 时，最合理的做法是？",
         "options": ["和任何公司比", "和同行业公司比", "和银行存款利率比", "和房价比"],
         "answer": 1, "explanation": "不同行业 PE 水平差异很大，同行业比较才有意义。"},
    ],
    "ch11": [
        {"question": "财报中的「营收」指的是？",
         "options": ["公司赚到的净利润", "公司销售产品/服务的总收入", "公司的现金余额", "公司的股价总额"],
         "answer": 1, "explanation": "营收（Revenue）是公司通过主营业务获得的总收入，未扣除成本。"},
        {"question": "营收增长但利润率下降，可能意味着？",
         "options": ["公司一定很好", "公司在烧钱换增长或成本失控", "财报造假", "马上分红"],
         "answer": 1, "explanation": "增收不增利需要警惕：可能是价格战、成本上升或激进扩张。"},
        {"question": "美股公司通常多久发布一次财报？",
         "options": ["每月", "每季度", "每年", "每两年"],
         "answer": 1, "explanation": "美股上市公司按季度发布财报（Q1-Q4）。"},
    ],
    "ch12": [
        {"question": "看一家公司时，「毛利率」高通常说明？",
         "options": ["公司定价能力强或成本低", "公司快破产了", "公司不交税", "公司员工少"],
         "answer": 0, "explanation": "高毛利率反映产品竞争力：要么能卖高价，要么成本控制得好。"},
        {"question": "以下哪个指标反映公司「赚钱的真本事」？",
         "options": ["市值", "净利润率", "员工数量", "办公楼面积"],
         "answer": 1, "explanation": "净利润率 = 净利润/营收，反映每一元收入最终能赚多少。"},
        {"question": "自由现金流为正且持续增长，通常是？",
         "options": ["坏信号", "好信号，公司造血能力强", "无关紧要的信号", "造假信号"],
         "answer": 1, "explanation": "自由现金流是公司真正能自由支配的钱，持续为正说明业务健康。"},
    ],
    # ---- 阶段 4: 理解股价和图表 ----
    "ch13": [
        {"question": "K 线（蜡烛图）中，一根绿色（或空心）K 线表示？",
         "options": ["收盘价高于开盘价（上涨）", "收盘价低于开盘价（下跌）", "停牌", "除权"],
         "answer": 0, "explanation": "绿色/阳线表示该周期内收盘价高于开盘价。"},
        {"question": "K 线的「上影线」长说明？",
         "options": ["价格曾冲高但回落", "价格一直在涨", "没有交易发生", "公司分红了"],
         "answer": 0, "explanation": "上影线是最高价与实体之间的距离，长上影说明冲高回落。"},
        {"question": "成交量放大配合价格上涨，通常说明？",
         "options": ["上涨有资金支持，较可信", "一定是庄家出货", "市场没人参与", "应该立刻卖出"],
         "answer": 0, "explanation": "量价齐升是健康的上涨形态，说明有真实资金推动。"},
    ],
    "ch14": [
        {"question": "移动平均线（MA）的主要作用是？",
         "options": ["预测明天涨跌", "平滑价格波动，显示趋势方向", "计算分红", "显示公司价值"],
         "answer": 1, "explanation": "均线平滑短期波动，帮助识别中长期趋势方向。"},
        {"question": "股价站上 20 日均线，通常被解读为？",
         "options": ["短期趋势转强", "必须马上卖出", "公司要退市", "没有任何意义"],
         "answer": 0, "explanation": "价格站上均线是趋势转强的常见技术信号。"},
        {"question": "「金叉」指的是？",
         "options": ["短期均线上穿长期均线", "股价创新高", "成交量放大", "公司发黄金"],
         "answer": 0, "explanation": "金叉（如 5 日线上穿 20 日线）是经典的买入参考信号。"},
    ],
    "ch15": [
        {"question": "技术分析的基本假设是？",
         "options": ["历史会重演，价格包含一切信息", "股价完全随机", "只有内幕消息有用", "财报决定一切"],
         "answer": 0, "explanation": "技术分析认为价格已反映所有信息，且历史模式会重复。"},
        {"question": "技术分析最大的局限是？",
         "options": ["太复杂", "无法预测突发事件和基本面变化", "需要电脑", "要花钱"],
         "answer": 1, "explanation": "技术分析看的是历史价格，无法预知财报暴雷、政策突变等事件。"},
        {"question": "对新手来说，技术分析应该？",
         "options": ["作为唯一决策依据", "作为辅助工具，结合基本面使用", "完全不用学", "用来天天交易"],
         "answer": 1, "explanation": "技术分析适合辅助择时，但不能替代对公司基本面的研究。"},
    ],
    "ch16": [
        {"question": "「支撑位」指的是？",
         "options": ["价格跌到此处容易获得买盘支撑", "价格涨到这里会停", "公司的支持部门", "交易所的地板"],
         "answer": 0, "explanation": "支撑位是历史上价格跌到附近就反弹的区域，买盘聚集。"},
        {"question": "「阻力位」被突破后，可能变成？",
         "options": ["新的支撑位", "新的阻力位", "没有任何意义", "停牌点"],
         "answer": 0, "explanation": "阻力变支撑是技术分析的经典原理：突破后角色互换。"},
        {"question": "在阻力位附近追涨买入，风险是？",
         "options": ["没有风险", "可能买在短期高点，面临回调", "一定会赚钱", "会被罚款"],
         "answer": 1, "explanation": "阻力位是卖压聚集区，追涨容易买在短期顶部。"},
    ],
    # ---- 阶段 5: 建立风险意识 ----
    "ch17": [
        {"question": "「不要把鸡蛋放在同一个篮子里」说的是？",
         "options": ["分散投资", "集中投资", "不要投资", "只买一只股"],
         "answer": 0, "explanation": "分散投资可以降低单一资产暴跌带来的毁灭性打击。"},
        {"question": "单只股票仓位建议不超过总资金的？",
         "options": ["100%", "50-80%", "20-30%", "1%"],
         "answer": 2, "explanation": "单票 20-30% 是常见的风控上限，避免一只股票毁掉整个账户。"},
        {"question": "加杠杆炒股最大的风险是？",
         "options": ["赚得太快", "亏损被放大，可能爆仓血本无归", "手续太麻烦", "利息太低"],
         "answer": 1, "explanation": "杠杆放大收益也放大亏损，新手应坚决避免。"},
    ],
    "ch18": [
        {"question": "止损的核心作用是？",
         "options": ["保证不亏钱", "把单笔亏损控制在可承受范围内", "让股价反弹", "减少交易次数"],
         "answer": 1, "explanation": "止损是预设的退出点，防止小亏变成无法承受的大亏。"},
        {"question": "新手常用的止损幅度是？",
         "options": ["-50%", "-30%", "-5% 到 -15%", "不设止损"],
         "answer": 2, "explanation": "5-15% 的止损幅度既能容忍正常波动，又能控制损失。"},
        {"question": "设了止损但股价跌到止损位时「再等等看」，这是？",
         "options": ["明智的灵活", "破坏纪律，亏损扩大的开始", "高手操作", "无所谓"],
         "answer": 1, "explanation": "随意修改止损等于没有止损，是亏损扩大的典型路径。"},
    ],
    "ch19": [
        {"question": "「仓位管理」主要解决什么问题？",
         "options": ["买哪只股票", "每次投多少钱", "什么时候卖", "选哪个券商"],
         "answer": 1, "explanation": "仓位管理决定每笔交易投入多少资金，是风控的核心。"},
        {"question": "单笔交易最大可接受亏损，一般建议不超过总资金的？",
         "options": ["20%", "10%", "1-2%", "50%"],
         "answer": 2, "explanation": "职业交易者常用 1-2% 规则：单笔亏损不超过总资金的 1-2%。"},
        {"question": "根据止损距离反推买入数量，这叫？",
         "options": ["拍脑袋建仓", "仓位计算", "满仓操作", "随机买入"],
         "answer": 1, "explanation": "仓位计算：可亏金额 ÷ 每股止损距离 = 应买股数。"},
    ],
    "ch20": [
        {"question": "「沉没成本谬误」在投资中的表现是？",
         "options": ["亏了不肯卖，因为已经亏了很多", "赚钱就跑", "频繁交易", "听消息买股"],
         "answer": 0, "explanation": "已经亏掉的钱是沉没成本，决策应基于未来前景而非过去亏损。"},
        {"question": "FOMO（害怕错过）情绪会导致？",
         "options": ["理性分析", "追高买入", "耐心等待", "分散投资"],
         "answer": 1, "explanation": "FOMO 让人在价格大涨后冲动追入，往往买在高点。"},
        {"question": "对抗情绪化交易最有效的方法是？",
         "options": ["凭感觉", "提前写好交易计划并严格执行", "多看群聊", "加仓摊平"],
         "answer": 1, "explanation": "交易计划在冷静时制定，执行时不受情绪干扰。"},
    ],
    # ---- 阶段 6: 模拟交易与复盘 ----
    "ch21": [
        {"question": "模拟交易最大的价值是？",
         "options": ["赚虚拟的钱", "零风险练习交易流程和纪律", "炫耀战绩", "打发时间"],
         "answer": 1, "explanation": "模拟交易让你在不亏真钱的情况下，练习完整的交易决策流程。"},
        {"question": "模拟交易和真实交易最大的区别是？",
         "options": ["规则不同", "心理压力完全不同", "价格不同", "时间不同"],
         "answer": 1, "explanation": "真金白银会带来恐惧和贪婪，模拟盘无法完全模拟心理压力。"},
        {"question": "从模拟转向实盘时，最好的做法是？",
         "options": ["直接全仓杀入", "先用小资金试水，逐步加大", "借钱加大杠杆", "永远不转实盘"],
         "answer": 1, "explanation": "小资金实盘能让你在真实心理压力下继续学习，风险可控。"},
    ],
    "ch22": [
        {"question": "交易日志最应该记录什么？",
         "options": ["只记赚钱的交易", "买入理由、计划、执行情况和事后反思", "只记价格", "别人的观点"],
         "answer": 1, "explanation": "完整的交易日志包括：为什么买、计划是什么、执行如何、学到什么。"},
        {"question": "复盘时发现「买入理由已经不成立」，应该？",
         "options": ["继续持有等回本", "认错卖出", "加仓摊平", "删掉交易记录"],
         "answer": 1, "explanation": "理由不成立就该离场，持有亏损股票等回本是常见错误。"},
        {"question": "定期复盘的主要目的是？",
         "options": ["后悔当初", "发现自己的错误模式并改进", "证明自己对", "打发时间"],
         "answer": 1, "explanation": "复盘的价值在于识别重复犯的错误，形成改进规则。"},
    ],
    "ch23": [
        {"question": "一笔好交易的标准是？",
         "options": ["一定赚钱了", "按计划执行了，无论盈亏", "买在最低点", "卖在最高点"],
         "answer": 1, "explanation": "好交易=严格执行计划的交易。单次盈亏有运气成分，纪律才是长期保障。"},
        {"question": "「截断亏损，让利润奔跑」意味着？",
         "options": ["亏了就跑，赚了也马上跑", "快速止损，但给盈利单更多空间", "不止损不止盈", "频繁交易"],
         "answer": 1, "explanation": "这是趋势交易的核心理念：严格控制亏损，让盈利充分增长。"},
        {"question": "新手最常犯的错误是？",
         "options": ["太早止损", "亏死扛、赚快跑（与正确做法相反）", "太分散", "太耐心"],
         "answer": 1, "explanation": "人性使然：亏损时不愿认错，盈利时急于落袋，恰好做反了。"},
    ],
    "ch24": [
        {"question": "制定交易计划应该包括哪些要素？",
         "options": ["只写买入价", "买入理由、仓位、止损、目标价、持有期限", "只写目标价", "别人的建议"],
         "answer": 1, "explanation": "完整计划五要素：理由、仓位、止损、目标、期限，缺一不可。"},
        {"question": "学习投资的正确心态是？",
         "options": ["快速致富", "终身学习，慢慢变富", "一夜暴富", "赌一把大的"],
         "answer": 1, "explanation": "投资是马拉松不是短跑，持续学习和复利效应才是正道。"},
        {"question": "完成全部课程后，你最应该做的是？",
         "options": ["立刻投入全部积蓄", "继续模拟练习，小资金实盘，保持复盘", "再也不学习", "到处推荐股票"],
         "answer": 1, "explanation": "课程只是起点：持续练习、小额实盘、定期复盘才能不断进步。"},
    ],
}

# ============================================================
# 阶段结业考试（每阶段 10 题，80 分通过）
# ============================================================

STAGE_EXAMS = {
    "stage1": {
        "title": "阶段一结业考试：股票是什么",
        "pass_score": 80,
        "questions": [
            {"question": "股票代表的是？",
             "options": ["公司所有权的一部分", "公司的债务", "一种保险", "银行存款"],
             "answer": 0, "explanation": "股票=公司所有权凭证。"},
            {"question": "公司上市的主要目的是？",
             "options": ["提高知名度", "融资", "避税", "奖励员工"],
             "answer": 1, "explanation": "上市核心目的是向公众募集资金。"},
            {"question": "股价短期波动主要由什么决定？",
             "options": ["公司利润", "供需关系（买卖力量）", "政府定价", "员工数量"],
             "answer": 1, "explanation": "短期价格由买卖双方力量对比决定。"},
            {"question": "长期看，股价最终跟随什么？",
             "options": ["市场情绪", "公司盈利能力", "交易量", "新闻数量"],
             "answer": 1, "explanation": "长期股价反映公司的真实赚钱能力。"},
            {"question": "股东与债权人的本质区别是？",
             "options": ["股东固定收益", "股东共担风险共享收益，债权人固定收息", "没有区别", "债权人风险更大"],
             "answer": 1, "explanation": "股东是所有者，债权人是债主。"},
            {"question": "散户最现实的优势是？",
             "options": ["信息更快", "资金更多", "耐心和长期视角", "杠杆更高"],
             "answer": 2, "explanation": "散户无业绩考核压力，可以长期持有。"},
            {"question": "浮动盈亏的含义是？",
             "options": ["已到手的利润", "卖出前只是账面数字", "券商欠款", "下周清零"],
             "answer": 1, "explanation": "浮盈浮亏只有平仓后才变成实际盈亏。"},
            {"question": "美股与 A 股相比的显著特点是？",
             "options": ["有涨跌停", "无单日涨跌幅限制", "只能买不能卖", "每天交易 1 小时"],
             "answer": 1, "explanation": "美股无涨跌停（有熔断机制）。"},
            {"question": "「追涨杀跌」的结果是？",
             "options": ["稳定盈利", "高买低卖反复亏损", "跑赢大盘", "没有影响"],
             "answer": 1, "explanation": "追涨杀跌是散户亏损的最常见模式。"},
            {"question": "投资股票的本质是？",
             "options": ["赌博", "成为公司的部分所有者，分享其成长", "买彩票", "存钱"],
             "answer": 1, "explanation": "买股票=买公司的一部分，分享其长期成长。"},
        ],
    },
    "stage2": {
        "title": "阶段二结业考试：认识全球股票市场",
        "pass_score": 80,
        "questions": [
            {"question": "全球市值最大的证券交易所是？",
             "options": ["纳斯达克", "纽约证券交易所", "伦敦证券交易所", "东京证券交易所"],
             "answer": 1, "explanation": "NYSE 是全球市值最大的交易所。"},
            {"question": "纳斯达克以哪类公司为主？",
             "options": ["能源", "科技", "农业", "纺织"],
             "answer": 1, "explanation": "纳斯达克是科技公司的聚集地。"},
            {"question": "A 股主板涨跌幅限制是？",
             "options": ["无限制", "±10%", "±20%", "±5%"],
             "answer": 1, "explanation": "A 股主板 ±10%，科创板/创业板 ±20%。"},
            {"question": "港股通的作用是？",
             "options": ["买美股", "内地投资者买部分港股", "香港人买 A 股", "免税"],
             "answer": 1, "explanation": "港股通是内地与香港的互联互通机制。"},
            {"question": "日经 225 是哪个国家的指数？",
             "options": ["中国", "韩国", "日本", "新加坡"],
             "answer": 2, "explanation": "日经 225 是日本股市的代表指数。"},
            {"question": "富时 100 指数属于哪个市场？",
             "options": ["德国", "法国", "英国", "美国"],
             "answer": 2, "explanation": "富时 100 是伦敦交易所的旗舰指数。"},
            {"question": "交易所的核心功能是？",
             "options": ["决定股价", "撮合买卖双方订单", "印刷股票", "发放贷款"],
             "answer": 1, "explanation": "交易所是撮合交易的平台。"},
            {"question": "「流动性好」意味着？",
             "options": ["股价天天涨", "买卖容易成交且价格冲击小", "交易免费", "水很多"],
             "answer": 1, "explanation": "流动性=快速成交+小额价格冲击。"},
            {"question": "全球分散投资的主要好处是？",
             "options": ["保证赚钱", "分散单一市场风险", "不用交税", "更方便"],
             "answer": 1, "explanation": "不同市场周期不同步，可分散风险。"},
            {"question": "美股常规交易时段（北京时间夏令时）是？",
             "options": ["9:00-15:00", "21:30-04:00", "12:00-20:00", "全天"],
             "answer": 1, "explanation": "美东 9:30-16:00 = 北京 21:30-04:00（夏令时）。"},
        ],
    },
    "stage3": {
        "title": "阶段三结业考试：如何认识一家公司",
        "pass_score": 80,
        "questions": [
            {"question": "了解公司商业模式的核心问题是？",
             "options": ["CEO 是谁", "它靠什么赚钱", "logo 好看吗", "员工多少"],
             "answer": 1, "explanation": "商业模式=公司赚钱的方式。"},
            {"question": "「护城河」是指？",
             "options": ["现金储备", "抵御竞争的持久优势", "专利数量", "办公楼"],
             "answer": 1, "explanation": "护城河=品牌/网络效应/成本优势等持久竞争力。"},
            {"question": "市盈率（PE）= ？",
             "options": ["股价 × 股本", "股价 ÷ 每股收益", "营收 ÷ 利润", "市值 ÷ 员工"],
             "answer": 1, "explanation": "PE = 股价 / EPS。"},
            {"question": "比较 PE 时应该？",
             "options": ["和任何公司比", "和同行业公司比", "和房价比", "和利率比"],
             "answer": 1, "explanation": "同行业比较才有意义。"},
            {"question": "「营收」是？",
             "options": ["净利润", "销售产品/服务的总收入", "现金余额", "股价总额"],
             "answer": 1, "explanation": "营收=未扣除成本的总收入。"},
            {"question": "营收增长但利润率下降，可能意味着？",
             "options": ["公司一定很好", "烧钱换增长或成本失控", "财报造假", "马上分红"],
             "answer": 1, "explanation": "增收不增利需要警惕。"},
            {"question": "美股公司财报发布频率是？",
             "options": ["每月", "每季度", "每年", "每两年"],
             "answer": 1, "explanation": "美股按季度发布财报。"},
            {"question": "高毛利率通常说明？",
             "options": ["快破产", "定价能力强或成本低", "不交税", "员工少"],
             "answer": 1, "explanation": "高毛利=产品竞争力。"},
            {"question": "净利润率反映的是？",
             "options": ["市值大小", "每一元收入最终赚多少", "员工数量", "办公面积"],
             "answer": 1, "explanation": "净利润率=净利润/营收。"},
            {"question": "自由现金流持续为正且增长，是？",
             "options": ["坏信号", "好信号，造血能力强", "无关信号", "造假信号"],
             "answer": 1, "explanation": "自由现金流是公司真正能支配的钱。"},
        ],
    },
    "stage4": {
        "title": "阶段四结业考试：理解股价和图表",
        "pass_score": 80,
        "questions": [
            {"question": "绿色（阳）K 线表示？",
             "options": ["收盘价低于开盘价", "收盘价高于开盘价", "停牌", "除权"],
             "answer": 1, "explanation": "阳线=收盘价>开盘价。"},
            {"question": "长上影线说明？",
             "options": ["一直涨", "冲高回落", "没交易", "分红"],
             "answer": 1, "explanation": "上影线=最高价与实体的距离。"},
            {"question": "量价齐升通常说明？",
             "options": ["庄家出货", "上涨有资金支持", "没人参与", "应该卖出"],
             "answer": 1, "explanation": "放量上涨较可信。"},
            {"question": "移动平均线的主要作用是？",
             "options": ["预测明天", "平滑波动显示趋势", "算分红", "显示价值"],
             "answer": 1, "explanation": "均线帮助识别趋势方向。"},
            {"question": "「金叉」是？",
             "options": ["短期均线上穿长期均线", "股价新高", "成交量放大", "发黄金"],
             "answer": 0, "explanation": "金叉=短期均线上穿长期均线。"},
            {"question": "技术分析的基本假设是？",
             "options": ["价格包含一切，历史会重演", "完全随机", "只有内幕有用", "财报决定一切"],
             "answer": 0, "explanation": "技术分析两大假设。"},
            {"question": "技术分析最大的局限是？",
             "options": ["太复杂", "无法预测突发事件", "需要电脑", "要花钱"],
             "answer": 1, "explanation": "技术分析无法预知基本面突变。"},
            {"question": "「支撑位」是？",
             "options": ["价格易获买盘支撑的区域", "价格会停涨", "支持部门", "交易所地板"],
             "answer": 0, "explanation": "支撑位=买盘聚集区。"},
            {"question": "阻力位被突破后可能变成？",
             "options": ["新支撑位", "新阻力位", "无意义", "停牌点"],
             "answer": 0, "explanation": "阻力变支撑是经典原理。"},
            {"question": "新手应如何使用技术分析？",
             "options": ["唯一依据", "辅助工具结合基本面", "完全不用", "天天交易"],
             "answer": 1, "explanation": "技术分析适合辅助择时。"},
        ],
    },
    "stage5": {
        "title": "阶段五结业考试：建立风险意识",
        "pass_score": 80,
        "questions": [
            {"question": "分散投资的目的是？",
             "options": ["赚更多", "降低单一资产暴跌的打击", "不用研究", "省手续费"],
             "answer": 1, "explanation": "分散降低毁灭性风险。"},
            {"question": "单只股票仓位建议不超过？",
             "options": ["100%", "50-80%", "20-30%", "1%"],
             "answer": 2, "explanation": "单票 20-30% 是常见风控上限。"},
            {"question": "加杠杆最大的风险是？",
             "options": ["赚太快", "亏损放大可能爆仓", "手续麻烦", "利息低"],
             "answer": 1, "explanation": "杠杆双向放大，新手应避免。"},
            {"question": "止损的核心作用是？",
             "options": ["保证不亏", "把单笔亏损控制在可承受范围", "让股价反弹", "减少交易"],
             "answer": 1, "explanation": "止损防止小亏变大亏。"},
            {"question": "新手常用止损幅度是？",
             "options": ["-50%", "-30%", "-5% 到 -15%", "不设"],
             "answer": 2, "explanation": "5-15% 兼顾波动容忍与损失控制。"},
            {"question": "随意修改止损计划等于？",
             "options": ["灵活操作", "没有止损", "高手行为", "无所谓"],
             "answer": 1, "explanation": "破坏纪律=没有止损。"},
            {"question": "单笔最大可接受亏损建议不超过总资金的？",
             "options": ["20%", "10%", "1-2%", "50%"],
             "answer": 2, "explanation": "1-2% 规则是职业标准。"},
            {"question": "仓位计算公式是？",
             "options": ["拍脑袋", "可亏金额 ÷ 每股止损距离", "满仓", "随机"],
             "answer": 1, "explanation": "仓位=可亏金额/止损距离。"},
            {"question": "「沉没成本谬误」的表现是？",
             "options": ["亏了不肯卖", "赚钱就跑", "频繁交易", "听消息"],
             "answer": 0, "explanation": "决策应基于未来而非过去亏损。"},
            {"question": "对抗情绪化交易最有效的是？",
             "options": ["凭感觉", "提前写计划并严格执行", "看群聊", "加仓摊平"],
             "answer": 1, "explanation": "计划在冷静时制定，执行时不受情绪干扰。"},
        ],
    },
    "stage6": {
        "title": "阶段六结业考试：模拟交易与复盘",
        "pass_score": 80,
        "questions": [
            {"question": "模拟交易最大的价值是？",
             "options": ["赚虚拟钱", "零风险练习流程和纪律", "炫耀", "打发时间"],
             "answer": 1, "explanation": "模拟盘让你零风险练完整流程。"},
            {"question": "模拟与实盘最大的区别是？",
             "options": ["规则", "心理压力", "价格", "时间"],
             "answer": 1, "explanation": "真金白银带来恐惧和贪婪。"},
            {"question": "从模拟转实盘最好的做法是？",
             "options": ["全仓杀入", "小资金试水逐步加大", "借钱杠杆", "永不转实盘"],
             "answer": 1, "explanation": "小资金实盘风险可控。"},
            {"question": "交易日志最应该记录？",
             "options": ["只记赚钱的", "理由、计划、执行、反思", "只记价格", "别人观点"],
             "answer": 1, "explanation": "完整日志四要素。"},
            {"question": "买入理由不成立时应该？",
             "options": ["持有等回本", "认错卖出", "加仓摊平", "删记录"],
             "answer": 1, "explanation": "理由不成立就该离场。"},
            {"question": "定期复盘的主要目的是？",
             "options": ["后悔", "发现错误模式并改进", "证明自己对", "打发时间"],
             "answer": 1, "explanation": "复盘=识别重复错误+形成规则。"},
            {"question": "一笔好交易的标准是？",
             "options": ["赚钱了", "按计划执行了", "买在最低", "卖在最高"],
             "answer": 1, "explanation": "好交易=严格执行计划。"},
            {"question": "「截断亏损，让利润奔跑」意味着？",
             "options": ["亏赚都跑", "快速止损给盈利空间", "不止损", "频繁交易"],
             "answer": 1, "explanation": "趋势交易核心理念。"},
            {"question": "新手最常犯的错误是？",
             "options": ["太早止损", "亏死扛赚快跑", "太分散", "太耐心"],
             "answer": 1, "explanation": "人性使然，恰好做反。"},
            {"question": "完整交易计划五要素是？",
             "options": ["只写买入价", "理由、仓位、止损、目标、期限", "只写目标价", "别人建议"],
             "answer": 1, "explanation": "五要素缺一不可。"},
        ],
    },
}


def get_lesson_quiz(chapter_id: str) -> list[dict]:
    """获取课时测验（不含答案，供前端展示）"""
    quiz = LESSON_QUIZZES.get(chapter_id, [])
    return [{"question": q["question"], "options": q["options"]} for q in quiz]


def grade_lesson_quiz(chapter_id: str, answers: list[int]) -> dict:
    """批改课时测验"""
    quiz = LESSON_QUIZZES.get(chapter_id, [])
    if not quiz:
        return {"error": "该课程没有测验"}

    correct = 0
    details = []
    for i, q in enumerate(quiz):
        user_ans = answers[i] if i < len(answers) else -1
        is_correct = user_ans == q["answer"]
        if is_correct:
            correct += 1
        details.append({
            "question": q["question"],
            "your_answer": user_ans,
            "correct_answer": q["answer"],
            "is_correct": is_correct,
            "explanation": q["explanation"],
        })

    total = len(quiz)
    score = round(correct / total * 100) if total > 0 else 0
    return {
        "score": score,
        "correct_count": correct,
        "total_questions": total,
        "passed": score >= 60,
        "details": details,
    }


def get_stage_exam(stage_id: str) -> dict:
    """获取阶段考试（不含答案）"""
    exam = STAGE_EXAMS.get(stage_id)
    if not exam:
        return {"error": "该阶段没有考试"}
    return {
        "title": exam["title"],
        "pass_score": exam["pass_score"],
        "questions": [{"question": q["question"], "options": q["options"]}
                      for q in exam["questions"]],
    }


def grade_stage_exam(stage_id: str, answers: list[int]) -> dict:
    """批改阶段考试"""
    exam = STAGE_EXAMS.get(stage_id)
    if not exam:
        return {"error": "该阶段没有考试"}

    questions = exam["questions"]
    correct = 0
    details = []
    for i, q in enumerate(questions):
        user_ans = answers[i] if i < len(answers) else -1
        is_correct = user_ans == q["answer"]
        if is_correct:
            correct += 1
        details.append({
            "question": q["question"],
            "your_answer": user_ans,
            "correct_answer": q["answer"],
            "is_correct": is_correct,
            "explanation": q["explanation"],
        })

    total = len(questions)
    score = round(correct / total * 100) if total > 0 else 0
    return {
        "score": score,
        "correct_count": correct,
        "total_questions": total,
        "passed": score >= exam["pass_score"],
        "pass_score": exam["pass_score"],
        "details": details,
    }


__all__ = [
    "LESSON_QUIZZES", "STAGE_EXAMS",
    "get_lesson_quiz", "grade_lesson_quiz",
    "get_stage_exam", "grade_stage_exam",
]
