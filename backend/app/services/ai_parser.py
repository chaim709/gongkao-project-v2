"""AI 题目解析服务 - 使用 Claude API 从文档中提取题目"""
import json
import re
from typing import Optional
from app.config import settings
from app.services.knowledge_tags import KNOWLEDGE_TAGS, get_all_flat_tags


PARSE_PROMPT = """你是一位专业的公务员考试题库录入专家。请从以下文档内容中提取所有题目，并按JSON格式返回。

**要求**：
1. 识别每道题的题号、题干、选项（A/B/C/D）、正确答案
2. 如果有解析，也提取出来
3. 根据题目内容智能分类：
   - category（一级分类）：言语理解与表达、判断推理、数量关系、资料分析、常识判断 等
   - subcategory（二级分类）：如 主旨概括、逻辑判断、工程问题 等
   - knowledge_point（知识点）：更细的知识点
4. 判断难度：easy/medium/hard
5. 如果题目包含图形/图片描述，标记 is_image_question 为 true

**可用的分类体系**：
{tags}

**返回格式**（严格JSON，不要markdown代码块标记）：
{{
  "subject": "行测",
  "questions": [
    {{
      "question_number": 1,
      "question_type": "single_choice",
      "stem": "题干内容",
      "option_a": "选项A内容",
      "option_b": "选项B内容",
      "option_c": "选项C内容",
      "option_d": "选项D内容",
      "answer": "A",
      "analysis": "解析内容（如有）",
      "category": "言语理解与表达",
      "subcategory": "主旨概括",
      "knowledge_point": "转折关系",
      "difficulty": "medium",
      "key_technique": "解题关键技巧（如有）",
      "common_mistake": "常见错误点（如有）",
      "is_image_question": false,
      "ai_confidence": 0.95
    }}
  ]
}}

**文档内容**：
{content}
"""


async def parse_questions_with_ai(
    content: str,
    subject: Optional[str] = None,
) -> dict:
    """使用 Claude API 解析题目文本"""
    import anthropic

    if not settings.ANTHROPIC_API_KEY:
        raise ValueError("未配置 ANTHROPIC_API_KEY，请在 .env 中设置")

    tags_text = json.dumps(KNOWLEDGE_TAGS, ensure_ascii=False, indent=2)

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    prompt = PARSE_PROMPT.format(tags=tags_text, content=content[:15000])

    message = await client.messages.create(
        model=settings.AI_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    # 提取返回的 JSON
    response_text = message.content[0].text
    # 尝试从 markdown 代码块中提取
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response_text)
    if json_match:
        response_text = json_match.group(1)

    result = json.loads(response_text.strip())

    # 如果指定了科目，覆盖
    if subject:
        result["subject"] = subject

    # 统计分类分布
    summary = {}
    for q in result.get("questions", []):
        cat = q.get("subcategory") or q.get("category") or "未分类"
        summary[cat] = summary.get(cat, 0) + 1

    result["total_questions"] = len(result.get("questions", []))
    result["summary"] = summary

    return result
