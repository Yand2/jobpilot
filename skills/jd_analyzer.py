import json
from typing import Any
from utils.json_utils import parse_json_object, require_fields


class JDAnalyzer:

    def __init__(self, client: Any):
        self.client = client

    def analyze(self, job_description: str) -> dict:

        prompt = f"""
你是 JobPilot 的 JD 分析 Skill。

你的任务是分析一份招聘 JD，
提取岗位信息并返回结构化结果。

招聘 JD：

========================
{job_description}
========================

请严格按照下面的 JSON 格式返回：

{{
    "job_title": "",
    "company": "",
    "job_type": "",
    "responsibilities": [],
    "required_skills": [],
    "bonus_skills": [],
    "experience_level": "",
    "keywords": []
}}

要求：

1. 只返回合法 JSON。
2. 不要输出 JSON 之外的解释。
3. 不要使用 Markdown。
4. 不要使用 ```json。
5. 如果 JD 没有相关信息，使用空字符串或空数组。
6. 不要自行编造 JD 中不存在的信息。

字段说明：

job_title：
岗位名称。

company：
公司名称。

job_type：
岗位类型，例如实习、全职、校招等。

responsibilities：
岗位核心工作内容，提取 3-7 条。

required_skills：
岗位明确要求的核心技能。

bonus_skills：
岗位中的加分技能、优先条件。

experience_level：
岗位要求的经验水平。

keywords：
岗位最重要的关键词。
"""

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2
        )

        result = parse_json_object(
            response.choices[0].message.content,
            "JD Analyzer"
        )
        return require_fields(
            result,
            (
                "job_title", "company", "job_type", "responsibilities",
                "required_skills", "bonus_skills", "experience_level", "keywords"
            ),
            "JD Analyzer"
        )
