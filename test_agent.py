from utils.llm import create_client
from agents.career_agent import CareerAgent



def main():


    client = create_client()



    agent = CareerAgent(
        client
    )



    # 读取JD

    with open(
        "data/job.txt",
        "r",
        encoding="utf-8"
    ) as f:

        job_description = f.read()



    # 用户信息

    user_profile = {


        "major":
        "你的专业",


        "education":
        "本科在读",


        "target_jobs":
        "AI产品、AI应用方向",


        "experience":
        """
        MUJI实习：

        使用Power BI制作食品销售数据分析报表。
        """,


        "ai_experience":
        """
        学习AI应用开发。

        了解Agent、
        Workflow、
        Skills、
        Harness。

        正在开发JobPilot项目。
        """

    }



    job_info = agent.jd_analyzer.analyze(job_description)
    match_result = agent.resume_matcher.match(job_info, user_profile)
    result = {"job_info": job_info, "match_result": match_result}



    print("\n================")
    print("岗位信息")
    print("================")


    print(
        result["job_info"]
    )



    print("\n================")
    print("匹配结果")
    print("================")


    print(
        result["match_result"]
    )



if __name__ == "__main__":

    main()
