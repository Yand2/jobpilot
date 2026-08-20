from skills.jd_analyzer import JDAnalyzer
from skills.resume_matcher import ResumeMatcher
from utils.llm import create_client


def main():

    # ==================================
    # 1. 创建 AI Client
    # ==================================

    client = create_client()


    # ==================================
    # 2. 创建两个 Skill
    # ==================================

    jd_analyzer = JDAnalyzer(client)

    resume_matcher = ResumeMatcher(client)


    # ==================================
    # 3. 读取 JD
    # ==================================

    with open(
        "data/job.txt",
        "r",
        encoding="utf-8"
    ) as file:

        job_description = file.read()


    # ==================================
    # 4. 模拟用户信息
    # ==================================

    user_profile = {

        "major": "这里填写你的真实专业",

        "education": "这里填写你的学历和年级",

        "target_jobs": "这里填写你想投递的岗位",

        "experience": """
这里填写你的真实经历。

例如：

MUJI 实习：
参与食品销售数据分析，
制作 Power BI 报表。

其他项目：
这里继续填写你的真实项目。
""",

        "ai_experience": """
对 AI 领域有较强兴趣。

了解基础 AI 工具的使用，
包括 Agent、Workflow、Skills、
Harness 等概念。

目前正在独立开发 JobPilot AI 求职助手项目。
"""
    }


    # ==================================
    # 5. 分析 JD
    # ==================================

    print()
    print("================================")
    print("Step 1：分析招聘 JD")
    print("================================")
    print()

    job_info = jd_analyzer.analyze(
        job_description
    )

    print("岗位：")
    print(job_info["job_title"])

    print()


    # ==================================
    # 6. 匹配用户经历
    # ==================================

    print("================================")
    print("Step 2：匹配用户经历")
    print("================================")
    print()

    match_result = resume_matcher.match(
        job_info,
        user_profile
    )


    # ==================================
    # 7. 输出结果
    # ==================================

    print("匹配度：")
    print(
        match_result["match_score"],
        "/ 100"
    )

    print()


    print("【强匹配】")

    for item in match_result["strong_matches"]:

        print(
            f"- {item['requirement']}"
        )

        print(
            f"  证据：{item['evidence']}"
        )

        print(
            f"  原因：{item['reason']}"
        )

    print()


    print("【部分匹配】")

    for item in match_result["partial_matches"]:

        print(
            f"- {item['requirement']}"
        )

        print(
            f"  证据：{item['evidence']}"
        )

        print(
            f"  原因：{item['reason']}"
        )

    print()


    print("【能力缺口】")

    for item in match_result["gaps"]:

        print(
            f"- {item['requirement']}"
        )

        print(
            f"  原因：{item['reason']}"
        )

    print()


    print("【未知信息】")

    for item in match_result["unknowns"]:

        print(
            f"- {item['requirement']}"
        )

        print(
            f"  原因：{item['reason']}"
        )

    print()


    print("【总结】")

    print(
        match_result["summary"]
    )

    print()


    print("【优先行动】")

    for action in match_result["priority_actions"]:

        print("-", action)


if __name__ == "__main__":
    main()