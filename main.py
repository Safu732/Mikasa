#!/usr/bin/env python3
"""
MIKASA OS v4.2.0
================
A cyberpunk-inspired AI-powered developer terminal built entirely on Android using Termux.
Now with Unified Cross-Language Compilers (Java, C, C++, HTML) & Standardized Error Mapping.

Architecture: Modular, single-file deployable with unified sub-systems.
"""

from __future__ import annotations

import abc
import json
import logging
import logging.handlers
import os
import pathlib
import subprocess
import sys
import textwrap
import threading
import traceback
import typing
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Union

# ──────────────────────────────────────────────────────────────
# SECTION 0: Dependency Guard & Fallback Matrix
# ──────────────────────────────────────────────────────────────

try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text
    from rich.traceback import install as install_rich_traceback
    install_rich_traceback(show_locals=True)
    _HAS_RICH = True
except ImportError:
    _HAS_RICH = False

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

# ──────────────────────────────────────────────────────────────
# SECTION 1: Config Schema & Manager
# ──────────────────────────────────────────────────────────────

@dataclass
class ConfigSchema:
    version: str = "4.2.0"
    theme: str = "cyberpunk"
    ollama_host: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:3b"
    plugins_dir: str = "plugins"
    logs_dir: str = "logs"
    prompt_ask: str = "You are MIKASA OS AI terminal assistant. Answer concisely."

    def to_dict(self) -> Dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in self.__dataclass_fields__.values()}

class ConfigManager:
    def __init__(self) -> None:
        self.config = ConfigSchema()

# ──────────────────────────────────────────────────────────────
# SECTION 2: Native Ollama Client (No Rust/Pydantic Dependencies)
# ──────────────────────────────────────────────────────────────

