from utils.llm import create_client
from agents.career_agent import CareerAgent


def main():

    client = create_client()

    agent = CareerAgent(client)

    print("================================")
    print("       JobPilot Agent")
    print("================================")

    while True:

        user_message = input(
            "\n你："
        ).strip()

        if user_message.lower() == "exit":

            print("JobPilot：再见。")

            break

        if not user_message:

            continue

        result = agent.handle(
            user_message
        )

        print("\nJobPilot：")

        print(result)


if __name__ == "__main__":

    main()