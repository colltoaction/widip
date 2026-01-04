import sys
import subprocess
import os

def main():
    """Run the native _yaml_parser binary."""
    # Find the binary relative to this file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parser_path = os.path.join(base_dir, "..", "yaml", "_yaml_parser")
    
    if not os.path.exists(parser_path):
        print(f"Error: Native parser binary not found at {parser_path}", file=sys.stderr)
        print("Please run 'make bootstrap' to build it.", file=sys.stderr)
        sys.exit(1)
    
    # Run the binary with same arguments
    # We don't use capture_output=True because we want it to be interactive/piped naturally
    try:
        # Pass stdin/stdout/stderr directly
        process = subprocess.Popen([parser_path] + sys.argv[1:])
        process.wait()
        sys.exit(process.returncode)
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print(f"Error executing parser: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
