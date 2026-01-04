#!/bin/sh
# Monoidal Computer - Shell Bootstrapping
printf "\033[1;34m[System]\033[0m Booting Monoidal Computer (Shell)...\n" >&2
printf "\033[1;32m[Runtime]\033[0m $(sh --version | head -n 1)\n" >&2
printf "\033[1;34m[System]\033[0m Ready.\n" >&2
