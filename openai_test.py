from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    response = client.models.list()
    print("✅ Your key works! Available models:")
    for model in response.data:
        print("-", model.id)
except Exception as e:
    print("❌ Error with your API key:", e)
