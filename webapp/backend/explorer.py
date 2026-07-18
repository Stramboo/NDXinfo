# -*- coding: utf-8 -*-
"""
explorer.py — 世界市场探索模块  Phase 3
本模块包含 8 大市场定义、50+ 代表公司、行业分类，为教学场景提供静态数据。
"""

from datetime import datetime, timezone, timedelta
import random

CST = timezone(timedelta(hours=8))

MARKETS = [
    {
        "id": "us", "name": "美国", "fullName": "美国股市（NYSE + NASDAQ）",
        "exchanges": ['NYSE（纽约证交所）', 'NASDAQ（纳斯达克）'],
        "currency": "USD", "currencySymbol": "$",
        "indices": [
            {"name": "S&P 500", "symbol": "^GSPC", "description": "500 家大公司，最全面"},
            {"name": "NASDAQ", "symbol": "^IXIC", "description": "科技股为主"},
            {"name": "道琼斯", "symbol": "^DJI", "description": "30 只超大蓝筹"},
        ],
        "timezone": "America/New_York", "openTime": "09:30", "closeTime": "16:00",
        "localTimes": {"open": "21:30", "close": "04:00"},
        "features": ['全球最大、最深的股票市场', 'T+0 结算，可以做空', '无涨跌停限制', '涵盖全球最知名科技公司'],
        "description": "美股是全球最重要的股票市场，由 NYSE 和 NASDAQ 两大交易所组成。苹果、微软、英伟达等科技巨头都在这里上市。对中国投资者来说，交易时间在晚上，可以兼顾白天工作。",
    },
    {
        "id": "cn", "name": "中国 A 股", "fullName": "中国 A 股（上海 + 深圳）",
        "exchanges": ['上交所（上海）', '深交所（深圳）', '北交所（北京）'],
        "currency": "CNY", "currencySymbol": "¥",
        "indices": [
            {"name": "上证综指", "symbol": "000001.SS", "description": "上海全市场"},
            {"name": "深证成指", "symbol": "399001.SZ", "description": "深圳市场"},
            {"name": "沪深300", "symbol": "000300.SS", "description": "300 只大盘蓝筹"},
        ],
        "timezone": "Asia/Shanghai", "openTime": "09:30", "closeTime": "15:00",
        "localTimes": {"open": "09:30", "close": "15:00"},
        "features": ['全球第二大股票市场', '±10% 涨跌停限制', 'T+1 交割', '散户占比高，政策影响大'],
        "description": "A 股是中国大陆最主要的股票市场，由上海和深圳两个交易所组成。A 股有涨跌停限制（±10%），采用 T+1 结算制度，即今天买入明天才能卖出。",
    },
    {
        "id": "hk", "name": "港股", "fullName": "香港交易所（HKEX）",
        "exchanges": ['香港交易所（HKEX）'],
        "currency": "HKD", "currencySymbol": "HK$",
        "indices": [
            {"name": "恒生指数", "symbol": "^HSI", "description": "港股代表指数"},
            {"name": "恒生科技", "symbol": "^HSTECH", "description": "科技股指数"},
            {"name": "国企指数", "symbol": "^HSCEI", "description": "H 股表现"},
        ],
        "timezone": "Asia/Hong_Kong", "openTime": "09:30", "closeTime": "16:00",
        "localTimes": {"open": "09:30", "close": "16:00"},
        "features": ['国际资金自由进出', '无涨跌停限制', '腾讯、阿里等中概股聚集地', '与 A 股有 AH 价差'],
        "description": "港股是连接中国和全球资本市场的桥梁。交易时间与 A 股相同（北京时间 9:30-16:00），但没有涨跌停限制。港股通让内地投资者也能方便地买卖港股。",
    },
    {
        "id": "jp", "name": "日本", "fullName": "东京证券交易所（TSE）",
        "exchanges": ['东京证券交易所（TSE）'],
        "currency": "JPY", "currencySymbol": "¥",
        "indices": [
            {"name": "日经 225", "symbol": "^N225", "description": "日本代表指数"},
            {"name": "东证指数", "symbol": "TOPX", "description": "东证一部综合"},
        ],
        "timezone": "Asia/Tokyo", "openTime": "09:00", "closeTime": "15:00",
        "localTimes": {"open": "08:00", "close": "14:00"},
        "features": ['亚洲最成熟的发达市场', '汽车和电子工业强国', '日元汇率影响大', '分红文化独特'],
        "description": "日本是全球第三大股票市场，以汽车（丰田、本田）和电子（索尼、任天堂）产业著称。日经 225 指数是日本经济的晴雨表。",
    },
    {
        "id": "uk", "name": "英国", "fullName": "伦敦证券交易所（LSE）",
        "exchanges": ['伦敦证交所（LSE）'],
        "currency": "GBP", "currencySymbol": "£",
        "indices": [
            {"name": "富时 100", "symbol": "^FTSE", "description": "英国蓝筹指数"},
            {"name": "富时 250", "symbol": "^FTMC", "description": "中型股指数"},
        ],
        "timezone": "Europe/London", "openTime": "08:00", "closeTime": "16:30",
        "localTimes": {"open": "15:00", "close": "23:30"},
        "features": ['欧洲最大的股票市场', '金融和资源股占比高', '传统高分红市场', '历史悠久（1698 年成立）'],
        "description": "伦敦是欧洲金融中心，富时 100 涵盖英国最大的 100 家上市公司。汇丰、壳牌、联合利华等全球知名企业都在此上市。",
    },
    {
        "id": "de", "name": "德国", "fullName": "法兰克福证券交易所（FWB）",
        "exchanges": ['法兰克福证交所（FWB）', 'Xetra 电子交易'],
        "currency": "EUR", "currencySymbol": "€",
        "indices": [
            {"name": "DAX 40", "symbol": "^GDAXI", "description": "德国蓝筹 40 强"},
            {"name": "MDAX", "symbol": "^MDAXI", "description": "中型企业"},
            {"name": "TecDAX", "symbol": "^TECDAX", "description": "科技股"},
        ],
        "timezone": "Europe/Berlin", "openTime": "09:00", "closeTime": "17:30",
        "localTimes": {"open": "15:00", "close": "23:30"},
        "features": ['欧洲最大经济体市场', '工业制造强国', '高分红传统', '汽车和化工产业主导'],
        "description": "德国 DAX 指数涵盖大众、西门子、SAP 等工业巨头，是全球制造业的标杆。德国股市以高分红和稳健增长著称。",
    },
    {
        "id": "ca", "name": "加拿大", "fullName": "多伦多证券交易所（TSX）",
        "exchanges": ['多伦多证交所（TSX）'],
        "currency": "CAD", "currencySymbol": "C$",
        "indices": [
            {"name": "S&P/TSX", "symbol": "^GSPTSE", "description": "加拿大综合指数"},
        ],
        "timezone": "America/Toronto", "openTime": "09:30", "closeTime": "16:00",
        "localTimes": {"open": "21:30", "close": "04:00"},
        "features": ['资源类股票占比高（矿产、能源）', '银行股稳健', '与美国市场联动性强'],
        "description": "加拿大股市以资源类公司（矿产、石油、天然气）和五大银行为核心，与美国经济高度关联。是了解资源型经济的窗口。",
    },
    {
        "id": "kr", "name": "韩国", "fullName": "韩国交易所（KRX）",
        "exchanges": ['韩国交易所（KRX）'],
        "currency": "KRW", "currencySymbol": "₩",
        "indices": [
            {"name": "KOSPI", "symbol": "^KS11", "description": "韩国综合指数"},
            {"name": "KOSDAQ", "symbol": "^KQ11", "description": "创业板"},
        ],
        "timezone": "Asia/Seoul", "openTime": "09:00", "closeTime": "15:30",
        "localTimes": {"open": "08:00", "close": "14:30"},
        "features": ['三星电子占 KOSPI 权重超 20%', '半导体产业主导', '出口导向型经济', '科技 + 制造为主'],
        "description": "韩国股市最鲜明特点是三星电子的权重极高。三星、SK 海力士等半导体企业是全球产业链的关键环节。了解韩国市场 = 了解全球半导体产业的脉搏。",
    },
]

