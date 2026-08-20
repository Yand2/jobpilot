import json
from typing import Any
from utils.json_utils import parse_json_object, require_fields


class ResumeMatcher:

    def __init__(self, client: Any):
        self.client = client

    def match(
        self,
        job_info: dict,
        user_profile: dict
    ) -> dict:

        prompt = f"""
你是 JobPilot 的 Resume Matcher Skill。

你的任务是：

根据招聘岗位要求和用户实际提供的个人信息，
判断用户与岗位之间的匹配程度。

========================
招聘岗位信息
========================

{json.dumps(
    job_info,
    ensure_ascii=False,
    indent=2
)}


========================
用户信息
========================

{json.dumps(
    user_profile,
    ensure_ascii=False,
    indent=2
)}


========================
匹配规则
========================

请严格遵守以下规则：

1. 只能使用用户明确提供的信息。

2. 不允许自行编造用户经历。

3. 不要因为用户的专业名称，
   就推测用户掌握某项技术。

4. 不要因为用户说“对AI感兴趣”，
   就认为用户拥有AI项目经验。

5. 如果用户没有提供某项技能的信息，
   应该判断为“未知”或者“存在缺口”，
   而不是默认用户不会。

6. 区分：
   - strong_match：明确匹配
   - partial_match：有一定相关性
   - gap：岗位要求但用户没有体现
   - unknown：无法根据现有信息判断

7. 匹配度必须基于实际信息。

8. 不要为了提高匹配度而美化用户经历。

9. 按以下权重评分，四项得分相加必须等于match_score：
   - core_requirements：核心岗位要求，满分40
   - relevant_experience：相关经历与成果，满分30
   - skills_tools：技能与工具，满分20
   - bonus_items：加分项，满分10


========================
输出格式
========================

只返回合法 JSON。

不要输出 Markdown。

不要使用 ```json。

不要输出 JSON 之外的解释。


JSON格式：

{{
    "match_score": 0,

    "score_breakdown": {{
        "core_requirements": 0,
        "relevant_experience": 0,
        "skills_tools": 0,
        "bonus_items": 0
    }},

    "strong_matches": [
        {{
            "requirement": "",
            "evidence": "",
            "reason": ""
        }}
    ],

    "partial_matches": [
        {{
            "requirement": "",
            "evidence": "",
            "reason": ""
        }}
    ],

    "gaps": [
        {{
            "requirement": "",
            "reason": ""
        }}
    ],

    "unknowns": [
        {{
            "requirement": "",
            "reason": ""
        }}
    ],

    "keyword_gaps": [],

    "summary": "",

    "priority_actions": [],

    "improvement_suggestions": []
}}


========================
字段说明
========================

match_score：

0-100的整数。

strong_matches：

用户已经有明确经历或能力，
并且与岗位要求直接匹配的地方。

evidence：

必须引用用户明确提供的信息。

partial_matches：

用户经历与岗位要求有一定关联，
但是不能完全证明已经具备该能力。

gaps：

岗位明确要求，
但用户目前没有提供相关经历或能力。

unknowns：

JD需要某项能力，
但是根据用户当前信息无法判断。

summary：

用简洁语言总结用户与岗位的整体匹配情况。

priority_actions：

为了提高这个岗位的竞争力，
用户最应该优先采取的行动。

例如：

- 补充SQL项目
- 制作AI Agent项目
- 在简历中量化Power BI项目成果

keyword_gaps：

JD中重要但用户材料没有明确体现的关键词。只列JD真实出现的词。

improvement_suggestions：

基于现有真实经历给出可执行的简历修改方向，不得补写虚构经历或数据。
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
            "Resume Matcher"
        )
        require_fields(
            result,
            (
                "match_score", "strong_matches", "partial_matches", "gaps",
                "unknowns", "keyword_gaps", "summary", "priority_actions",
                "improvement_suggestions", "score_breakdown"
            ),
            "Resume Matcher"
        )
        score = result["match_score"]
        if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
            raise ValueError("Resume Matcher的match_score必须是0-100的整数。")
        breakdown = result["score_breakdown"]
        limits = {
            "core_requirements": 40,
            "relevant_experience": 30,
            "skills_tools": 20,
            "bonus_items": 10,
        }
        if not isinstance(breakdown, dict):
            raise ValueError("Resume Matcher的score_breakdown必须是JSON对象。")
        for key, limit in limits.items():
            value = breakdown.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= limit:
                raise ValueError(f"score_breakdown.{key}必须是0-{limit}的整数。")
        if sum(breakdown[key] for key in limits) != score:
            raise ValueError("match_score必须等于score_breakdown四项之和。")
        return result
