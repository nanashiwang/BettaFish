"""预判卡生成：把真实信号数据交给 LLM 产出当日 Top3 预判卡与头条判断。"""

from __future__ import annotations

import json
from datetime import date
from typing import Any, Dict, List

from sqlalchemy import text

from SentimentRadar.db import get_engine
from SentimentRadar.pipeline.llm import invoke_json

_SYSTEM = (
    "你是 A 股舆情雷达的证据归因分析师。基于给定的真实信号数据（舆情热度、板块行情、关联新闻）"
    "撰写预判卡。要求：客观克制、只描述舆情与价格的observable事实、证据链与风险，"
    "禁止使用'买入/卖出/加仓/目标价'等投资建议词汇。"
    "任何上涨/异动原因都必须来自给定新闻、政策、公告、行情或个股证据；没有来源就写'证据不足/疑似驱动'。只输出 JSON。"
)

_USER_TEMPLATE = """今日日期：{today}

以下是今日筛选出的 {count} 个舆情-价格信号（数据均为真实计算结果）：

{signals_text}

场景说明：
- 先闻后动：舆情热度已起、板块价格尚未明显反应，存在关注窗口，但需警惕消息有效性
- 同步共振：舆情与板块价格同步走强，主线确认但需警惕过热
- 先动后闻：板块价格先动、舆情后起，存在消息兑现/出货风险，定调必须是警惕提醒

任务：为每个信号生成一张预判卡，并给出一句话当日头条（headline，60 字内，概括今日主线与最大风险）。

输出 JSON 格式：
{{
  "headline": "...",
  "cards": [
    {{
      "signal_index": 1,
      "title": "12 字内标题",
      "judgement": "一句话核心判断（40 字内）",
      "reason": "依据（50 字内，引用热度与行情数据）",
      "risk": "风险（40 字内）",
      "next": "后续观察点（40 字内）",
      "tags": ["话题词", "场景", "板块"],
      "detail": {{
        "summary": "80 字内综合解读",
        "causal_summary": "为什么动：必须基于真实来源的一句话归因；证据不足时明确写疑似驱动",
        "confidence": "中等偏高/中等/证据不足",
        "causal_chain": [
          {{"step": "真实事件", "text": "引用给定来源中的真实新闻/政策/公告，不得编造"}},
          {{"step": "产业映射", "text": "说明事件如何映射到给定真实板块/产业链"}},
          {{"step": "行情验证", "text": "引用热度z、价格z、量比或个股证据验证"}},
          {{"step": "反证提醒", "text": "说明仍需哪些公告/价格/业务占比反证"}}
        ],
        "evidence_basis": [
          {{"source": "来源名", "title": "必须来自给定新闻列表的标题", "url": "原始URL或空", "type": "新闻报道/政策监管/公司公告/行情验证/产业数据", "credibility": "高/较高/中/中低", "note": "为什么采用"}}
        ],
        "counter_evidence": ["反证或失效条件；若未捕捉到反证，说明需要继续观察什么"],
        "why": ["判断依据 1", "判断依据 2", "判断依据 3"],
        "timeline": [{{"time": "今日", "label": "舆情信号", "text": "..."}}],
        "evidence_chain": [{{"source": "来源名", "count": 1, "credibility": "高/较高/中/中低", "note": "说明"}}],
        "risk_boundary": ["该判断失效的条件 1", "条件 2"],
        "next_watch": ["观察点 1", "观察点 2"]
      }}
    }}
  ]
}}

注意：
- evidence_basis 的 title/source/url 必须来自给定的新闻证据列表，禁止杜撰来源。
- causal_summary 必须区分“事实”和“推断”，证据不足只能写“疑似驱动”。
- evidence_chain 的来源与数量必须基于给到的真实新闻来源统计；timeline 基于真实信息，不要编造具体时刻。"""

_SOURCE_CREDIBILITY = {
    "财联社": "较高",
    "华尔街见闻": "较高",
    "澎湃新闻": "中",
    "雪球热榜": "中",
    "今日头条": "中",
    "微博热搜": "中低",
    "知乎热榜": "中低",
    "抖音热榜": "中低",
    "百度贴吧": "中低",
}

