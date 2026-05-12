import json
import logging
from datetime import datetime

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    base_url=settings.OPENAI_BASE_URL,
    api_key=settings.OPENAI_API_KEY,
)

async def build_system_prompt(db) -> str:
    """动态构建 AI 提示词，注入当前配置的类型列表和当前年份"""
    from app.utils.config_helper import get_all_configs
    configs = await get_all_configs(db)
    activity_types = "、".join(configs.get("activity_types", ["讲座", "志愿活动", "文体活动", "初赛", "观众招募", "分享会", "其他"]))
    credit_types = "、".join(configs.get("credit_types", ["思想成长", "实践实习", "创新创业", "志愿公益", "文体活动", "技能特长"]))
    current_year = datetime.now().year

    return f"""你是一个校园活动信息提取助手。请从用户提供的公众号推文和群消息中提取以下字段，返回严格 JSON 格式。

⚠️ 当前年份：{current_year} 年。
⚠️ 所有时间都是北京时间（UTC+8），原文写什么时间就输出什么时间，绝对不要做任何时区转换。
⚠️ 原文中"X月X日"或"X月X日（星期X）"形式的日期，一律视为 {current_year} 年。
⚠️ 原文中"上午XX:XX"=XX:XX，"下午XX:XX"=XX:XX（保持24小时制原数字），"晚上XX:XX"=XX:XX。(如果不是24小时制就转换成24小时制)
⚠️ 时间分隔符可能是"—""–""-""～"，它们连接的起止时间中，前半段是开始、后半段是结束。
⚠️ 报名截止时间如果原文没写明具体日期，设为活动开始日期的前一天 12:00（中午）。

字段说明：
- title: 活动标题
- activity_type: 活动类型（{activity_types}）
- start_time: 活动开始时间，ISO8601 格式，如 "{current_year}-11-15T09:00:00"
- end_time: 活动结束时间，ISO8601 格式，如 "{current_year}-11-15T12:00:00"
- location: 活动地点
- credit_type: 学分类型（{credit_types}）
- credit_value: 学分分值，数字（0.0-2.0）
- registration_deadline: 报名截止时间，ISO8601 格式
- max_participants: 最大参与人数，整数
- description: 活动详情描述

每个字段返回格式：{{"value": "提取值", "confidence": "high|medium|low"}}

样例输入：
第十一届应急救护大赛来啦！初赛：11月15日（星期六）上午9:00～12:00，地点：行政广场。报名截止至11月6日。120个名额。

样例输出：
{{
  "title": {{"value": "第十一届应急救护大赛", "confidence": "high"}},
  "activity_type": {{"value": "竞赛", "confidence": "medium"}},
  "start_time": {{"value": "{current_year}-11-15T09:00:00", "confidence": "high"}},
  "end_time": {{"value": "{current_year}-11-15T12:00:00", "confidence": "high"}},
  "location": {{"value": "行政广场", "confidence": "high"}},
  "credit_type": {{"value": "实践实习", "confidence": "medium"}},
  "credit_value": {{"value": 0.2, "confidence": "medium"}},
  "registration_deadline": {{"value": "{current_year}-11-06T12:00:00", "confidence": "high"}},
  "max_participants": {{"value": 120, "confidence": "high"}},
  "description": {{"value": "初赛：11月15日（星期六）上午9:00～12:00，地点：行政广场。", "confidence": "high"}}
}}
"""


async def parse_activity_text(db, article_text: str | None, group_message: str | None) -> dict:
    user_content_parts = []
    if article_text:
        user_content_parts.append(f"公众号推文：\n{article_text}")
    if group_message:
        user_content_parts.append(f"群消息：\n{group_message}")

    system_prompt = await build_system_prompt(db)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "\n\n".join(user_content_parts)},
    ]

    try:
        completion = await client.chat.completions.create(
            model=settings.OPENAI_MODEL_NAME,
            messages=messages,  # type: ignore
            response_format={"type": "json_object"},
            stream=False,
        )
        raw = completion.choices[0].message.content
        logger.info("AI parse_activity_text success, model=%s, raw=%s", settings.OPENAI_MODEL_NAME, raw)
        return json.loads(raw)
    except Exception:
        logger.exception("AI parse_activity_text failed, model=%s", settings.OPENAI_MODEL_NAME)
        raise
