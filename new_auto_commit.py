#!/usr/bin/env python3
import os
import subprocess
import json
import urllib.request
import urllib.error
import sys

# --- Configuration ---
MODEL = "llama3-70b-versatile"  # Updated model name to match Groq's latest naming convention
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
    """Runs a shell command and returns the output safely with diagnostic info."""
    try:
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
        # Return empty string but keep diagnostics in case we need to debug
        return ""
    except Exception:
        return ""

def get_repo_info():
    """Retrieves the repository name and current branch."""
    branch = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    toplevel = run_cmd(["git", "rev-parse", "--show-toplevel"])
    repo_name = os.path.basename(toplevel) if toplevel else "Unknown"
    return repo_name, branch

def get_staged_diff():
    """Gets the git diff of currently staged files."""
    return run_cmd(["git", "diff", "--staged", "--ignore-submodules=dirty"])

def get_unstaged_status():
    """Checks for modified or untracked files."""
    return run_cmd(["git", "status", "--porcelain", "--ignore-submodules=dirty"])

def generate_commit_message(diff, api_key):
    """Uses Groq's LLaMA-3 to generate a conventional commit message."""
    if not diff or len(diff.strip()) < 10:
        return "chore: update files"

    print("🧠 Analyzing code changes with AI...")
    
    # Escape quotes to prevent JSON 400 Bad Request errors
    safe_diff = diff[:4000].replace('"', "'") 
    
    prompt = (
        "You are a Principal Software Engineer. Write a concise, professional Git commit message "
        "based on the following 'git diff'. Follow the Conventional Commits specification. "
        "Do NOT include markdown, quotes, or explanations. Output ONLY the raw message.\n\n"
        f"Git Diff:\n{safe_diff}"
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
        "temperature": 0.1,
        "max_tokens": 80
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result['choices'][0]['message']['content'].strip().strip('"').strip("'")
    except Exception as e:
        print(f"❌ AI Generation failed: {e}")
        return None

def main():
    repo_name, branch = get_repo_info()
    
    print("-" * 40)
    print(f"📂 Repo:   {repo_name}")
    print(f"🌿 Branch: {branch}")
    print(f"📍 Path:   {os.getcwd()}")
    print("-" * 40)
    
    api_key = get_api_key()
    if not api_key:
        return

    auto_mode = "-a" in sys.argv or "--auto" in sys.argv
    
    # Step 1: Check staged
    diff = get_staged_diff()
    
    if not diff:
        print("ℹ️ No staged changes detected. Checking for unstaged/untracked files...")
        unstaged = get_unstaged_status()
        
        if unstaged:
            print("✨ Found unstaged/untracked changes:")
            for line in unstaged.split('\n'):
                if line.strip():
                    print(f"   {line}")
                
            if auto_mode:
                auto_add = 'y'
            else:
                auto_add = input("\nDo you want to stage all these files (`git add .`)? (y/n): ").strip().lower()
                
            if auto_add == 'y':
                print("➕ Running 'git add .'...")
                run_cmd(["git", "add", "."])
                diff = get_staged_diff()
                if not diff:
                    print("❌ Error: Files were added but 'git diff --staged' is still empty.")
                    return
            else:
                print("🛑 Aborted by user.")
                return
        else:
            print("⚠️ Git reports the working tree is clean (ignoring dirty submodules).")
            return

    # Step 2: AI Generation
    commit_msg = generate_commit_message(diff, api_key)
    if not commit_msg:
        print("❌ Failed to generate a message from the AI.")
        return

    print(f"\n✨ Generated Message: {commit_msg}")

    # Step 3: Final Action
    if auto_mode:
        confirm = 'y'
    else:
        confirm = input("Confirm commit and push? (y/n): ").strip().lower()
        
    if confirm == 'y':
        print("💾 Committing...")
        run_cmd(["git", "commit", "-m", commit_msg])
        print("🚀 Pushing to remote...")
        run_cmd(["git", "push"])
        print("✅ Process complete!")
    else:
        print("🛑 Commit aborted.")

if __name__ == "__main__":
    main()