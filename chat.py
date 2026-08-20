from utils.llm import create_client
from agents.career_agent import CareerAgent


def main():

    client = create_client()

    agent = CareerAgent(client)

    agent.start_conversation()


if __name__ == "__main__":

    main()