class OllamaClient:
    """Lightweight API client bypassing high-memory dependencies via requests."""
    def __init__(self, config: ConfigSchema) -> None:
        self.config = config
        self.base_url = config.ollama_host

    @property
    def is_available(self) -> bool:
        if not _HAS_REQUESTS: return False
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        if not self.is_available: return []
        try:
            resp = requests.get(f"{self.base_url}/api/tags")
            return [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            return []

    def chat_stream(self, prompt: str) -> typing.Generator[str, None, None]:
        payload = {
            "model": self.config.ollama_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True
        }
        try:
            resp = requests.post(f"{self.base_url}/api/chat", json=payload, stream=True)
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    data = json.loads(line)
                    content = data.get("message", {}).get("content", "")
                    if content: yield content
                    if data.get("done"): break
        except Exception as e:
            yield f"Connection Error: {e}"

# ──────────────────────────────────────────────────────────────
# SECTION 3: Cross-Language Compiler Engine (Java/C++/C/HTML)
# ──────────────────────────────────────────────────────────────

class CrossLanguageEngine:
    """Compiles and executes files while routing errors to a unified standard format."""
    def __init__(self, ui: TerminalUI) -> None:
        self.ui = ui

    def format_exception(self, lang: str, error_msg: str) -> str:
        """Standardizes error shapes for all target coding languages."""
        return f"[bold red][!] {lang.upper()} RUNTIME EXCEPTION[/bold red]\n[dim]Logs:[/dim] {error_msg.strip()}"

    def execute_pipeline(self, lang: str, file_path: str) -> None:
        lang = lang.lower().strip()
        path = pathlib.Path(file_path)

        if not path.exists():
            self.ui.error(f"Target file not found: {file_path}")
            return

        # Core logic separation based on language target hardware binary maps
        if lang == "java":
            cmd = f"javac {file_path} && java {path.stem}"
        elif lang in ["c", "cpp", "c++"]:
            compiler = "clang++" if lang != "c" else "clang"
            cmd = f"{compiler} {file_path} -o temp_bin && ./temp_bin"
        elif lang == "html":
            # Validates basic structural layout mapping via lightweight inline Python script
            cmd = f"python3 -c 'from bs4 import BeautifulSoup; BeautifulSoup(open(\"{file_path}\"), \"lxml\")'"
        else:
            self.ui.error(f"Compiler engine does not support language: '{lang}'")
            return

        self.ui.info(f"Invoking native system compilers for {lang.upper()}...")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            
            if result.returncode != 0:
                # Catching execution error and transforming it into uniform shape
                self.ui.print(self.format_exception(lang, result.stderr))
            else:
                self.ui.success(f"{lang.upper()} Process Executed Cleanly!")
                if result.stdout:
                    self.ui.print(result.stdout)
                    
            # Clean up compiled binaries if exist
            if os.path.exists("temp_bin"): os.remove("temp_bin")
            if os.path.exists(f"{path.stem}.class"): os.remove(f"{path.stem}.class")

        except subprocess.TimeoutExpired:
            self.ui.print(self.format_exception(lang, "Execution timed out (Max limit: 15s)."))
        except Exception as e:
            self.ui.print(self.format_exception(lang, str(e)))

# ──────────────────────────────────────────────────────────────
# SECTION 4: Base Plugin & System Layer
# ──────────────────────────────────────────────────────────────

class BasePlugin(abc.ABC):
    name: str = "base"
    version: str = "1.0.0"
    description: str = "Base plugin schema"

    @abc.abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    def info(self) -> Dict[str, str]:
        return {"name": self.name, "version": self.version, "description": self.description}

# ──────────────────────────────────────────────────────────────
# SECTION 5: Terminal UI Layer
# ──────────────────────────────────────────────────────────────

class TerminalUI:
    def __init__(self, config: ConfigSchema) -> None:
        self.config = config
        self.console = Console()

    def banner(self) -> None:
        banner_text = textwrap.dedent(
            """
            ███╗   ███╗██╗██╗  ██╗ █████╗ ███████╗ █████╗     ██████╗ ███████╗
            ████╗ ████║██║██║ ██╔╝██╔══██╗██╔════╝██╔══██╗    ██╔══██╗██╔════╝
            ██╔████╔██║██║█████╔╝ ███████║███████╗███████║    ██║  ██║███████╗
            ██║╚██╔╝██║██║██╔═██╗ ██╔══██║╚════██║██╔══██║    ██║  ██║╚════██║
            ██║ ╚═╝ ██║██║██║  ██╗██║  ██║███████║██║  ██║    ██████╔╝███████║
            ╚═╝     ╚═╝╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝    ╚═════╝ ╚══════╝
            """
        )
        self.console.print(Panel(Text(banner_text, style="bold bright_cyan"), border_style="cyan", subtitle=f"v{self.config.version} | Compiler & AI Active Hub"))

    def print(self, text: str) -> None: self.console.print(text)
    def success(self, text: str) -> None: self.console.print(f"[bold bright_green]✓ {text}[/]")
    def error(self, text: str) -> None: self.console.print(f"[bold bright_red]✗ {text}[/]")
    def info(self, text: str) -> None: self.console.print(f"[dim cyan]{text}[/]")

    def prompt(self, message: str) -> str:
        return Prompt.ask(f"[bright_cyan]{message}[/]")

    def live_ai_stream(self, generator: typing.Generator[str, None, None]) -> None:
        full_text = ""
        with Live(console=self.console, refresh_per_second=10) as live:
            for chunk in generator:
                full_text += chunk
                live.update(Panel(Text(full_text, style="bright_cyan"), border_style="cyan", title="[bold]Local Qwen AI Engine[/]"))

# ──────────────────────────────────────────────────────────────
# SECTION 6: System Orchestrator & Main Core Loop
# ──────────────────────────────────────────────────────────────

class MikasaOS:
    def __init__(self) -> None:
        self.config_mgr = ConfigManager()
        self.config = self.config_mgr.config
        self.ui = TerminalUI(self.config)
        self.ai = OllamaClient(self.config)
        self.compiler = CrossLanguageEngine(self.ui)
        self._running = False

    def run(self) -> None:
        self._running = True
        os.system("clear")
        self.ui.banner()

        if not self.ai.is_available:
            self.ui.error("Ollama Core Offline! AI features require 'ollama serve' in background.")

        self.ui.print("\n[bold bright_green]MIKASA OS Core Booted Successfully.[/]\n")

        while self._running:
            try:
                user_input = self.ui.prompt("MIKASA").strip()
                if not user_input: continue

                parts = user_input.split(maxsplit=2)
                cmd = parts[0].lower()

                # Router rules matrix
                if cmd == "exit":
                    self.ui.print("[bold bright_cyan]Deactivating core engine... Goodbye, Pilot.[/]")
                    self._running = False
                elif cmd == "clear":
                    os.system("clear")
                    self.ui.banner()
                elif cmd == "status":
                    self.ui.success(f"Version: {self.config.version} | Ollama Server Status: {'Online' if self.ai.is_available else 'Offline'}")
                elif cmd == "ask":
                    if len(parts) < 2:
                        self.ui.error("Usage: ask <your query>")
                        continue
                    self.ui.live_ai_stream(self.ai.chat_stream(parts[1]))
                elif cmd == "compile":
                    # Unified Language Execution Hook
                    # Usage: compile <java|c|cpp|html> <file_path>
                    if len(parts) < 3:
                        self.ui.error("Usage: compile <java|c|cpp|html> <file_path>")
                        continue
                    self.compiler.execute_pipeline(parts[1], parts[2])
                else:
                    self.ui.error(f"Unknown system array instruction: '{cmd}'")

            except KeyboardInterrupt:
                self.ui.print("\n[bold yellow]SIGINT intercepted. Use 'exit' command to cleanly power off.[/]")
            except Exception as e:
                self.ui.print(f"[bold red]Core Exception Unhandled: {e}[/]")

if __name__ == "__main__":
    app = MikasaOS()
    app.run()