_POLICY_WORDS = ("政策", "监管", "商务部", "工信部", "发改委", "海关", "限制", "制裁", "出口", "进口", "关税")
_PRICE_WORDS = ("涨价", "价格", "报价", "供给", "短缺", "库存", "产能", "原料", "稀土", "金属", "材料")
_DISCLOSURE_WORDS = ("公告", "澄清", "互动平台", "投资者", "订单", "合同", "业绩")


def _evidence_type(item: Dict[str, Any]) -> str:
    title = str(item.get("title") or "")
    if any(word in title for word in _POLICY_WORDS):
        return "政策监管"
    if any(word in title for word in _DISCLOSURE_WORDS):
        return "公司公告"
    if any(word in title for word in _PRICE_WORDS):
        return "产业数据"
    return "新闻报道"


def _evidence_docs(signal: Dict[str, Any], news: List[Dict[str, Any]], limit: int = 6) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for news_index in signal["topic"].get("news_indexes", [])[:limit]:
        if not isinstance(news_index, int) or news_index < 1 or news_index > len(news):
            continue
        item = news[news_index - 1]
        docs.append({
            "id": news_index,
            "source": item.get("source_name") or item.get("source") or "未知来源",
            "title": item.get("title") or "",
            "url": item.get("url") or "",
            "type": _evidence_type(item),
            "credibility": _SOURCE_CREDIBILITY.get(item.get("source_name"), "中"),
            "note": "来自当日真实热榜/新闻源，被话题聚合采用",
        })
    return docs


def _confidence_from_docs(docs: List[Dict[str, Any]]) -> str:
    if not docs:
        return "证据不足"
    if len(docs) >= 2 and any(doc.get("credibility") in {"高", "较高"} for doc in docs):
        return "中等偏高"
    return "中等"


