import sys
import time
import threading

class UI:
    def __init__(self):
        # ANSI Escape Sequences for Terminal Colors
        self.CYAN = "\033[96m"
        self.GREEN = "\033[92m"
        self.YELLOW = "\033[93m"
        self.RED = "\033[91m"
        self.BLUE = "\033[94m"
        self.MAGENTA = "\033[95m"
        self.BOLD = "\033[1m"
        self.UNDERLINE = "\033[4m"
        self.DIM = "\033[2m"
        self.RESET = "\033[0m"

        self.spinner_thread = None
        self.spinner_running = False

    def print_header(self, version):
        border = "=" * 70
        title = f"{self.CYAN}{self.BOLD}[ MJ REVERSE AI ]{self.RESET}"
        subtitle = f"{self.DIM}Offline Python AI Agent for local .gguf models{self.RESET}"
        ver_info = f"{self.GREEN}Version {version}{self.RESET}"
        ws_info = f"{self.DIM}Workspace: {self.UNDERLINE}{sys.path[0] or '.'}{self.RESET}"

        print(f"\n{self.CYAN}{border}{self.RESET}")
        print(f"  {title}")
        print(f"  {subtitle}")
        print(f"  {ver_info}")
        print(f"  {ws_info}")
        print(f"{self.CYAN}{border}{self.RESET}\n")

    def success(self, message):
        print(f"{self.GREEN}{self.BOLD}[OK]{self.RESET} {self.GREEN}{message}{self.RESET}")

    def error(self, message):
        print(f"{self.RED}{self.BOLD}[ERROR]{self.RESET} {self.RED}{message}{self.RESET}", file=sys.stderr)

    def warning(self, message):
        print(f"{self.YELLOW}{self.BOLD}[WARN]{self.RESET} {self.YELLOW}{message}{self.RESET}")

    def info(self, message):
        print(f"{self.BLUE}{self.BOLD}[INFO]{self.RESET} {self.CYAN}{message}{self.RESET}")

    def _spin_worker(self, text):
        chars = ["|", "/", "-", "\\"]
        idx = 0
        while self.spinner_running:
            sys.stdout.write(f"\r{self.CYAN}{self.BOLD}{chars[idx]}{self.RESET} {self.DIM}{text}{self.RESET}")
            sys.stdout.flush()
            idx = (idx + 1) % len(chars)
            time.sleep(0.1)
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()

    def start_spinner(self, text):
        if self.spinner_running:
            self.stop_spinner_success("Updated spinner")
        self.spinner_running = True
        self.spinner_thread = threading.Thread(target=self._spin_worker, args=(text,), daemon=True)
        self.spinner_thread.start()

    def stop_spinner_success(self, text):
        self.spinner_running = False
        if self.spinner_thread:
            self.spinner_thread.join()
            self.spinner_thread = None
        self.success(text)

    def stop_spinner_error(self, text):
        self.spinner_running = False
        if self.spinner_thread:
            self.spinner_thread.join()
            self.spinner_thread = None
        self.error(text)

    def prompt_input(self, question_text):
        try:
            return input(question_text)
        except (KeyboardInterrupt, EOFError):
            print()
            return "/exit"

    def confirm(self, prompt_text, default_to_yes=False):
        suffix = " [Y/n]" if default_to_yes else " [y/N]"
        question = f"\n{self.YELLOW}{self.BOLD}{prompt_text}{self.RESET}{self.DIM}{suffix}{self.RESET}: "
        answer = self.prompt_input(question).strip().lower()
        
        if answer == "":
            return default_to_yes
        return answer in ["y", "yes"]

    def print_tool_call(self, tool_name, parameters):
        border = "-" * 60
        print(f"\n{self.YELLOW}{border}{self.RESET}")
        print(f"{self.YELLOW}{self.BOLD}[TOOL CALL]: {self.MAGENTA}{tool_name}{self.RESET}")
        for k, v in parameters.items():
            print(f"  {self.CYAN}{k}{self.RESET}: {self.RESET}{repr(v)}")
        print(f"{self.YELLOW}{border}{self.RESET}")

    def format_markdown(self, text):
        lines = text.split("\n")
        formatted_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                lang = line.strip().replace("```", "")
                label = f"[{lang.upper()}]" if lang else "[CODE]"
                formatted_lines.append(f"{self.CYAN}{self.BOLD}{label}{self.RESET}")
                continue
            
            if in_code_block:
                formatted_lines.append(f"{self.GREEN}  {line}{self.RESET}")
            else:
                parts = line.split("`")
                new_line = ""
                for idx, part in enumerate(parts):
                    if idx % 2 == 1:
                        new_line += f"{self.YELLOW}{part}{self.RESET}"
                    else:
                        new_line += part
                
                if new_line.startswith("# "):
                    new_line = f"\n{self.CYAN}{self.BOLD}{self.UNDERLINE}{new_line[2:]}{self.RESET}\n"
                elif new_line.startswith("## "):
                    new_line = f"\n{self.CYAN}{self.BOLD}{new_line[3:]}{self.RESET}\n"
                elif new_line.startswith("### "):
                    new_line = f"\n{self.CYAN}{self.BOLD}{self.DIM}{new_line[4:]}{self.RESET}\n"
                    
                formatted_lines.append(new_line)
                
        return "\n".join(formatted_lines)
