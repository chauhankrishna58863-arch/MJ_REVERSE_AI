import sys
import os

# Dynamically find site-packages relative to this script
_script_dir = os.path.dirname(os.path.abspath(__file__))
_search_roots = [
    os.path.dirname(os.path.dirname(_script_dir)),  # grandparent (PulseShift)
    os.path.dirname(_script_dir),                    # parent (models)
]
_found_sp = False
for _root in _search_roots:
    _sp = os.path.join(_root, "apps", "python", "Lib", "site-packages")
    if os.path.isdir(_sp) and _sp not in sys.path:
        sys.path.insert(0, _sp)
        _found_sp = True
        break
if not _found_sp:
    _fallback = r"A:\OllamaData\apps\python\Lib\site-packages"
    if os.path.isdir(_fallback) and _fallback not in sys.path:
        sys.path.insert(0, _fallback)

import re
import gc
from tools import AgentTools

# ─── Model Profiles ──────────────────────────────────────────────────────────
# Maps filename patterns (lowercase) to optimal settings for each model family.
# chat_format: tells llama-cpp-python how to wrap messages into the model's
#              native prompt template. "auto" = let the library detect from
#              GGUF metadata (works for most modern models).
# ctx:         recommended context window (tokens).  Smaller = less RAM.
# ram_gb:      approximate RAM needed (model weights + context KV-cache).
# family:      human-readable family name for display.
# ─────────────────────────────────────────────────────────────────────────────
MODEL_PROFILES = [
    # ── Llama 3 / 3.1 / 3.2  ─────────────────────────────────────────────
    {"pattern": "llama-3",     "chat_format": "llama-3",  "ctx": 4096, "ram_gb": 2.5, "family": "Llama 3.x"},
    {"pattern": "llama3",      "chat_format": "llama-3",  "ctx": 4096, "ram_gb": 2.5, "family": "Llama 3.x"},
    # ── Mistral / Mixtral  ───────────────────────────────────────────────
    {"pattern": "mistral",     "chat_format": "mistral-instruct", "ctx": 4096, "ram_gb": 5.0, "family": "Mistral"},
    {"pattern": "mixtral",     "chat_format": "mistral-instruct", "ctx": 4096, "ram_gb": 5.0, "family": "Mixtral"},
    # ── Phi-3 / Phi-3.5  ─────────────────────────────────────────────────
    {"pattern": "phi-3",       "chat_format": "chatml",   "ctx": 4096, "ram_gb": 3.0, "family": "Phi-3.x"},
    {"pattern": "phi3",        "chat_format": "chatml",   "ctx": 4096, "ram_gb": 3.0, "family": "Phi-3.x"},
    # ── Qwen 2 / 2.5  ───────────────────────────────────────────────────
    {"pattern": "qwen",        "chat_format": "chatml",   "ctx": 4096, "ram_gb": 5.0, "family": "Qwen 2.x"},
    # ── CodeGemma  ───────────────────────────────────────────────────────
    {"pattern": "codegemma",   "chat_format": "gemma",    "ctx": 4096, "ram_gb": 5.5, "family": "CodeGemma"},
    {"pattern": "gemma",       "chat_format": "gemma",    "ctx": 4096, "ram_gb": 5.5, "family": "Gemma"},
    # ── NemoMix / Nemo  ──────────────────────────────────────────────────
    {"pattern": "nemo",        "chat_format": "chatml",   "ctx": 2048, "ram_gb": 8.0, "family": "NemoMix"},
    # ── DeepSeek Coder  ──────────────────────────────────────────────────
    {"pattern": "deepseek",    "chat_format": "chatml",   "ctx": 4096, "ram_gb": 5.0, "family": "DeepSeek"},
    # ── StarCoder / CodeLlama ────────────────────────────────────────────
    {"pattern": "starcoder",   "chat_format": "chatml",   "ctx": 4096, "ram_gb": 5.0, "family": "StarCoder"},
    {"pattern": "codellama",   "chat_format": "llama-2",  "ctx": 4096, "ram_gb": 5.0, "family": "CodeLlama"},
    # ── Llama 2 (older)  ─────────────────────────────────────────────────
    {"pattern": "llama-2",     "chat_format": "llama-2",  "ctx": 4096, "ram_gb": 5.0, "family": "Llama 2"},
    {"pattern": "llama2",      "chat_format": "llama-2",  "ctx": 4096, "ram_gb": 5.0, "family": "Llama 2"},
]

