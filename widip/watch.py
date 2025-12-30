import asyncio
import sys

from .files import reload_diagram


async def handle_changes():
    from watchfiles import awatch
    async for changes in awatch('.', recursive=True):
        for change_type, path_str in changes:
            if path_str.endswith(".yaml"):
                reload_diagram(path_str)

async def run_with_watcher(coro):
    # Start watcher
    watcher_task = None
    if __debug__:
        if sys.stdin.isatty():
            print(f"watching for changes in current path", file=sys.stderr)
        watcher_task = asyncio.create_task(handle_changes())

    try:
        await coro
    finally:
        if watcher_task:
            watcher_task.cancel()
            try:
                await watcher_task
            except asyncio.CancelledError:
                pass