def _normalize_causal_detail(
    detail: Dict[str, Any],
    signal: Dict[str, Any],
    news: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """补齐证据归因结构，确保所有归因至少绑定真实新闻或行情证据。"""
    topic = signal["topic"]
    board = signal["board"]
    metrics = signal["metrics"]
    stocks = signal.get("stock_candidates") or []
    docs = _evidence_docs(signal, news)

    evidence_basis = detail.get("evidence_basis")
    if not isinstance(evidence_basis, list) or not evidence_basis:
        evidence_basis = docs[:4]
    else:
        # 只保留能匹配到真实来源标题的证据，避免 LLM 杜撰。
        allowed = {(doc["source"], doc["title"]): doc for doc in docs}
        normalized_basis: List[Dict[str, Any]] = []
        for item in evidence_basis:
            doc = allowed.get((item.get("source"), item.get("title")))
            if not doc:
                continue
            real_doc = dict(doc)
            if item.get("note"):
                real_doc["note"] = str(item.get("note"))[:120]
            normalized_basis.append(real_doc)
        evidence_basis = normalized_basis[:6] or docs[:4]

    confidence = "证据不足" if not evidence_basis else (detail.get("confidence") or _confidence_from_docs(evidence_basis))
    lead = evidence_basis[0] if evidence_basis else None
    causal_summary = str(detail.get("causal_summary") or "").strip()
    if lead:
        if not causal_summary:
            causal_summary = (
                f"基于{lead['source']}《{lead['title'][:28]}》等真实来源，"
                f"市场正在验证「{topic['name']}」对{board['name']}的影响。"
            )
    else:
        causal_summary = f"当前缺少可追溯新闻/政策来源，仅能把「{topic['name']}」标记为疑似驱动。"

    causal_chain = detail.get("causal_chain")
    if not isinstance(causal_chain, list) or not causal_chain:
        causal_chain = [
            {
                "step": "真实事件",
                "text": (
                    f"已捕捉到{lead['source']}《{lead['title']}》。"
                    if lead else "当前未捕捉到足够高可信新闻/政策原文。"
                ),
            },
            {
                "step": "产业映射",
                "text": f"该话题经板块约束映射到真实板块「{board['name']}」，不是模型自由编造板块。",
            },
            {
                "step": "行情验证",
                "text": (
                    f"热度z={topic.get('heat_z')}，近3日板块涨幅{metrics.get('return_3d')}%，"
                    f"价格z={metrics.get('price_z')}，量比{metrics.get('volume_ratio')}。"
                ),
            },
            {
                "step": "个股映射",
                "text": f"观察池覆盖{len(stocks)}只个股，需继续核验公司公告、业务占比与资金扩散。",
            },
        ]

    counter_evidence = detail.get("counter_evidence")
    if not isinstance(counter_evidence, list) or not counter_evidence:
        counter_evidence = [
            "若后续公司公告澄清业务占比低，需下调驱动可信度。",
            "若只有个股上涨但板块量价不扩散，可能只是短线题材交易。",
            "若新闻为旧消息重复传播或缺少权威来源，归因应降级为疑似驱动。",
        ]

    detail["causal_summary"] = causal_summary[:240]
    detail["confidence"] = confidence
    detail["causal_chain"] = causal_chain[:6]
    detail["evidence_basis"] = evidence_basis[:6]
    detail["counter_evidence"] = counter_evidence[:6]
    return detail


def _fmt_num(value: Any, suffix: str = "", default: str = "-") -> str:
    if value is None or value == "":
        return default
    try:
        num = float(value)
    except (TypeError, ValueError):
        return default
    return f"{num:+.2f}{suffix}" if suffix == "%" else f"{num:.2f}{suffix}"


def _fmt_amount(value: Any) -> str:
    if value is None or value == "":
        return "-"
    try:
        num = float(value)
    except (TypeError, ValueError):
        return "-"
    if abs(num) >= 10000:
        return f"{num / 10000:+.2f}亿"
    return f"{num:+.0f}万"


def _stock_line(item: Dict[str, Any]) -> str:
    profile = item.get("company_profile") or {}
    financial = item.get("financial") or {}
    quote = item.get("quote_metrics") or {}
    announcements = item.get("announcements") or []
    money_flow = item.get("money_flow") or {}
    board_flow = item.get("board_money_flow") or {}

    parts = [
        f"{item['name']}({item['code']}) {item['label']}",
        f"3日{_fmt_num(item.get('return_3d'), '%')}",
        f"量比{_fmt_num(item.get('volume_ratio'))}",
    ]
    if quote:
        parts.append(
            f"换手{_fmt_num(quote.get('turnover_rate'), '%')} PE{_fmt_num(quote.get('pe'))}"
        )
    if profile:
        parts.append(
            f"{profile.get('soe_tag') or '股权待核验'} {profile.get('industry') or ''}".strip()
        )
    if financial:
        parts.append(
            f"营收{_fmt_num(financial.get('revenue_yoy'), '%')} 净利{_fmt_num(financial.get('profit_yoy'), '%')} ROE{_fmt_num(financial.get('roe'), '%')}"
        )
    if announcements:
        latest = announcements[0]
        parts.append(f"公告[{latest.get('type')}] {str(latest.get('title') or '')[:28]}")
    if money_flow:
        parts.append(
            f"个股资金{_fmt_amount(money_flow.get('net_mf_amount'))} 占比{_fmt_num(money_flow.get('net_mf_ratio'), '%')}"
        )
    if board_flow:
        parts.append(f"板块资金{_fmt_amount(board_flow.get('net_mf_amount'))}")
    return " / ".join(part for part in parts if part and part != "-")


def _stock_evidence_summary(stocks: List[Dict[str, Any]]) -> str:
    if not stocks:
        return "个股证据 0 项"
    return (
        f"行情增强 {sum(1 for s in stocks if s.get('quote_metrics'))} / "
        f"基础资料 {sum(1 for s in stocks if s.get('company_profile'))} / "
        f"财务 {sum(1 for s in stocks if s.get('financial'))} / "
        f"公告 {sum(len(s.get('announcements') or []) for s in stocks)} / "
        f"资金流 {sum(1 for s in stocks if s.get('money_flow'))}"
    )


def _signal_text(index: int, signal: Dict[str, Any], news: List[Dict[str, Any]]) -> str:
    topic = signal["topic"]
    board = signal["board"]
    metrics = signal["metrics"]
    stocks = signal.get("stock_candidates") or []
    titles = []
    source_counts: Dict[str, int] = {}
    for news_index in topic["news_indexes"][:8]:
        item = news[news_index - 1]
        titles.append(
            f"  - 证据#{news_index} [{item['source_name']}] {item['title']} | URL:{item.get('url') or ''}"
        )
    for news_index in topic["news_indexes"]:
        name = news[news_index - 1]["source_name"]
        source_counts[name] = source_counts.get(name, 0) + 1
    sources = "、".join(f"{name}{count}条" for name, count in source_counts.items())
    stock_text = "暂无"
    if stocks:
        stock_text = "；".join(_stock_line(item) for item in stocks[:6])
    return (
        f"信号 {index}：{topic['name']}（场景：{signal['scenario']}，强度：{signal['strength']}）\n"
        f"- 舆情：热度分 {topic['heat_score']}（z={topic['heat_z']}），覆盖来源：{sources}\n"
        f"- 板块：{board['name']}（{board['type']}），近 3 日涨幅 {metrics['return_3d']}%"
        f"（z={metrics['price_z']}），量比 {metrics['volume_ratio']}\n"
        f"- 个股观察池：{stock_text}\n"
        f"- 个股证据覆盖：{_stock_evidence_summary(stocks)}\n"
        f"- 关联热榜：\n" + "\n".join(titles)
    )


def generate_cards(
    trade_date: date,
    signals: List[Dict[str, Any]],
    news: List[Dict[str, Any]],
    model: str,
) -> List[Dict[str, Any]]:
    """LLM 生成预判卡并落库，返回卡片记录。"""
    top = signals[:3]
    signals_text = "\n\n".join(_signal_text(i + 1, s, news) for i, s in enumerate(top))
    result = invoke_json(
        _SYSTEM,
        _USER_TEMPLATE.format(today=trade_date.isoformat(), count=len(top), signals_text=signals_text),
        model=model,
        max_tokens=4000,
    )
    headline = str(result.get("headline") or "").strip()[:300]
    cards = []
    for rank, card in enumerate(result.get("cards", [])[: len(top)], start=1):
        signal = top[(card.get("signal_index") or rank) - 1]
        topic = signal["topic"]
        news_count = len(topic["news_indexes"])
        detail = card.get("detail") or {}
        detail = _normalize_causal_detail(detail, signal, news)
        detail["stock_candidates"] = signal.get("stock_candidates", [])
        record = {
            "trade_date": trade_date,
            "rank": rank,
            "card_id": f"{trade_date.strftime('%Y%m%d')}-{rank}",
            "scenario": signal["scenario"],
            "strength": signal["strength"],
            "title": str(card.get("title") or topic["name"])[:200],
            "judgement": str(card.get("judgement") or ""),
            "reason": str(card.get("reason") or ""),
            "risk": str(card.get("risk") or ""),
            "next_watch": str(card.get("next") or ""),
            "tags": (card.get("tags") or [topic["name"], signal["scenario"]])[:4],
            "evidence_summary": (
                f"热榜 {news_count} 条 / 热度z {topic['heat_z']} / "
                f"价格z {signal['metrics']['price_z']} / {_stock_evidence_summary(signal.get('stock_candidates', []))}"
            ),
            "detail": detail,
            "boards": signal["all_boards"],
            "stock_candidates": signal.get("stock_candidates", []),
            "heat_z": topic["heat_z"],
            "price_z": signal["metrics"]["price_z"],
            "headline": headline,
        }
        cards.append(record)

    with get_engine().begin() as conn:
        conn.execute(text("DELETE FROM radar_predictions WHERE trade_date = :d"), {"d": trade_date})
        for record in cards:
            conn.execute(
                text(
                    """
                    INSERT INTO radar_predictions
                        (trade_date, rank, card_id, scenario, strength, title, judgement, reason,
                         risk, next_watch, tags, evidence_summary, detail, boards, stock_candidates,
                         heat_z, price_z, headline)
                    VALUES
                        (:trade_date, :rank, :card_id, :scenario, :strength, :title, :judgement, :reason,
                         :risk, :next_watch, CAST(:tags AS JSONB), :evidence_summary, CAST(:detail AS JSONB),
                         CAST(:boards AS JSONB), CAST(:stock_candidates AS JSONB), :heat_z, :price_z, :headline)
                    """
                ),
                {
                    **record,
                    "tags": json.dumps(record["tags"], ensure_ascii=False),
                    "detail": json.dumps(record["detail"], ensure_ascii=False),
                    "boards": json.dumps(record["boards"], ensure_ascii=False),
                    "stock_candidates": json.dumps(record["stock_candidates"], ensure_ascii=False),
                },
            )
    return cards
