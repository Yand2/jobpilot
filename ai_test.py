import os
import json
from openai import OpenAI


# ==========================================
# 1. 创建 DeepSeek 客户端
# ==========================================

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


# ==========================================
# 2. AI 调用函数
# ==========================================

def ask_ai(prompt):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3
    )

    return response.choices[0].message.content


# ==========================================
# 3. 收集用户信息
# ==========================================

def collect_user_profile():

    print()
    print("========================================")
    print("              JobPilot AI")
    print("========================================")
    print()

    print("你好，我是 JobPilot。")
    print("我可以帮助你分析招聘岗位、")
    print("匹配你的个人经历、发现能力差距，")
    print("并给出求职建议。")
    print()

    print("在开始分析岗位之前，我需要先了解你。")
    print()

    # 专业
    major = input(
        "你的专业是什么？\n"
        "> "
    )

    # 学历
    education = input(
        "\n你的学历和目前年级是什么？\n"
        "例如：本科大四 / 硕士二年级\n"
        "> "
    )

    # 目标岗位
    target_jobs = input(
        "\n你目前主要考虑哪些岗位？\n"
        "例如：AI产品、数据分析、AI应用开发等\n"
        "> "
    )

    # 经历
    experience = input(
        "\n请简单介绍一下你的主要经历。\n"
        "可以包括实习、项目、比赛、校园经历等。\n"
        "> "
    )

    # AI经历
    ai_experience = input(
        "\n你目前有哪些 AI 相关经验？\n"
        "如果没有，可以直接输入“暂无”。\n"
        "> "
    )

    return {
        "major": major,
        "education": education,
        "target_jobs": target_jobs,
        "experience": experience,
        "ai_experience": ai_experience
    }


# ==========================================
# 4. 分析招聘 JD
# ==========================================

def analyze_job(job_description, user_profile):

    prompt = f"""
你是 JobPilot，一名专业的 AI 求职助手。

你的任务是：

1. 分析招聘岗位 JD
2. 提取岗位结构化信息
3. 结合用户背景进行匹配分析
4. 找出用户与岗位之间的能力差距
5. 给出具体求职建议


========================
用户信息
========================

专业：
{user_profile["major"]}

学历与年级：
{user_profile["education"]}

目标岗位：
{user_profile["target_jobs"]}

主要经历：
{user_profile["experience"]}

AI相关经验：
{user_profile["ai_experience"]}


========================
招聘 JD
========================

{job_description}


========================
输出要求
========================

请严格按照下面的 JSON 格式输出。

不要输出任何 JSON 之外的文字。

不要使用 Markdown。

不要使用 ```json 代码块。

必须返回合法 JSON。


JSON结构：

{{
    "job_title": "",
    "company": "",
    "job_type": "",
    "responsibilities": [],
    "required_skills": [],
    "bonus_skills": [],
    "experience_level": "",
    "keywords": [],
    "user_matching": {{
        "strong_matches": [],
        "partial_matches": [],
        "gaps": []
    }},
    "ai_capability_analysis": {{
        "job_ai_requirements": [],
        "user_ai_capabilities": [],
        "missing_ai_capabilities": []
    }},
    "recommendation": {{
        "should_apply": true,
        "match_score": 0,
        "reason": "",
        "priority_skills": [],
        "resume_focus": []
    }}
}}


========================
字段说明
========================

job_title：
岗位名称。

company：
公司名称。如果 JD 中没有明确出现公司名称，填写空字符串。

job_type：
岗位类型，例如：
实习、全职、校招等。
如果无法判断，填写空字符串。

responsibilities：
岗位核心工作内容。
提取 3-7 条。

required_skills：
岗位明确要求的核心技能。

bonus_skills：
JD 中属于加分项、优先条件或者非必需条件的技能。

experience_level：
岗位要求的经验水平，例如：
应届生、实习生、1-3年经验等。

keywords：
从 JD 中提取最重要的关键词。

user_matching.strong_matches：
用户经历与岗位要求明显匹配的地方。

user_matching.partial_matches：
用户具备一定相关性，但还不够充分的地方。

user_matching.gaps：
用户目前明显缺少的能力或经历。

ai_capability_analysis.job_ai_requirements：
岗位明确要求或者隐含需要的 AI 能力。

ai_capability_analysis.user_ai_capabilities：
用户明确提供的 AI 相关能力。
不要自行推测用户拥有没有明确提供的 AI 能力。

ai_capability_analysis.missing_ai_capabilities：
岗位需要，但是用户目前没有明确体现的 AI 能力。

recommendation.should_apply：
根据岗位要求和用户背景判断是否建议投递。

recommendation.match_score：
给出 0-100 的整数匹配度。

recommendation.reason：
用简洁的语言解释为什么。

recommendation.priority_skills：
如果用户希望提高这个岗位的竞争力，最应该优先补充的能力。

recommendation.resume_focus：
简历应该重点突出哪些已有经历。


========================
重要规则
========================

1. 不要假设用户没有提供的信息。

2. 不要因为用户对 AI 感兴趣，就默认用户拥有 AI 项目经验。

3. 不要因为用户的专业名称，就推测用户掌握某项具体技术。

4. 只有用户明确提供的经历，才能作为用户经历进行匹配。

5. 如果信息不足，应该明确体现为缺口，而不是自行补充。

6. 对岗位的要求要区分“明确要求”和“推测要求”。

7. match_score 必须基于用户实际提供的信息。

8. 最终必须返回合法 JSON。
"""

    return ask_ai(prompt)


