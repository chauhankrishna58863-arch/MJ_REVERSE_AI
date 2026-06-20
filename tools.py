import os
import json
import subprocess

class AgentTools:
    def __init__(self, workspace_root):
        self.workspace_root = os.path.abspath(workspace_root)

    def _resolve_safe_path(self, relative_path):
        resolved = os.path.abspath(os.path.join(self.workspace_root, relative_path))
        if not resolved.startswith(self.workspace_root):
            raise PermissionError(f"Access Denied: Path escapes workspace root ({resolved})")
        return resolved

    def read_file(self, file_path):
        try:
            safe_path = self._resolve_safe_path(file_path)
            if not os.path.exists(safe_path):
                return f"Error: File not found at '{file_path}'"
            if not os.path.isfile(safe_path):
                return f"Error: '{file_path}' is a directory, not a file."
            
            with open(safe_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def write_file(self, file_path, content):
        try:
            safe_path = self._resolve_safe_path(file_path)
            parent_dir = os.path.dirname(safe_path)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            
            with open(safe_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Success: Written file successfully to '{file_path}' ({len(content)} characters)."
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def list_dir(self, dir_path="."):
        try:
            safe_path = self._resolve_safe_path(dir_path)
            if not os.path.exists(safe_path):
                return f"Error: Directory not found at '{dir_path}'"
            
            items = os.listdir(safe_path)
            results = []
            for item in items:
                full_path = os.path.join(safe_path, item)
                rel_path = os.path.relpath(full_path, self.workspace_root).replace('\\', '/')
                is_dir = os.path.isdir(full_path)
                results.append({
                    "name": item,
                    "path": rel_path,
                    "type": "directory" if is_dir else "file",
                    "size": os.path.getsize(full_path) if not is_dir else None
                })
            return json.dumps(results, indent=2)
        except Exception as e:
            return f"Error listing directory: {str(e)}"

    def search_files(self, query, dir_path="."):
        try:
            start_path = self._resolve_safe_path(dir_path)
            results = []
            
            for root, dirs, files in os.walk(start_path):
                dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '.gradle', '.idea', '__pycache__', 'local-code-ai-py']]
                
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.workspace_root).replace('\\', '/')
                    
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if query.lower() in content.lower():
                                lines = content.split('\n')
                                matches = []
                                for idx, line in enumerate(lines):
                                    if query.lower() in line.lower():
                                        matches.append({
                                            "lineNum": idx + 1,
                                            "content": line.strip()
                                        })
                                if matches:
                                    results.append({
                                        "file": rel_path,
                                        "matches": matches[:10]
                                    })
                    except Exception:
                        continue
            
            return json.dumps(results, indent=2) if results else f"No matches found for query: \"{query}\""
        except Exception as e:
            return f"Error searching files: {str(e)}"

    def run_command(self, cmd):
        try:
            if cmd.strip().startswith('cd '):
                return f"Error: 'cd' command is not supported. All commands run in the workspace context: {self.workspace_root}"
            
            process = subprocess.run(
                cmd,
                shell=True,
                cwd=self.workspace_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60
            )
            
            stdout = process.stdout or ""
            stderr = process.stderr or ""
            return f"Exit code: {process.returncode}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 60 seconds."
        except Exception as e:
            return f"Error running command: {str(e)}"
