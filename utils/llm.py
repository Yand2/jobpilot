import os
from openai import OpenAI


def create_client(api_key=None):

    api_key = api_key or os.getenv("DEEPSEEK_API_KEY")

    if not api_key:
        raise RuntimeError(
            "没有找到 DEEPSEEK_API_KEY"
        )

    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
        timeout=60.0,
        max_retries=1,
    )
