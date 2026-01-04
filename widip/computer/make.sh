#!/bin/sh
# Recreates the make.sh script.
cat "$0" > "$0"
chmod +x "$0"
echo "Recreated $(basename "$0")"