COMPANIES = [
    {
        "symbol": "AAPL", "name": "苹果", "nameEn": "Apple Inc.",
        "market": "us", "sector": "科技", "industry": "消费电子",
        "products": "iPhone/Mac/Wearables", "description": "全球市值最大公司之一",
    },
    {
        "symbol": "MSFT", "name": "微软", "nameEn": "Microsoft Corp.",
        "market": "us", "sector": "科技", "industry": "软件/云服务",
        "products": "Windows/Azure/Office", "description": "企业软件霸主",
    },
    {
        "symbol": "NVDA", "name": "英伟达", "nameEn": "NVIDIA Corp.",
        "market": "us", "sector": "科技", "industry": "半导体",
        "products": "AI GPU/CUDA", "description": "AI 时代的核心公司",
    },
    {
        "symbol": "GOOGL", "name": "谷歌", "nameEn": "Alphabet Inc.",
        "market": "us", "sector": "科技", "industry": "互联网",
        "products": "搜索/YouTube/Android", "description": "全球最大搜索引擎",
    },
    {
        "symbol": "AMZN", "name": "亚马逊", "nameEn": "Amazon.com",
        "market": "us", "sector": "消费", "industry": "电商/云计算",
        "products": "电商/AWS", "description": "电商+云服务双引擎",
    },
    {
        "symbol": "TSLA", "name": "特斯拉", "nameEn": "Tesla Inc.",
        "market": "us", "sector": "消费", "industry": "电动车",
        "products": "Model 3/Y/Cybertruck", "description": "电动车行业标杆",
    },
    {
        "symbol": "META", "name": "Meta", "nameEn": "Meta Platforms",
        "market": "us", "sector": "科技", "industry": "社交媒体",
        "products": "Facebook/Instagram/WhatsApp", "description": "全球最大社交网络",
    },
    {
        "symbol": "BRK.B", "name": "伯克希尔", "nameEn": "Berkshire Hathaway",
        "market": "us", "sector": "金融", "industry": "综合投资",
        "products": "保险/铁路/能源", "description": "巴菲特的投资旗舰",
    },
    {
        "symbol": "JPM", "name": "摩根大通", "nameEn": "JPMorgan Chase",
        "market": "us", "sector": "金融", "industry": "银行",
        "products": "商业银行/投行", "description": "美国最大银行",
    },
    {
        "symbol": "V", "name": "维萨", "nameEn": "Visa Inc.",
        "market": "us", "sector": "金融", "industry": "支付",
        "products": "信用卡网络", "description": "全球最大支付网络",
    },
    {
        "symbol": "JNJ", "name": "强生", "nameEn": "Johnson & Johnson",
        "market": "us", "sector": "医药", "industry": "制药/消费品",
        "products": "药品/医疗器械", "description": "全球最大医疗保健公司",
    },
    {
        "symbol": "UNH", "name": "联合健康", "nameEn": "UnitedHealth Group",
        "market": "us", "sector": "医药", "industry": "医疗保险",
        "products": "医疗保险/服务", "description": "美国最大医保公司",
    },
    {
        "symbol": "XOM", "name": "埃克森美孚", "nameEn": "Exxon Mobil",
        "market": "us", "sector": "能源", "industry": "石油天然气",
        "products": "勘探/炼油", "description": "全球最大石油公司之一",
    },
    {
        "symbol": "WMT", "name": "沃尔玛", "nameEn": "Walmart Inc.",
        "market": "us", "sector": "消费", "industry": "零售",
        "products": "超市/电商", "description": "全球最大零售商",
    },
    {
        "symbol": "HD", "name": "家得宝", "nameEn": "Home Depot",
        "market": "us", "sector": "消费", "industry": "家居建材",
        "products": "家居装修零售", "description": "北美家装龙头",
    },
    {
        "symbol": "COST", "name": "好市多", "nameEn": "Costco Wholesale",
        "market": "us", "sector": "消费", "industry": "仓储零售",
        "products": "会员制仓储超市", "description": "会员制零售标杆",
    },
    {
        "symbol": "600519", "name": "贵州茅台", "nameEn": "Kweichow Moutai",
        "market": "cn", "sector": "消费", "industry": "白酒",
        "products": "茅台酒", "description": "中国市值最高公司之一",
    },
    {
        "symbol": "000858", "name": "五粮液", "nameEn": "Wuliangye Yibin",
        "market": "cn", "sector": "消费", "industry": "白酒",
        "products": "高端白酒", "description": "白酒行业第二",
    },
    {
        "symbol": "601398", "name": "工商银行", "nameEn": "ICBC",
        "market": "cn", "sector": "金融", "industry": "银行",
        "products": "商业银行", "description": "全球市值最大银行",
    },
    {
        "symbol": "601318", "name": "中国平安", "nameEn": "Ping An Insurance",
        "market": "cn", "sector": "金融", "industry": "保险",
        "products": "寿险/产险/银行", "description": "综合金融集团",
    },
    {
        "symbol": "300750", "name": "宁德时代", "nameEn": "CATL",
        "market": "cn", "sector": "科技", "industry": "电池",
        "products": "动力电池/储能", "description": "全球最大动力电池制造商",
    },
    {
        "symbol": "002594", "name": "比亚迪", "nameEn": "BYD Company",
        "market": "cn", "sector": "消费", "industry": "电动车",
        "products": "新能源车/电池", "description": "中国新能源车龙头",
    },
    {
        "symbol": "0700", "name": "腾讯控股", "nameEn": "Tencent Holdings",
        "market": "hk", "sector": "科技", "industry": "互联网",
        "products": "微信/游戏/支付", "description": "中国最大互联网公司",
    },
    {
        "symbol": "9988", "name": "阿里巴巴", "nameEn": "Alibaba Group",
        "market": "hk", "sector": "消费", "industry": "电商/云",
        "products": "淘宝/天猫/阿里云", "description": "中国最大电商平台",
    },
    {
        "symbol": "3690", "name": "美团", "nameEn": "Meituan",
        "market": "hk", "sector": "消费", "industry": "本地生活",
        "products": "外卖/到店/社区团购", "description": "本地生活服务龙头",
    },
    {
        "symbol": "1810", "name": "小米", "nameEn": "Xiaomi Corp.",
        "market": "hk", "sector": "科技", "industry": "消费电子",
        "products": "手机/IoT/汽车", "description": "全球第三大手机厂商",
    },
    {
        "symbol": "9618", "name": "京东", "nameEn": "JD.com",
        "market": "hk", "sector": "消费", "industry": "电商",
        "products": "自营电商/物流", "description": "中国第二大电商",
    },
    {
        "symbol": "7203", "name": "丰田", "nameEn": "Toyota Motor",
        "market": "jp", "sector": "消费", "industry": "汽车",
        "products": "燃油车/混动/氢能", "description": "全球最大汽车制造商",
    },
    {
        "symbol": "6758", "name": "索尼", "nameEn": "Sony Group",
        "market": "jp", "sector": "科技", "industry": "电子/娱乐",
        "products": "游戏/影像/音乐/传感器", "description": "日本电子娱乐巨头",
    },
    {
        "symbol": "7974", "name": "任天堂", "nameEn": "Nintendo",
        "market": "jp", "sector": "科技", "industry": "游戏",
        "products": "Switch/马里奥/塞尔达", "description": "全球顶级游戏公司",
    },
    {
        "symbol": "9984", "name": "软银集团", "nameEn": "SoftBank Group",
        "market": "jp", "sector": "金融", "industry": "科技投资",
        "products": "愿景基金/Arm/雅虎日本", "description": "全球最大科技投资者",
    },
    {
        "symbol": "8035", "name": "东京电子", "nameEn": "Tokyo Electron",
        "market": "jp", "sector": "科技", "industry": "半导体设备",
        "products": "芯片制造设备", "description": "全球半导体设备龙头",
    },
    {
        "symbol": "HSBA", "name": "汇丰控股", "nameEn": "HSBC Holdings",
        "market": "uk", "sector": "金融", "industry": "银行",
        "products": "商业银行/投行", "description": "欧洲最大银行",
    },
    {
        "symbol": "SHEL", "name": "壳牌", "nameEn": "Shell plc",
        "market": "uk", "sector": "能源", "industry": "石油天然气",
        "products": "勘探/炼油/LNG", "description": "全球能源巨头",
    },
    {
        "symbol": "ULVR", "name": "联合利华", "nameEn": "Unilever",
        "market": "uk", "sector": "消费", "industry": "消费品",
        "products": "食品/日化/护理", "description": "全球最大消费品公司之一",
    },
    {
        "symbol": "VOW3", "name": "大众汽车", "nameEn": "Volkswagen AG",
        "market": "de", "sector": "消费", "industry": "汽车",
        "products": "大众/奥迪/保时捷", "description": "全球最大汽车集团之一",
    },
    {
        "symbol": "SAP", "name": "SAP", "nameEn": "SAP SE",
        "market": "de", "sector": "科技", "industry": "企业软件",
        "products": "ERP/云/数据库", "description": "全球最大企业软件公司",
    },
    {
        "symbol": "SIEGY", "name": "西门子", "nameEn": "Siemens AG",
        "market": "de", "sector": "工业", "industry": "工业制造",
        "products": "自动化/能源/医疗", "description": "德国工业 4.0 代表",
    },
    {
        "symbol": "RY", "name": "加拿大皇家银行", "nameEn": "Royal Bank of Canada",
        "market": "ca", "sector": "金融", "industry": "银行",
        "products": "商业银行/财富管理", "description": "加拿大最大银行",
    },
    {
        "symbol": "CNQ", "name": "加拿大自然资源", "nameEn": "Canadian Natural Resources",
        "market": "ca", "sector": "能源", "industry": "石油天然气",
        "products": "油砂/天然气", "description": "加拿大最大能源公司之一",
    },
    {
        "symbol": "005930", "name": "三星电子", "nameEn": "Samsung Electronics",
        "market": "kr", "sector": "科技", "industry": "半导体/电子",
        "products": "内存/手机/显示", "description": "全球最大半导体/手机制造商",
    },
    {
        "symbol": "000660", "name": "SK 海力士", "nameEn": "SK Hynix",
        "market": "kr", "sector": "科技", "industry": "半导体",
        "products": "内存芯片", "description": "全球第二大内存制造商",
    },
    {
        "symbol": "035420", "name": "NAVER", "nameEn": "NAVER Corp.",
        "market": "kr", "sector": "科技", "industry": "互联网",
        "products": "搜索引擎/LINE/云", "description": "韩国的\u201c百度\u201d",
    },
]

