import asyncio
import sys
from pathlib import Path
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from yaml import YAMLError

from discopy.utils import tuplify

from .loader import repl_read
from .files import diagram_draw, file_diagram
from .widish import SHELL_RUNNER
from .compiler import SHELL_COMPILER, force


# TODO watch functor ??

class ShellHandler(FileSystemEventHandler):
    """Reload the shell on change."""
    def __init__(self, loop, queue):
        self.loop = loop
        self.queue = queue

    def on_modified(self, event):
        if event.src_path.endswith(".yaml"):
            self.loop.call_soon_threadsafe(self.queue.put_nowait, event)

async def handle_events(queue):
    while True:
        event = await queue.get()
        print(f"reloading {event.src_path}")
        try:
            fd = file_diagram(str(event.src_path))
            diagram_draw(Path(event.src_path), fd)
            diagram_draw(Path(event.src_path+".2"), fd)
        except YAMLError as e:
            print(e)
        queue.task_done()

async def async_shell_main(file_name):
    path = Path(file_name)
    loop = asyncio.get_running_loop()
    queue = asyncio.Queue()

    # Start observer
    print(f"watching for changes in current path")
    event_handler = ShellHandler(loop, queue)
    observer = Observer()
    observer.schedule(event_handler, ".", recursive=True)
    observer.start()

    # Start event consumer
    consumer_task = asyncio.create_task(handle_events(queue))

    try:
        while True:
            try:
                prompt = f"--- !{file_name}\n"
                # Use run_in_executor for blocking input
                source = await loop.run_in_executor(None, input, prompt)
                
                source_d = repl_read(source)
                if __debug__:
                    diagram_draw(path, source_d)
                compiled_d = source_d
                # compiled_d = SHELL_COMPILER(source_d)
                # if __debug__:
                #     diagram_draw(path.with_suffix(".shell.yaml"), compiled_d)
                constants = tuple(x.name for x in compiled_d.dom)
                result_ev = SHELL_RUNNER(compiled_d)(*constants)
                print(force(result_ev))
            except EOFError:
                print("⌁")
                break
            except KeyboardInterrupt:
                print()
            except YAMLError as e:
                print(e)
    finally:
        observer.stop()
        observer.join()
        consumer_task.cancel()

async def async_widish_main(file_name, *shell_program_args: str):
    loop = asyncio.get_running_loop()
    
    fd = file_diagram(file_name)
    path = Path(file_name)
    if __debug__:
        diagram_draw(path, fd)
    constants = tuple(x.name for x in fd.dom)
    fd = SHELL_COMPILER(fd)
    if __debug__:
        diagram_draw(path.with_suffix(".shell.yaml"), fd)
    runner = SHELL_RUNNER(fd)(*constants)

    if sys.stdin.isatty():
        inp = ""
    else:
        inp = await loop.run_in_executor(None, sys.stdin.read)
        
    run_res = runner(inp)
    val = force(run_res)
    print(*(tuple(x.rstrip() for x in tuplify(val) if x)), sep="\n")

def widish_main(file_name, *shell_program_args: str):
    # Deprecated sync wrapper
    asyncio.run(async_widish_main(file_name, *shell_program_args))

async def main():
    match sys.argv:
        case [_]:
            try:
                await async_shell_main("bin/yaml/shell.yaml")
            except KeyboardInterrupt:
                pass
        case [_, file_name, *args]: 
            await async_widish_main(file_name, *args)
