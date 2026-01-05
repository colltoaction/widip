import sys
from pathlib import Path
sys.path.append(str(Path.cwd() / "lib"))

from computer.yaml import load
from computer.exec import execute, titi_runner
import asyncio

async def main():
    yaml_src = "&hello !echo world\n---\n*hello"
    try:
        diag = load(yaml_src)
        print("Load successful")
    except UnboundLocalError as e:
        print(f"FAILED: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