INDUSTRIES = [
    {"name": "互联网", "count": 3, "symbols": ['GOOGL', '0700', '035420']},
    {"name": "仓储零售", "count": 1, "symbols": ['COST']},
    {"name": "企业软件", "count": 1, "symbols": ['SAP']},
    {"name": "保险", "count": 1, "symbols": ['601318']},
    {"name": "制药/消费品", "count": 1, "symbols": ['JNJ']},
    {"name": "医疗保险", "count": 1, "symbols": ['UNH']},
    {"name": "半导体", "count": 2, "symbols": ['NVDA', '000660']},
    {"name": "半导体/电子", "count": 1, "symbols": ['005930']},
    {"name": "半导体设备", "count": 1, "symbols": ['8035']},
    {"name": "家居建材", "count": 1, "symbols": ['HD']},
    {"name": "工业制造", "count": 1, "symbols": ['SIEGY']},
    {"name": "支付", "count": 1, "symbols": ['V']},
    {"name": "本地生活", "count": 1, "symbols": ['3690']},
    {"name": "汽车", "count": 2, "symbols": ['7203', 'VOW3']},
    {"name": "消费品", "count": 1, "symbols": ['ULVR']},
    {"name": "消费电子", "count": 2, "symbols": ['AAPL', '1810']},
    {"name": "游戏", "count": 1, "symbols": ['7974']},
    {"name": "电动车", "count": 2, "symbols": ['TSLA', '002594']},
    {"name": "电商", "count": 1, "symbols": ['9618']},
    {"name": "电商/云", "count": 1, "symbols": ['9988']},
    {"name": "电商/云计算", "count": 1, "symbols": ['AMZN']},
    {"name": "电子/娱乐", "count": 1, "symbols": ['6758']},
    {"name": "电池", "count": 1, "symbols": ['300750']},
    {"name": "白酒", "count": 2, "symbols": ['600519', '000858']},
    {"name": "石油天然气", "count": 3, "symbols": ['XOM', 'SHEL', 'CNQ']},
    {"name": "社交媒体", "count": 1, "symbols": ['META']},
    {"name": "科技投资", "count": 1, "symbols": ['9984']},
    {"name": "综合投资", "count": 1, "symbols": ['BRK.B']},
    {"name": "软件/云服务", "count": 1, "symbols": ['MSFT']},
    {"name": "银行", "count": 4, "symbols": ['JPM', '601398', 'HSBA', 'RY']},
    {"name": "零售", "count": 1, "symbols": ['WMT']},
]

