# AI Auto-Committer 🚀

A lightning-fast, zero-dependency command-line tool that automatically writes professional [Conventional Commit](https://www.conventionalcommits.org/) messages for you using Groq's LLaMA-3 API.

Stop thinking about what to write in your commit messages. Let AI read your `git diff` and do it for you in milliseconds.

## ✨ Features

* **Blazing Fast AI**: Powered by Groq's `llama3-70b-8192` model for near-instant inference.
* **Smart Staging**: Automatically detects unstaged or untracked files and asks if you want to stage them.
* **"YOLO" Auto Mode**: Bypass all prompts with the `-a` flag to instantly stage, commit, and push in one command.
* **Zero Heavy Dependencies**: Built entirely with Python's standard library (`urllib`, `subprocess`, `os`, `json`).
* **Painless Configuration**: Saves your API key locally so you don't have to fight with Windows/Linux environment variables.
* **Submodule Safe**: Ignores noisy `-dirty` submodule warnings.

## 🛠️ Prerequisites

* Python 3.7 or higher
* Git installed and initialized in your repository
* A **Free** Groq API Key (Get one at [console.groq.com](https://console.groq.com/keys))

## 📦 Installation

Since this tool is packaged via `pyproject.toml`, you can install it globally on your machine using `pip`.

1. Clone or download this repository.
2. Open your terminal and navigate to the folder containing `pyproject.toml` and `auto_commit.py`.
3. Run the following command:

```bash
pip install .
```

*(Note: If you want to keep editing the code and have the changes apply instantly, install it in editable mode: `pip install -e .`)*

## 🚀 Usage

Once installed, the `ai-commit` command will be available globally in your terminal. Navigate to any git repository with changes and run:

### 1. Interactive Mode (Default)
Safely review what is happening before committing.
```bash
ai-commit
```

### 2. Auto Mode (Fast)
Skip the prompts and just get it done.
```bash
ai-commit -a
# or
ai-commit --auto
```

## 🔑 Configuration

On your very first run, the tool will prompt you for your API key and save it to `~/.ai_commit_key` (or the equivalent path on Windows).

## 📝 License

Created by Peeyush. Feel free to modify and adapt this tool for your personal or team workflows!