class Agent:
    TOTAL_RAM_GB = 8  # your machine's RAM

    def __init__(self, ui, workspace_root, models_dir, initial_model_path, context_size=4096):
        self.ui = ui
        self.workspace_root = workspace_root
        self.models_dir = models_dir
        self.model_path = initial_model_path
        self.context_size = context_size
        self.chat_format = None          # detected per-model
        self.model_family = "Unknown"
        
        self.tools = AgentTools(workspace_root)
        self.llm = None
        self.messages = []
        self.loaded_files = set()
        self.memory_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.json")

    # ── Profile Detection ────────────────────────────────────────────────
    @staticmethod
    def get_model_profile(model_path):
        """Match a GGUF filename against MODEL_PROFILES and return the best match."""
        name = os.path.basename(model_path).lower()
        for profile in MODEL_PROFILES:
            if profile["pattern"] in name:
                return profile
        # Fallback: let llama.cpp auto-detect
        return {"pattern": "*", "chat_format": None, "ctx": 2048, "ram_gb": 5.0, "family": "Unknown"}

    def initialize(self):
        basename = os.path.basename(self.model_path)
        profile = self.get_model_profile(self.model_path)
        self.model_family = profile["family"]
        self.chat_format = profile["chat_format"]
        self.context_size = profile["ctx"]

        # RAM warning
        if profile["ram_gb"] > self.TOTAL_RAM_GB * 0.85:
            self.ui.warning(
                f"{basename} needs ~{profile['ram_gb']:.1f} GB RAM "
                f"(you have {self.TOTAL_RAM_GB} GB). It may be very slow "
                f"due to heavy swap usage."
            )

        self.ui.info(f"Model family : {self.model_family}")
        self.ui.info(f"Chat format  : {self.chat_format or 'auto-detect'}")
        self.ui.info(f"Context size : {self.context_size} tokens")
        self.ui.start_spinner(f"Loading GGUF model: {basename}...")
        try:
            from llama_cpp import Llama
            llama_kwargs = dict(
                model_path=self.model_path,
                n_ctx=self.context_size,
                verbose=False,
            )
            if self.chat_format:
                llama_kwargs["chat_format"] = self.chat_format

            self.llm = Llama(**llama_kwargs)
            self.ui.stop_spinner_success(f"{basename} loaded successfully!")
            self.load_memory()
        except Exception as e:
            self.ui.stop_spinner_error(f"Failed to load model: {str(e)}")
            raise e

    def load_memory(self):
        if not os.path.exists(self.memory_path):
            self.reset_conversation()
            return
        
        try:
            import json
            with open(self.memory_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    self.messages = data
                    # Always update system prompt at index 0 to reflect current workspace
                    if self.messages[0]["role"] == "system":
                        self.messages[0]["content"] = self.build_system_prompt()
                    else:
                        self.messages.insert(0, {"role": "system", "content": self.build_system_prompt()})
                    
                    # Reconstruct loaded_files list
                    for msg in self.messages:
                        if msg["role"] == "user" and "[Developer Injected Context for File:" in msg["content"]:
                            match = re.search(r"\[Developer Injected Context for File:\s*(.*?)\]", msg["content"])
                            if match:
                                self.loaded_files.add(match.group(1).strip())
                    self.ui.info(f"Restored previous conversation memory ({len(self.messages)} messages).")
                    return
        except Exception as e:
            self.ui.warning(f"Memory file was corrupted or unreadable: {str(e)}")
            try:
                bak_path = self.memory_path + ".corrupt"
                if os.path.exists(self.memory_path):
                    os.replace(self.memory_path, bak_path)
                    self.ui.info(f"Backed up corrupted memory file to: {os.path.basename(bak_path)}")
            except Exception:
                pass
        
        self.reset_conversation()

    def save_memory(self):
        try:
            import json
            with open(self.memory_path, 'w', encoding='utf-8') as f:
                json.dump(self.messages, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.ui.warning(f"Failed to save conversation memory: {str(e)}")

    def reset_conversation(self):
        self.messages = [
            {"role": "system", "content": self.build_system_prompt()}
        ]
        self.loaded_files.clear()
        self.save_memory()

    def build_system_prompt(self):
        return f"""You are MJ Reverse AI, a premium and highly-capable offline agentic AI developer running locally.
You help the user build, debug, and understand their code. You have access to tools that let you read and modify the workspace.

Workspace Root Directory: {self.workspace_root}

To perform operations on the workspace, you MUST output specific XML tags in your response. You can output multiple tags in a single turn if needed.
The system will parse these tags, ask the user for permission, execute the tools, and feed the results back to you.

Available XML Tools:

1. READ FILE:
   <read_file path="relative/path/to/file" />
   Use this to view the content of a file.

2. WRITE/CREATE FILE:
   <write_file path="relative/path/to/file">
   [complete file contents here]
   </write_file>
   Use this to create a new file or completely rewrite an existing file with new content.

3. LIST DIRECTORY:
   <list_dir path="relative/path/to/dir" />
   Use this to list files and folders (default path is "." for the root).

4. SEARCH CODEBASE:
   <search_files query="text to find" />
   Use this to search for text matches/usages across codebase files.

5. RUN COMMAND:
   <run_command cmd="command to run" />
   Use this to run terminal commands (e.g. compiling, testing, package installs, running files).
   Note: Do not use 'cd' commands; all commands run in the workspace root.

Guidelines:
- Explain what you want to do BEFORE using a tool.
- Talk like a normal developer, replying in clear English.
- Write high-quality, clean, production-ready code.
- Wait for tool results before explaining them or declaring a task complete.
"""

    def start_repl(self):
        self.ui.success("Welcome to MJ Reverse AI! Chat with me in plain English.")
        self.ui.info("Type /help to see available slash commands.")
        
        while True:
            user_input = self.ui.prompt_input(f"\n{self.ui.CYAN}{self.ui.BOLD}MJ Reverse AI> {self.ui.RESET}").strip()
            
            if not user_input:
                continue
                
            if user_input.startswith('/'):
                exit_repl = self.handle_slash_command(user_input)
                if exit_repl:
                    break
                continue
                
            self.run_agent_loop(user_input)

    def handle_slash_command(self, command_str):
        parts = command_str.split(' ')
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in ['/exit', '/quit']:
            self.ui.info("Exiting MJ Reverse AI. Goodbye!")
            return True
            
        elif cmd == '/help':
            print(f"\n{self.ui.CYAN}{self.ui.BOLD}Available Slash Commands:{self.ui.RESET}")
            print(f"  {self.ui.YELLOW}/help{self.ui.RESET}           - Show this help menu")
            print(f"  {self.ui.YELLOW}/exit{self.ui.RESET} or {self.ui.YELLOW}/quit{self.ui.RESET} - Exit the AI shell")
            print(f"  {self.ui.YELLOW}/switch{self.ui.RESET}         - Change GGUF model from models folder")
            print(f"  {self.ui.YELLOW}/clear{self.ui.RESET}          - Reset chat history and conversation")
            print(f"  {self.ui.YELLOW}/files{self.ui.RESET}          - List files loaded in current session")
            print(f"  {self.ui.YELLOW}/add <file>{self.ui.RESET}     - Load file content directly into context")
            print(f"  {self.ui.YELLOW}/status{self.ui.RESET}        - View loaded model metadata and workspace path")
            print()
            
        elif cmd == '/clear':
            self.reset_conversation()
            self.ui.success("Chat conversation history cleared.")
            
        elif cmd == '/files':
            if not self.loaded_files:
                self.ui.info("No files loaded in the current chat history.")
            else:
                self.ui.info("Files currently in context:")
                for f in self.loaded_files:
                    print(f"  - {self.ui.YELLOW}{f}{self.ui.RESET}")
                    
        elif cmd == '/add':
            if not args:
                self.ui.error("Usage: /add <file-path>")
                return False
            file_to_add = " ".join(args)
            self.ui.start_spinner(f"Reading file: {file_to_add}...")
            content = self.tools.read_file(file_to_add)
            if content.startswith("Error"):
                self.ui.stop_spinner_error(content)
            else:
                self.ui.stop_spinner_success(f"Loaded {file_to_add} into context.")
                self.loaded_files.add(file_to_add)
                self.messages.append({
                    "role": "user",
                    "content": f"[Developer Injected Context for File: {file_to_add}]\n\n```\n{content}\n```\n\nUse this to help answer future questions."
                })
                self.messages.append({
                    "role": "assistant",
                    "content": f"Acknowledged. I have loaded {file_to_add} into my active context."
                })
                self.ui.success(f"Appended file context for: {file_to_add}")
                self.save_memory()
                
        elif cmd == '/status':
            print(f"\n{self.ui.CYAN}{self.ui.BOLD}System Status:{self.ui.RESET}")
            print(f"  Model      : {self.ui.YELLOW}{os.path.basename(self.model_path)}{self.ui.RESET}")
            print(f"  Family     : {self.ui.YELLOW}{self.model_family}{self.ui.RESET}")
            print(f"  Chat Format: {self.ui.YELLOW}{self.chat_format or 'auto'}{self.ui.RESET}")
            print(f"  Context    : {self.ui.YELLOW}{self.context_size} tokens{self.ui.RESET}")
            print(f"  Models Dir : {self.ui.YELLOW}{self.models_dir}{self.ui.RESET}")
            print(f"  Workspace  : {self.ui.YELLOW}{self.workspace_root}{self.ui.RESET}")
            print()
            
        elif cmd == '/switch':
            self.switch_model()
            
        else:
            self.ui.error(f"Unknown command: {cmd}. Type /help for available options.")
            
        return False

    def switch_model(self):
        if not os.path.exists(self.models_dir):
            self.ui.error(f"Models directory not found at: {self.models_dir}")
            return
            
        files = os.listdir(self.models_dir)
        gguf_files = sorted([f for f in files if f.endswith('.gguf')])
        
        if not gguf_files:
            self.ui.warning(f"No GGUF models found in models directory: {self.models_dir}")
            return
            
        print(f"\n{self.ui.CYAN}{self.ui.BOLD}Available GGUF Models:{self.ui.RESET}")
        current_basename = os.path.basename(self.model_path)
        for idx, file in enumerate(gguf_files):
            fpath = os.path.join(self.models_dir, file)
            size_gb = os.path.getsize(fpath) / (1024**3)
            profile = self.get_model_profile(fpath)
            tag = f" {self.ui.MAGENTA}[loaded]{self.ui.RESET}" if file == current_basename else ""
            ram_color = self.ui.RED if profile["ram_gb"] > self.TOTAL_RAM_GB * 0.85 else self.ui.GREEN
            print(f"  [{idx + 1}] {self.ui.GREEN}{file}{self.ui.RESET}{tag}")
            print(f"      {self.ui.DIM}{profile['family']}  |  {size_gb:.1f} GB  |  ~{ram_color}{profile['ram_gb']:.0f} GB RAM{self.ui.RESET}")
            
        choice = self.ui.prompt_input(f"\n{self.ui.YELLOW}Select new model index (or Enter to cancel): {self.ui.RESET}").strip()
        if choice == "":
            return
            
        try:
            choice_idx = int(choice) - 1
            if choice_idx < 0 or choice_idx >= len(gguf_files):
                self.ui.error("Invalid selection index.")
                return
        except ValueError:
            self.ui.error("Please enter a valid number.")
            return
            
        new_model_path = os.path.join(self.models_dir, gguf_files[choice_idx])
        
        if new_model_path == self.model_path:
            self.ui.info("That model is already loaded.")
            return

        self.ui.info("Unloading current model from memory...")
        self.llm = None
        gc.collect()
        
        self.model_path = new_model_path
        self.initialize()
        self.ui.success(f"Successfully switched to: {os.path.basename(new_model_path)}")

    def run_agent_loop(self, user_msg):
        self.messages.append({"role": "user", "content": user_msg})
        self.save_memory()
        keep_running = True
        
        while keep_running:
            self.ui.info("\n🤖 AI is thinking...")
            print(f"{self.ui.GREEN}{self.ui.BOLD}AI: {self.ui.RESET}", end="", flush=True)
            
            response_text = ""
            try:
                stream = self.llm.create_chat_completion(
                    messages=self.messages,
                    stream=True,
                    temperature=0.7,
                    max_tokens=2048
                )
                
                for chunk in stream:
                    content = chunk["choices"][0]["delta"].get("content", "")
                    if content:
                        response_text += content
                        print(content, end="", flush=True)
                        
                print()
                self.messages.append({"role": "assistant", "content": response_text})
                self.save_memory()
                tool_calls = self.parse_tool_calls(response_text)
                
                if not tool_calls:
                    keep_running = False
                else:
                    results = []
                    for call in tool_calls:
                        tool_name = call["tool"]
                        params = call["params"]
                        
                        approved = self.ui.confirm(
                            f"Allow AI to run tool: {self.ui.MAGENTA}{tool_name}{self.ui.RESET} with parameters {repr(params)}?",
                            default_to_yes=False
                        )
                        
                        if approved:
                            self.ui.start_spinner(f"Executing {tool_name}...")
                            result = self.execute_tool(tool_name, params)
                            self.ui.stop_spinner_success(f"Completed {tool_name}.")
                            results.append({
                                "tool": tool_name,
                                "params": params,
                                "status": "success",
                                "result": result
                            })
                        else:
                            self.ui.warning(f"Permission denied by user for: {tool_name}")
                            results.append({
                                "tool": tool_name,
                                "params": params,
                                "status": "denied",
                                "result": "Error: Permission Denied by User."
                            })
                            
                    feedback_str = "[Tool Execution Results]\n\n"
                    for res in results:
                        feedback_str += f"Tool: {res['tool']}\nParameters: {repr(res['params'])}\nStatus: {res['status']}\nResult:\n{res['result']}\n\n"
                    feedback_str += "Please review these results and continue your coding task."
                    self.messages.append({"role": "user", "content": feedback_str})
                    self.save_memory()
                    
            except Exception as e:
                self.ui.error(f"Inference error during execution: {str(e)}")
                keep_running = False

    def parse_tool_calls(self, text):
        calls = []
        
        write_matches = re.finditer(r'<write_file\s+path="([^"]+)">([\s\S]*?)<\/write_file>', text)
        for m in write_matches:
            calls.append({
                "index": m.start(),
                "tool": "write_file",
                "params": {"path": m.group(1), "content": m.group(2).strip()}
            })
            
        read_matches = re.finditer(r'<read_file\s+path="([^"]+)"\s*\/>', text)
        for m in read_matches:
            calls.append({
                "index": m.start(),
                "tool": "read_file",
                "params": {"path": m.group(1)}
            })
            
        list_matches = re.finditer(r'<list_dir\s+path="([^"]+)"\s*\/>', text)
        for m in list_matches:
            calls.append({
                "index": m.start(),
                "tool": "list_dir",
                "params": {"path": m.group(1)}
            })
            
        search_matches = re.finditer(r'<search_files\s+query="([^"]+)"\s*\/>', text)
        for m in search_matches:
            calls.append({
                "index": m.start(),
                "tool": "search_files",
                "params": {"query": m.group(1)}
            })
            
        run_matches = re.finditer(r'<run_command\s+cmd="([^"]+)"\s*\/>', text)
        for m in run_matches:
            calls.append({
                "index": m.start(),
                "tool": "run_command",
                "params": {"cmd": m.group(1)}
            })
            
        calls.sort(key=lambda x: x["index"])
        return calls

    def execute_tool(self, tool_name, params):
        if tool_name == "read_file":
            self.loaded_files.add(params["path"])
            return self.tools.read_file(params["path"])
        elif tool_name == "write_file":
            self.loaded_files.add(params["path"])
            return self.tools.write_file(params["path"], params["content"])
        elif tool_name == "list_dir":
            return self.tools.list_dir(params["path"])
        elif tool_name == "search_files":
            return self.tools.search_files(params["query"])
        elif tool_name == "run_command":
            return self.tools.run_command(params["cmd"])
        else:
            return f"Error: Unknown tool name {tool_name}"
