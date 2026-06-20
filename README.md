# MJ Reverse AI

> **Offline AI Coding Agent** — Runs locally on your machine using GGUF models. No internet required after setup.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- 🔌 **Fully Offline** — No API keys, no cloud, no internet needed
- 🤖 **Multi-Model Support** — Works with Llama 3, Mistral, Phi-3, Qwen, CodeGemma, DeepSeek & more
- 🧠 **Auto-Detection** — Automatically picks the correct chat format for each model
- 🛠️ **Agentic Tools** — Read/write files, search code, run terminal commands
- 🔄 **Hot-Swap Models** — Switch between models mid-session with `/switch`
- 💊 **Self-Healing** — Launcher auto-restores missing files from embedded backups
- 📊 **RAM-Aware** — Shows memory requirements and warns about heavy models

## 📋 Requirements

| Component | Details |
|---|---|
| **OS** | Windows 10/11 |
| **Python** | 3.10 or 3.11 (embedded/portable works) |
| **RAM** | 8 GB minimum (16 GB recommended for 7B models) |
| **CPU** | Any x86_64 (AVX2 recommended) |
| **Models** | At least one `.gguf` model file |

## 🚀 Quick Start

### 1. Clone this repo
```bash
git clone https://github.com/YOUR_USERNAME/MJ-Reverse-AI.git
cd MJ-Reverse-AI
```

### 2. Install Python dependency
```bash
pip install llama-cpp-python==0.3.19 --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

> **Note for older CPUs (4th gen Intel / no AVX2):** The above URL provides pre-built CPU wheels that avoid illegal instruction crashes.

### 3. Download a GGUF model

Place any `.gguf` model in a `models/` folder next to the project or in the parent directory. Recommended models:

| Model | Size | RAM Needed | Best For |
|---|---|---|---|
| [Llama-3.2-3B-Instruct-Q4_K_M](https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF) | 1.9 GB | ~2 GB | Low-RAM systems |
| [Phi-3.5-mini-instruct-Q4_K_M](https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF) | 2.2 GB | ~3 GB | Balanced quality/speed |
| [Qwen2.5-Coder-7B-Instruct-Q4_K_M](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF) | 4.4 GB | ~5 GB | Best code quality |

### 4. Launch
```bash
# Windows — double-click START.bat
# Or from terminal:
python launcher.py
```

## 📁 Project Structure

```
MJ-Reverse-AI/
├── START.bat          # Windows launcher (auto-detects paths)
├── launcher.py        # Self-healing entry point
├── agent.py           # AI agent with model profiles & chat loop
├── ui.py              # Terminal UI (colors, spinners, prompts)
├── tools.py           # Agentic tools (read/write/search/run)
├── requirements.txt   # Python dependencies
├── .gitignore
└── README.md
```

## 💬 Usage

Once launched, you'll see the model selection menu:

```
Select an AI Model to load:
  [1] Llama-3.2-3B-Instruct-Q4_K_M.gguf
      Llama 3.x  |  1.9 GB  |  ~2 GB RAM
  [2] Phi-3.5-mini-instruct-Q4_K_M.gguf
      Phi-3.x  |  2.2 GB  |  ~3 GB RAM
```

After loading, chat in plain English:

```
MJ Reverse AI> create a python flask hello world app
```

The AI can read/write files and run commands in your workspace (with your permission).

### Slash Commands

| Command | Description |
|---|---|
| `/help` | Show available commands |
| `/switch` | Change to a different GGUF model |
| `/status` | View loaded model info |
| `/clear` | Reset chat history |
| `/add <file>` | Load a file into context |
| `/files` | List files in context |
| `/exit` | Quit |

## 🧩 Supported Models

Any GGUF model works. These families have optimized chat format profiles:

| Family | Chat Format | Example |
|---|---|---|
| Llama 3.x | `llama-3` | Llama-3.2-3B-Instruct |
| Mistral | `mistral-instruct` | Mistral-7B-Instruct-v0.3 |
| Phi-3.x | `chatml` | Phi-3.5-mini-instruct |
| Qwen 2.x | `chatml` | Qwen2.5-Coder-7B-Instruct |
| CodeGemma | `gemma` | codegemma-7b |
| DeepSeek | `chatml` | DeepSeek-Coder-6.7B |
| CodeLlama | `llama-2` | CodeLlama-7B-Instruct |

Unknown models fall back to auto-detection from GGUF metadata.

## 🔧 Pendrive / Portable Mode

MJ Reverse AI can run entirely from a USB drive:

1. Place `apps/python/` (portable Python) alongside the project
2. Place `.gguf` models in a `models/` folder
3. `START.bat` auto-detects paths relative to its location

```
USB Drive/
├── apps/python/          # Portable Python 3.11
├── models/               # Your .gguf files
└── MJ-Reverse-AI/        # This project
    ├── START.bat
    ├── launcher.py
    └── ...
```

## 📄 License

MIT License — free for personal and commercial use.
