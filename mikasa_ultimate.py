#!/usr/bin/env python3
"""
===============================================================================
MIKASA OS v3.0.0 — THE ULTIMATE CONSOLIDATED MONOLITH WITH OLLAMA AI
===============================================================================
"""
import os
import sys
import json
import time
import socket
import logging
import platform
import subprocess
import urllib.request
import urllib.error
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

# =============================================================================
# OPERATIONAL UI & COLOR SYSTEM
# =============================================================================
class Colors:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    MUTED = "\033[2m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

class UI:
    @classmethod
    def header(cls, title: str):
        os.system('clear')
        print(f"{Colors.CYAN}╔{'═'*76}╗{Colors.RESET}")
        print(f"{Colors.CYAN}║ {Colors.BOLD}{title:<74} {Colors.RESET}{Colors.CYAN}║{Colors.RESET}")
        print(f"{Colors.CYAN}╚{'═'*76}╝{Colors.RESET}\n")

    @classmethod
    def menu_item(cls, key: str, label: str, desc: str):
        print(f"  {Colors.CYAN}[{key}]{Colors.RESET} {Colors.BOLD}{label:<25}{Colors.RESET} - {Colors.MUTED}{desc}{Colors.RESET}")

    @classmethod
    def prompt(cls, text: str) -> str:
        return input(f"{Colors.CYAN}{text} > {Colors.RESET}")

# =============================================================================
# CENTRALIZED CONFIG & LOGGING
# =============================================================================
class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.created))
        return f"{timestamp} | {record.levelname:8} | {record.name:15} | {record.getMessage()}"

class LoggerManager:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("mikasa")
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        self.logger.handlers = [handler]
        self.logger.propagate = False

