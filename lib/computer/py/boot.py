"""Monoidal Computer Boot Script (Python)."""
import time
import sys

def boot():
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    RESET = "\033[0m"

    print(f"{PURPLE}--- MONOIDAL COMPUTER PYTHON BOOT ---{RESET}")
    print(f"{BLUE}[INFO]{RESET} Python Interface {sys.version.split()[0]} detection...")
    time.sleep(0.1)
    print(f"{BLUE}[INFO]{RESET} Mapping categories to library/computer...")
    time.sleep(0.1)
    print(f"{CYAN}[SYSTEM]{RESET} Finalizing environment...")
    print(f"{GREEN}[READY]{RESET} System standing by.")
    print(f"{PURPLE}-------------------------------------{RESET}")

if __name__ == "__main__":
    boot()
