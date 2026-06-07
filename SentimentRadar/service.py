"""极简预判版舆情雷达数据服务。

当前先提供可运行的 Mock 数据和稳定 API 结构，后续可替换为真实采集、
行情、舆情评分和 Agent 解析结果。
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


TODAY_CARDS = [
    {
        "id": "ai-compute",
        "rank": 1,
        "title": "AI 算力持续升温",
        "scenario": "同步共振",
        "strength": "高",
        "judgement": "AI 算力为今日市场最强主线，资金关注度高。",
        "reason": "大模型迭代、算力需求增长与产业链催化同时出现。",
        "risk": "部分个股涨幅较大，短期分歧或波动加剧。",
        "next": "关注订单/业绩兑现、龙头动向、资金持续性。",
        "evidence": "新闻 18 条 / 公告 2 条 / 社媒 260 条",
        "tags": ["AI 算力", "半导体", "同步共振"],
    },
    {
        "id": "semi-cycle",
        "rank": 2,
        "title": "半导体景气延续",
        "scenario": "先闻后动",
        "strength": "中-高",
        "judgement": "产业新闻先出现，板块随后扩散，仍在验证阶段。",
        "reason": "库存周期改善、国产替代加速与政策支持延续。",
        "risk": "海外不确定性、周期波动、个股业绩分化。",
        "next": "关注产能利用率、价格趋势、出口数据。",
        "evidence": "新闻 12 条 / 研报 9 条 / 社媒 142 条",
        "tags": ["半导体", "先闻后动", "景气周期"],
    },
    {
        "id": "cash-out-risk",
        "rank": 3,
        "title": "先动后闻需警惕",
        "scenario": "先动后闻",
        "strength": "中",
        "judgement": "部分个股先涨后发消息，存在消息兑现风险。",
        "reason": "价格和成交早于新闻扩散，新闻出现后分歧加大。",
        "risk": "消息不及预期、估值回落、资金快速撤离。",
        "next": "跟踪消息真实性、业绩影响、资金流向。",
        "evidence": "新闻 7 条 / 股吧 96 条 / 价格异动 4 条",
        "tags": ["先动后闻", "兑现风险", "风险边界"],
    },
]


DETAILS = {
    "ai-compute": {
        "title": "AI 算力持续升温",
        "scenario": "同步共振",
        "summary": "新闻、舆情、板块表现和部分个股热度同步增强，说明市场主线仍集中在算力方向。",
        "why": [
            "政策端继续强调算力基础设施建设。",
            "产业端出现新增订单与云服务扩容讨论。",
            "舆情端多个平台同时升温，且关联股票数量增加。",
        ],
        "timeline": [
            {"time": "09:10", "label": "新闻出现", "text": "产业媒体发布算力扩容相关报道"},
            {"time": "09:45", "label": "舆情升温", "text": "AI 算力话题进入多平台热议"},
            {"time": "10:20", "label": "板块联动", "text": "半导体、服务器、光模块相关个股同步活跃"},
            {"time": "13:30", "label": "分歧出现", "text": "高位个股讨论转向兑现与持续性"},
        ],
        "evidence_chain": [
            {"source": "新闻媒体", "count": 18, "credibility": "较高", "note": "多家产业媒体集中报道"},
            {"source": "公司公告", "count": 2, "credibility": "高", "note": "涉及订单与产能披露"},
            {"source": "社交媒体", "count": 260, "credibility": "中", "note": "讨论量高但观点分化"},
            {"source": "股吧论坛", "count": 96, "credibility": "中低", "note": "情绪偏热，需过滤噪声"},
        ],
        "risk_boundary": [
            "短期热度过高，可能出现分歧放大。",
            "部分个股基本面兑现速度可能低于舆情预期。",
            "若后续无公告或订单证据补充，热度可能回落。",
        ],
        "next_watch": [
            "是否继续出现权威来源和公告证据。",
            "板块内是否仍有多只个股同步活跃。",
            "高热个股是否出现明显放量分歧。",
        ],
    },
    "semi-cycle": {
        "title": "半导体景气延续",
        "scenario": "先闻后动",
        "summary": "产业新闻先于板块热度出现，市场正在验证半导体周期改善的持续性。",
        "why": [
            "库存周期改善相关内容先于盘中扩散。",
            "国产替代与设备更新形成主题支撑。",
            "板块内部扩散较温和，尚未出现极端过热。",
        ],
        "timeline": [
            {"time": "08:40", "label": "产业新闻", "text": "多篇库存改善与设备需求报道发布"},
            {"time": "10:05", "label": "板块跟随", "text": "设备、材料、设计相关方向升温"},
            {"time": "11:20", "label": "舆情扩散", "text": "社媒开始讨论国产替代和景气周期"},
        ],
        "evidence_chain": [
            {"source": "产业新闻", "count": 12, "credibility": "较高", "note": "集中讨论库存周期"},
            {"source": "机构观点", "count": 9, "credibility": "中高", "note": "观点偏审慎乐观"},
            {"source": "社交媒体", "count": 142, "credibility": "中", "note": "扩散尚未极端"},
        ],
        "risk_boundary": [
            "周期改善仍需业绩数据验证。",
            "海外不确定性可能影响情绪。",
            "板块内公司分化较大。",
        ],
        "next_watch": [
            "观察订单和产能利用率数据。",
            "关注板块联动是否扩大。",
            "跟踪头部公司公告与业绩预告。",
        ],
    },
    "cash-out-risk": {
        "title": "先动后闻需警惕",
        "scenario": "先动后闻",
        "summary": "部分个股在新闻扩散前已经出现价格和关注度变化，新闻出现后可能进入验证或兑现阶段。",
        "why": [
            "价格/成交异动早于新闻传播。",
            "新闻发布后，社媒情绪快速升温但分歧明显。",
            "部分来源可信度不足，存在小作文传播特征。",
        ],
        "timeline": [
            {"time": "09:35", "label": "价格异动", "text": "相关个股成交与关注度先行变化"},
            {"time": "10:50", "label": "消息扩散", "text": "社媒出现订单与合作传闻"},
            {"time": "13:15", "label": "新闻跟进", "text": "财经媒体开始转载相关内容"},
            {"time": "14:20", "label": "风险升高", "text": "讨论转向真实性与兑现风险"},
        ],
        "evidence_chain": [
            {"source": "行情异动", "count": 4, "credibility": "高", "note": "时间早于新闻扩散"},
            {"source": "社媒转发", "count": 180, "credibility": "中低", "note": "信息源头不稳定"},
            {"source": "财经新闻", "count": 7, "credibility": "中", "note": "多为跟进转载"},
            {"source": "公司公告", "count": 0, "credibility": "待验证", "note": "暂无公告佐证"},
        ],
        "risk_boundary": [
            "消息兑现风险较高。",
            "若没有公告佐证，后续分歧可能放大。",
            "高位放量时需重点观察资金行为变化。",
        ],
        "next_watch": [
            "是否出现公司公告或权威媒体确认。",
            "资金是否继续净流入。",
            "相关板块是否同步扩散，而不是单一个股独立波动。",
        ],
    },
}


SETTINGS = {
    "focus_targets": {
        "stocks": ["寒武纪", "中科曙光", "宁德时代"],
        "themes": ["AI 算力", "半导体", "固态电池"],
        "sectors": ["计算机设备", "电子", "新能源"],
    },
    "push_templates": [
        {"id": "morning", "name": "早间 3 条", "enabled": True, "time": "08:30"},
        {"id": "noon", "name": "午间变化", "enabled": True, "time": "11:45"},
        {"id": "close", "name": "收盘复盘", "enabled": True, "time": "15:30"},
        {"id": "risk", "name": "高风险即时提醒", "enabled": True, "time": "实时"},
    ],
    "risk_preferences": ["消息兑现风险", "过热风险", "来源不明", "负面扩散"],
    "channels": ["站内信", "邮件", "企业微信"],
}


def get_today_briefing() -> Dict[str, Any]:
    return {
        "success": True,
        "updated_at": _timestamp(),
        "product": "A 股舆情雷达",
        "version": "极简预判版",
        "disclaimer": "仅供舆情观察 · 不构成投资建议",
        "headline": "今日主线偏向 AI 算力与半导体，但部分个股出现先动后闻，需警惕消息兑现风险。",
        "cards": deepcopy(TODAY_CARDS),
        "my_related": {
            "summary": "我的关注命中 4 条",
            "highlight": "寒武纪相关舆情升温，属于“同步共振”，但短期讨论过热。",
            "items": [
                {"label": "自选股舆情", "value": "3 条预警"},
                {"label": "持仓舆情", "value": "2 条关注"},
                {"label": "关注主题", "value": "AI 算力"},
            ],
        },
        "top_risk": {
            "title": "今日最高风险：消息兑现风险",
            "level": "高",
            "scope": "AI 算力、半导体部分个股",
            "reason": "价格提前反应，新闻密集出现，短期分歧加大。",
        },
        "evidence_overview": [
            {"name": "新闻媒体", "count": 1286},
            {"name": "公告研报", "count": 312},
            {"name": "社交媒体", "count": 2457},
            {"name": "机构观点", "count": 89},
            {"name": "其他来源", "count": 631},
        ],
    }


def get_prediction_detail(card_id: str) -> Dict[str, Any]:
    detail = DETAILS.get(card_id)
    if not detail:
        return {"success": False, "message": "未找到对应预判解析"}
    return {
        "success": True,
        "id": card_id,
        "updated_at": _timestamp(),
        "disclaimer": "仅供舆情观察 · 不构成投资建议",
        "detail": deepcopy(detail),
    }


def get_my_focus() -> Dict[str, Any]:
    return {
        "success": True,
        "updated_at": _timestamp(),
        "disclaimer": "仅供舆情观察 · 不构成投资建议",
        "hits": [
            {
                "name": "寒武纪",
                "type": "股票",
                "match": "AI 算力主线",
                "scenario": "同步共振",
                "risk": "讨论过热",
                "next": "观察公告或订单证据补充",
            },
            {
                "name": "半导体",
                "type": "板块",
                "match": "景气周期延续",
                "scenario": "先闻后动",
                "risk": "业绩分化",
                "next": "观察产业数据与头部公司披露",
            },
            {
                "name": "固态电池",
                "type": "主题",
                "match": "午后讨论升温",
                "scenario": "闻而不动",
                "risk": "市场反馈有限",
                "next": "观察是否扩散到板块联动",
            },
        ],
        "settings": deepcopy(SETTINGS),
    }


def get_settings() -> Dict[str, Any]:
    return {
        "success": True,
        "updated_at": _timestamp(),
        "settings": deepcopy(SETTINGS),
    }


def update_settings(payload: Dict[str, Any]) -> Dict[str, Any]:
    # 原型阶段仅回显前端提交内容，不写入磁盘，避免误改用户配置。
    merged = deepcopy(SETTINGS)
    if isinstance(payload, dict):
        for key in ("focus_targets", "push_templates", "risk_preferences", "channels"):
            if key in payload:
                merged[key] = payload[key]
    return {
        "success": True,
        "message": "设置已保存（原型内存态）",
        "updated_at": _timestamp(),
        "settings": merged,
    }