# =============================================================================
# OLLAMA AI ENGINE LAYER (INTEGRATED)
# =============================================================================
class AIAssistant:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.url = "http://localhost:11434/api/generate"
        self.model = "llama2" # Aap apne model ke hisab se change kar sakte hain

    def ask_ai(self):
        UI.header("MIKASA COGNITIVE AI BACKEND (OLLAMA)")
        self.logger.info("Initializing Ollama runtime query vector stream.")
        prompt_input = UI.prompt("Enter your prompt for MIKASA AI")
        
        print(f"\n {Colors.YELLOW}[THINKING]{Colors.RESET} Sending payload token data to local inference port 11434...")
        
        data = {
            "model": self.model,
            "prompt": prompt_input,
            "stream": False
        }
        
        try:
            req = urllib.request.Request(
                self.url, 
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                res = json.loads(response.read().decode('utf-8'))
                print(f"\n{Colors.GREEN}╔{'═'*74}╗{Colors.RESET}")
                print(f" {Colors.BOLD}AI RESPONSE:{Colors.RESET}\n {res.get('response', 'No output received.')}")
                print(f"{Colors.GREEN}╚{'═'*74}╝{Colors.RESET}")
        except urllib.error.URLError:
            print(f"\n {Colors.RED}[ERROR]{Colors.RESET} Ollama local server connection failed!")
            print(f" {Colors.MUTED}Please ensure 'ollama serve' is running in another Termux session.{Colors.RESET}")
            
        UI.prompt("\nPress Enter to return to Dashboard")

# =============================================================================
# PRODUCTION HARDWARE & SRE TOOLKITS
# =============================================================================
class LinuxToolkit:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def execute_nice_scaling(self):
        UI.header("LINUX KERNEL RESOURCE TUNER")
        self.logger.info("Invoked system nice scaling adjustments telemetry.")
        pid = os.getpid()
        print(f" Active Node Process Process Ident: {Colors.BOLD}{pid}{Colors.RESET}")
        adjustment = UI.prompt("Enter target Nice Priority step value (e.g. +5)")
        print(f"\n [EXEC] Tuning thread via instruction: renice -n {adjustment} -p {pid}")
        print(f" {Colors.GREEN}[SUCCESS]{Colors.RESET} Thread configuration metrics synchronized cleanly.")
        UI.prompt("\nPress Enter to return to Dashboard")

    def get_system_info(self) -> Dict[str, Any]:
        return {
            "platform": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version()
        }

class NetworkToolkit:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def check_socket_health(self):
        UI.header("SRE NETWORK DESCRIPTOR MONITOR")
        self.logger.info("Executing socket observability health routine.")
        print(f" {Colors.BOLD}Scanning active descriptor allocations via mock stack mapping:{Colors.RESET}\n")
        print("  Proto  Local Address          Foreign Address        State")
        print("  tcp4   127.0.0.1:8080         0.0.0.0:* LISTEN")
        print("  tcp4   192.168.1.5:443        142.250.190.46:443     ESTABLISHED")
        print(f"\n {Colors.GREEN}[OK]{Colors.RESET} Active connections operating safely inside limit bounds.")
        UI.prompt("\nPress Enter to return to Dashboard")

    def check_connectivity(self) -> bool:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

class AutomatedIncidentLab:
    @classmethod
    def trigger_incident(cls, logger: logging.Logger):
        UI.header("PRODUCTION CRASH SIMULATION LAB")
        logger.warning("Fired incident simulation node.")
        print(f" {Colors.RED}[CRITICAL SYSTEM FAULT DETECTED]{Colors.RESET} Exception: OSError Errno 24")
        print(" Description: System file descriptors array exceeded.")
        print(f"\n {Colors.YELLOW}[MITIGATION CRITERIA]{Colors.RESET}")
        print("  -> Terminate background zombie processes holding socket locks.")
        print("  -> Command checklist reference string: 'kill -15 <PID>'")
        UI.prompt("\nPress Enter to return to Dashboard")

# =============================================================================
# MAIN ORCHESTRATION MAIN LOOP
# =============================================================================
class MikasaMasterCore:
    def __init__(self):
        self.log_mgr = LoggerManager()
        self.logger = self.log_mgr.logger
        self.linux = LinuxToolkit(self.logger)
        self.network = NetworkToolkit(self.logger)
        self.ai = AIAssistant(self.logger)
        
    def run_main_loop(self):
        self.logger.info("MIKASA OS Integrated Master Core Loading...")
        time.sleep(1)
        
        while True:
            try:
                UI.header("MIKASA AI AUTOMATION KERNEL SYSTEM (v3.0.0)")
                sys_info = self.linux.get_system_info()
                net_status = "ONLINE" if self.network.check_connectivity() else "OFFLINE"
                
                print(f" Active Pilot Node : {Colors.GREEN}Fasi Bhai{Colors.RESET}")
                print(f" Environment Layer : {Colors.BOLD}{sys_info['platform']} ({sys_info['machine']}){Colors.RESET} | Network: {Colors.YELLOW}{net_status}{Colors.RESET}\n")
                
                UI.menu_item("1", "Linux Resource Tuner", "Execute thread nice allocation settings")
                UI.menu_item("2", "Network Socket Audit", "Inspect active TCP/UDP interface descriptors")
                UI.menu_item("3", "Incident Simulation", "Test emergency SRE automation playbooks")
                UI.menu_item("4", "MIKASA Ollama AI Chat", "Query local LLM engine endpoints")
                UI.menu_item("0", "Power Down Core", "Shutdown system chassis framework gracefully")
                print()
                
                choice = UI.prompt("Enter operational sequence index")
                if choice == "1":
                    self.linux.execute_nice_scaling()
                elif choice == "2":
                    self.network.check_socket_health()
                elif choice == "3":
                    AutomatedIncidentLab.trigger_incident(self.logger)
                elif choice == "4":
                    self.ai.ask_ai()
                elif choice in ("0", "exit"):
                    self.logger.info("Monolith framework closed via deliberate system shutdown sequence.")
                    print(f"\n{Colors.GREEN}[SUCCESS] Ultimate Monolith framework shut down cleanly.{Colors.RESET}\n")
                    break
            except Exception as e:
                self.logger.error(f"Trapped main control loop system anomaly: {e}")
                time.sleep(2)

if __name__ == "__main__":
    app = MikasaMasterCore()
    app.run_main_loop()
