import os

from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Using the most modern stable flash model from your list
MODEL_ID = "gemini-2.5-flash"


def test_connection():
    try:
        response = client.models.generate_content(
            model=MODEL_ID, contents="Say 'System online with Gemini 2.5 Flash'"
        )
        print(f"✅ {response.text}")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")


if __name__ == "__main__":
    test_connection()
