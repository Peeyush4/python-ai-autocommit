import requests
import os
import pandas as pd

CONFIG_FILE = os.path.expanduser("~/.ai_commit_key")


def get_api_key():
    """Retrieves the API key from a local config file, or prompts the user for it."""
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        return api_key

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return f.read().strip()

    print("🔑 GROQ API Key not found.")
    print("Get your free key at: https://console.groq.com/keys")
    api_key = input("Please paste your GROQ_API_KEY here: ").strip()
    
    if api_key:
        with open(CONFIG_FILE, "w") as f:
            f.write(api_key)
        print(f"✅ Key saved to {CONFIG_FILE} for future use!\n")
        return api_key
    
    return None

api_key = get_api_key()
if not api_key:
    print("❌ No API key found. Please set your GROQ_API_KEY environment variable or create a config file.")
    exit(1)

url = "https://api.groq.com/openai/v1/models"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)

# Convert the JSON response to a pandas DataFrame
df = pd.DataFrame(response.json()["data"])

df.to_excel("models.xlsx", index=False)