def get_market_status(market_id: str) -> dict:
    """计算某市场当前是否在交易时间（v2.4：周末判断 + 跨天区段修正）"""
    now = datetime.now(CST)
    m = next((m for m in MARKETS if m["id"] == market_id), None)
    if not m:
        return {"isOpen": False, "status": "unknown"}

    # 周末休市（周六/周日，按北京时间近似）
    if now.weekday() >= 5:
        return {"isOpen": False, "status": "closed_weekend"}

    hour = now.hour
    # 跨天区段用列表表示 [(start, end), ...]
    market_hours = {
        "cn": [(9, 15)], "hk": [(9, 16)], "jp": [(8, 14)], "kr": [(8, 14)],
        "us": [(21, 24), (0, 5)], "ca": [(21, 24), (0, 5)],
        "uk": [(15, 24), (0, 0)], "de": [(15, 24), (0, 0)],
    }
    if market_id in market_hours:
        for st, en in market_hours[market_id]:
            if st <= hour < en:
                return {"isOpen": True, "status": "open"}
        # 判断是未开盘还是已收盘
        first_open = min(st for st, _ in market_hours[market_id])
        if hour < first_open:
            return {"isOpen": False, "status": "scheduled"}
        return {"isOpen": False, "status": "closed"}
    return {"isOpen": False, "status": "unknown"}

def get_companies(market=None, sector=None, industry=None, search=None):
    """过滤公司列表"""
    result = COMPANIES
    if market:
        result = [c for c in result if c["market"] == market]
    if sector:
        result = [c for c in result if c["sector"] == sector]
    if industry:
        result = [c for c in result if c["industry"] == industry]
    if search:
        s = search.lower()
        result = [c for c in result if s in c["name"].lower() or s in c["nameEn"].lower() or s in c["symbol"].lower()]
    return result

__all__ = ["MARKETS", "COMPANIES", "INDUSTRIES", "get market_status", "get_companies"]
