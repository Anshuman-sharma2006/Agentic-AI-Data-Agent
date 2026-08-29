from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()


def pick_llm(level: str):
    """
    Picks a Groq model based on the question level.

    Args:
        level: "low", "medium", or "high"

    Returns:
        ChatGroq configured to use Groq.
    """

    level = level.lower()

    if level == "low":
        model = "qwen/qwen3.6-27b"

    elif level == "medium":
        model = "qwen/qwen3.8-27b"

    elif level == "high":
        model = "openai/gpt-oss-120b"

    else:
        raise ValueError(f"Unsupported level: {level}")
#reasoning_format-> by default, the reasoning format is set to "hidden"(Think div) in the ChatGroq class. If you want to change it, you can uncomment the line and set it to your desired format.
    return ChatGroq(
        model=model,
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0,
        reasoning_format="hidden",
    )


if __name__ == "__main__":
    llm = pick_llm("low")

    response = llm.invoke("What is the capital of France?")

    print(response.content)