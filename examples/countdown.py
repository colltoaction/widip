import sys

for line in sys.stdin:
    line = line.strip()
    if not line: continue
    # Ignore cycle detection thunk strings
    if "<function" in line: continue

    try:
        if line == "Liftoff!":
            continue
        n = int(line)
        if n > 1:
            print(n - 1, flush=True)
        elif n == 1:
            print("Liftoff!", flush=True)
    except ValueError:
        pass
