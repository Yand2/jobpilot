from utils.llm import create_client
from utils.router import IntentRouter


def main():

    client = create_client()

    router = IntentRouter(client)

    print("================================")
    print("JobPilot Intent Router")
    print("输入 exit 退出")
    print("================================")

    while True:

        user_message = input("\n你：").strip()

        if user_message.lower() == "exit":

            break

        if not user_message:

            continue

        result = router.route(
            user_message
        )

        print("\nAgent判断：")

        print(
            "Intent：",
            result["intent"]
        )

        print(
            "Reason：",
            result["reason"]
        )


if __name__ == "__main__":

    main()