# ==========================================
# 5. 解析 AI 返回的 JSON
# ==========================================

def parse_json_result(result):

    try:
        job_info = json.loads(result)

        return job_info

    except json.JSONDecodeError:

        print()
        print("AI 返回的内容不是合法 JSON。")
        print()
        print("AI 原始返回内容：")
        print(result)

        return None


# ==========================================
# 6. 展示分析结果
# ==========================================

def display_result(job_info):

    print()
    print("========================================")
    print("          JobPilot 岗位分析结果")
    print("========================================")
    print()

    # --------------------------------------
    # 岗位基本信息
    # --------------------------------------

    print("【岗位信息】")
    print()

    print("岗位名称：")
    print(job_info.get("job_title", ""))

    print()

    print("公司：")
    print(job_info.get("company", ""))

    print()

    print("岗位类型：")
    print(job_info.get("job_type", ""))

    print()

    # --------------------------------------
    # 岗位职责
    # --------------------------------------

    print("【核心工作内容】")
    print()

    for item in job_info.get("responsibilities", []):
        print("-", item)

    print()

    # --------------------------------------
    # 必备技能
    # --------------------------------------

    print("【必备技能】")
    print()

    for skill in job_info.get("required_skills", []):
        print("-", skill)

    print()

    # --------------------------------------
    # 加分技能
    # --------------------------------------

    print("【加分技能】")
    print()

    for skill in job_info.get("bonus_skills", []):
        print("-", skill)

    print()

    # --------------------------------------
    # 关键词
    # --------------------------------------

    print("【岗位关键词】")
    print()

    for keyword in job_info.get("keywords", []):
        print("-", keyword)

    print()

    # --------------------------------------
    # 用户匹配
    # --------------------------------------

    matching = job_info.get("user_matching", {})

    print("【你的优势】")
    print()

    for item in matching.get("strong_matches", []):
        print("-", item)

    print()

    print("【部分匹配】")
    print()

    for item in matching.get("partial_matches", []):
        print("-", item)

    print()

    print("【能力缺口】")
    print()

    for item in matching.get("gaps", []):
        print("-", item)

    print()

    # --------------------------------------
    # AI能力分析
    # --------------------------------------

    ai_analysis = job_info.get(
        "ai_capability_analysis",
        {}
    )

    print("【岗位需要的 AI 能力】")
    print()

    for item in ai_analysis.get(
        "job_ai_requirements",
        []
    ):
        print("-", item)

    print()

    print("【你目前体现出的 AI 能力】")
    print()

    for item in ai_analysis.get(
        "user_ai_capabilities",
        []
    ):
        print("-", item)

    print()

    print("【AI 能力缺口】")
    print()

    for item in ai_analysis.get(
        "missing_ai_capabilities",
        []
    ):
        print("-", item)

    print()

    # --------------------------------------
    # 投递建议
    # --------------------------------------

    recommendation = job_info.get(
        "recommendation",
        {}
    )

    print("【投递建议】")
    print()

    should_apply = recommendation.get(
        "should_apply",
        False
    )

    if should_apply:
        print("建议投递：是")
    else:
        print("建议投递：暂不建议")

    print()

    print(
        "岗位匹配度：",
        recommendation.get(
            "match_score",
            0
        ),
        "/ 100"
    )

    print()

    print("原因：")
    print(
        recommendation.get(
            "reason",
            ""
        )
    )

    print()

    print("【优先补充的能力】")
    print()

    for item in recommendation.get(
        "priority_skills",
        []
    ):
        print("-", item)

    print()

    print("【简历应该重点突出】")
    print()

    for item in recommendation.get(
        "resume_focus",
        []
    ):
        print("-", item)

    print()


# ==========================================
# 7. 主程序
# ==========================================

def main():

    # 第一步：收集用户信息
    user_profile = collect_user_profile()

    print()
    print("========================================")
    print("正在读取招聘 JD...")
    print("========================================")
    print()

    # 第二步：读取 JD
    with open(
        "data/job.txt",
        "r",
        encoding="utf-8"
    ) as file:

        job_description = file.read()

    print("正在分析岗位，请稍等...")
    print()

    # 第三步：让 AI 分析 JD
    result = analyze_job(
        job_description,
        user_profile
    )

    # 第四步：解析 JSON
    job_info = parse_json_result(result)

    # 第五步：展示结果
    if job_info:

        display_result(job_info)


# ==========================================
# 8. 程序入口
# ==========================================

if __name__ == "__main__":
    main()