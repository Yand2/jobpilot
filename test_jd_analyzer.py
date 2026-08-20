from skills.jd_analyzer import JDAnalyzer
from utils.llm import create_client


def main():

    # 创建 AI 客户端
    client = create_client()

    # 创建 JD Analyzer
    analyzer = JDAnalyzer(client)

    # 读取 JD
    with open(
        "data/job.txt",
        "r",
        encoding="utf-8"
    ) as file:

        job_description = file.read()

    print("正在分析 JD...")
    print()

    # 调用 Skill
    result = analyzer.analyze(
        job_description
    )

    print("========== JD Analyzer ==========")
    print()

    print("岗位名称：")
    print(result["job_title"])

    print()

    print("公司：")
    print(result["company"])

    print()

    print("核心职责：")

    for item in result["responsibilities"]:
        print("-", item)

    print()

    print("必备技能：")

    for skill in result["required_skills"]:
        print("-", skill)

    print()

    print("加分技能：")

    for skill in result["bonus_skills"]:
        print("-", skill)

    print()

    print("关键词：")

    for keyword in result["keywords"]:
        print("-", keyword)


if __name__ == "__main__":
    main()