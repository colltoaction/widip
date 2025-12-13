import subprocess
import time
import os
import sys

def test_interactive_session():
    os.makedirs("bin/yaml", exist_ok=True)
    img = "bin/yaml/shell.jpg"
    if os.path.exists(img): os.remove(img)

    p = subprocess.Popen([sys.executable, "-m", "widip"],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    try:
        time.sleep(1)
        for cmd in ["x: y\n", "a: b\n"]:
            p.stdin.write(cmd)
            p.stdin.flush()
            time.sleep(2) # wait for render
            assert os.path.exists(img), f"Image not created for {cmd.strip()}"

        p.stdin.close()
        p.wait(timeout=5)
        assert p.returncode == 0
        print("Test passed!")
    finally:
        if p.poll() is None: p.kill()

if __name__ == "__main__":
    test_interactive_session()
