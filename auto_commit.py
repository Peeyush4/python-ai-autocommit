#!/usr/bin/env python3
import os
import subprocess
import json
import urllib.request
import urllib.error
import sys

# --- Configuration ---
MODEL = "llama-3.3-70b-versatile"
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

def run_cmd(command):
    """Runs a shell command and returns the output safely."""
    try:
        # Added encoding='utf-8' and errors='replace' to handle Windows encoding issues (UnicodeDecodeError)
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            check=True, 
            encoding='utf-8', 
            errors='replace'
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Return empty string instead of None to prevent .strip() errors in calling functions
        return ""
    except Exception:
        return ""

def get_staged_diff():
    """Gets the git diff of currently staged files, ignoring dirty submodules."""
    return run_cmd(["git", "diff", "--staged", "--ignore-submodules=dirty"])

def get_unstaged_status():
    """Checks for modified or untracked files, ignoring dirty submodules."""
    return run_cmd(["git", "status", "--porcelain", "--ignore-submodules=dirty"])

def generate_commit_message(diff, api_key):
    """Uses Groq's LLaMA-3 to generate a conventional commit message."""
    if not diff or len(diff.strip()) < 10:
        return "chore: minor updates"

    print("🧠 Analyzing code changes with AI...")
    
    # Truncate and clean the diff to prevent 400 Bad Request errors
    # We use a 4000 char limit which is safe for most context windows
    safe_diff = diff[:4000].replace('"', "'") 
    
    prompt = (
        "You are a Principal Software Engineer. Write a concise, professional Git commit message "
        "based on the following 'git diff'. Follow the Conventional Commits specification "
        "(e.g., feat:, fix:, refactor:, chore:, docs:). Do NOT include markdown, quotes, or explanations. "
        f"Output ONLY the raw message.\n\nGit Diff:\n{safe_diff}"
    )

    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "AI-Auto-Committer/1.0"
    }
    
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1, # Lowered for even higher determinism
        "max_tokens": 80
    }

    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode("utf-8"), 
            headers=headers
        )
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            commit_msg = result['choices'][0]['message']['content'].strip()
            # Final cleanup of common LLM artifacts
            return commit_msg.split('\n')[0].strip('"').strip("'").strip('`')
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else ""
        if e.code == 400:
            print(f"❌ Bad Request (400): The diff might be too complex or the request is malformed.")
            print(f"Details: {error_body}")
        elif e.code == 401:
            print("❌ Unauthorized: Your API key is invalid.")
        elif e.code == 429:
            print("❌ Rate Limit: Too many requests to Groq.")
        else:
            print(f"❌ API Request failed: {e.code} {e.reason}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def main():
    api_key = get_api_key()
    if not api_key:
        print("❌ Cannot proceed without a GROQ API Key. Aborting.")
        return

    auto_mode = "-a" in sys.argv or "--auto" in sys.argv

    diff = get_staged_diff()
    
    if not diff:
        unstaged = get_unstaged_status()
        if unstaged:
            print("⚠️ No staged changes found, but you have unstaged/untracked files:")
            for line in unstaged.split('\n'):
                if line.strip():
                    print(f"   {line}")
                
            if auto_mode:
                print("\n⚡ Auto-mode: Staging all files automatically...")
                auto_add = 'y'
            else:
                auto_add = input("\nDo you want to stage all these files (`git add .`) and continue? (y/n): ").strip().lower()
                
            if auto_add == 'y':
                run_cmd(["git", "add", "."])
                diff = get_staged_diff()
                if not diff:
                    print("🛑 Still no valid changes to commit after staging. Aborting.")
                    return
            else:
                print("🛑 Commit aborted. Please stage files manually.")
                return
        else:
            print("⚠️ Working tree clean. Nothing to commit.")
            return

    commit_msg = generate_commit_message(diff, api_key)
    if not commit_msg:
        return

    print(f"\n✨ Generated Commit Message:\n> {commit_msg}\n")

    if auto_mode:
        print("⚡ Auto-mode: Committing and pushing automatically...")
        confirm = 'y'
    else:
        confirm = input("Do you want to commit and push this? (y/n): ").strip().lower()
        
    if confirm == 'y':
        run_cmd(["git", "commit", "-m", commit_msg])
        print("🚀 Pushing to GitHub...")
        run_cmd(["git", "push"])
        print("✅ Successfully pushed!")
    else:
        print("🛑 Commit aborted.")

if __name__ == "__main__":
    main()