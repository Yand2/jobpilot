import json
from utils.json_utils import parse_json_object, require_fields


class IntentRouter:

    def __init__(self, client):

        self.client = client

    def route(self, user_message):

        prompt = f"""
你是 JobPilot 的任务路由器。

你的任务是判断用户当前想让求职 Agent 做什么。

用户说：

{user_message}

请从以下任务中选择一个：

1. analyze_jd
用户想分析招聘 JD、岗位职责、岗位要求。

2. match_resume
用户想知道自己的经历是否符合某个岗位。

3. full_analysis
用户想知道一个岗位是否适合自己，
需要同时分析 JD 和用户匹配程度。

4. update_profile
用户正在提供自己的个人信息、
专业、学历、经历、技能等。

5. general_chat
无法归类到以上任务。

只返回 JSON：

{{
    "intent": "",
    "reason": ""
}}

要求：

1. intent 必须是上面五个选项之一。
2. 不要编造用户没有说的信息。
3. 只返回合法 JSON。
4. 不要输出 Markdown。
"""

        response = self.client.chat.completions.create(

            model="deepseek-chat",

            messages=[

                {
                    "role": "system",
                    "content": "你是一个严格的任务分类器。"
                },

                {
                    "role": "user",
                    "content": prompt
                }

            ],

            temperature=0

        )

        result = parse_json_object(
            response.choices[0].message.content,
            "Router"
        )
        require_fields(result, ("intent", "reason"), "Router")
        allowed = {
            "analyze_jd", "match_resume", "full_analysis",
            "update_profile", "general_chat"
        }
        if result["intent"] not in allowed:
            raise ValueError(f"Router返回了未知意图：{result['intent']}")
        return result
