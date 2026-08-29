import os
from dotenv import load_dotenv
from groq import Groq
from langchain_groq import ChatGroq

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")


print("Key loaded:", bool(api_key))
print("Key prefix:", api_key[:8] if api_key else None)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

models = client.models.list()

for model in models.data:
    print(model.id)

model = ChatGroq(
    model="qwen/qwen3.6-27b",
    groq_api_key=os.getenv("GROQ_API_KEY")
)

response = model.invoke("Why do parrots talk?")

print(response.content)