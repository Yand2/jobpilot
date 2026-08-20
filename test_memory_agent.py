from agents.career_agent import CareerAgent
from utils.llm import create_client



client = create_client()


agent = CareerAgent(
    client
)



questions = agent.check_profile()



if questions:


    print(
        "我需要了解你的信息："
    )


    for q in questions:

        print(
            "-",
            q
        )


else:

    print(
        "用户信息完整"
    )