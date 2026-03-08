"""
AI 公告分析服务

调用 OpenAI 兼容 API，对招考公告内容进行摘要和关键信息提取。
支持 OpenAI / DeepSeek / Moonshot / 通义千问等兼容接口。
"""
import re
import httpx
from typing import Optional

from app.utils.logging import get_logger

logger = get_logger(__name__)

DEFAULT_PROMPT = """你是一个公务员考试信息分析助手。请根据以下招考公告内容，提取并整理关键信息。

请按以下格式输出：

## 基本信息
- **招录单位**：
- **招录人数**：
- **考试类型**：
- **地区**：

## 重要时间
- **发布日期**：
- **报名时间**：
- **考试时间**：
- **缴费截止**：

## 报考条件
（列出主要报考条件，如学历、年龄、专业等）

## 考试内容
（笔试科目、面试形式等）

## 注意事项
（重要提醒，如报名网址、咨询电话等）

## 一句话总结
（用一句话概括这个公告的核心内容）

---
以下是公告原文：

{content}"""


def _strip_html(html: str) -> str:
    """去除 HTML 标签，保留纯文本。"""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


async def analyze_content(
    content: str,
    model: str,
    api_key: str,
    base_url: str,
    prompt_template: Optional[str] = None,
    title: Optional[str] = None,
) -> Optional[str]:
    """
    调用 LLM 分析公告内容。

    Args:
        content: 公告 HTML 内容
        model: 模型名称 (如 gpt-4o-mini, deepseek-chat)
        api_key: API Key
        base_url: API 基础 URL (如 https://api.openai.com/v1)
        prompt_template: 提示词模板，{content} 为占位符
        title: 公告标题（可选，补充上下文）

    Returns:
        AI 分析结果文本，失败返回 None
    """
    if not content or not api_key or not model:
        return None

    # 去除 HTML 标签
    plain_text = _strip_html(content)
    if len(plain_text) < 20:
        logger.warning("ai_analyzer.content_too_short", length=len(plain_text))
        return None

    # 截断过长内容（保留前 8000 字）
    if len(plain_text) > 8000:
        plain_text = plain_text[:8000] + "\n...(内容过长已截断)"

    # 构建提示词
    template = prompt_template or DEFAULT_PROMPT
    if title:
        plain_text = f"标题：{title}\n\n{plain_text}"
    user_message = template.replace("{content}", plain_text)

    # 确保 base_url 格式正确
    base_url = base_url.rstrip("/")
    if not base_url.endswith("/v1"):
        base_url = f"{base_url}/v1"
    url = f"{base_url}/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": user_message}],
        "temperature": 0.3,
        "max_tokens": 2000,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        result = data["choices"][0]["message"]["content"].strip()
        logger.info(
            "ai_analyzer.success",
            model=model,
            input_len=len(plain_text),
            output_len=len(result),
        )
        return result

    except httpx.HTTPStatusError as exc:
        logger.error(
            "ai_analyzer.api_error",
            status=exc.response.status_code,
            body=exc.response.text[:500],
        )
        return None
    except Exception as exc:
        logger.error("ai_analyzer.error", error=str(exc))
        return None
