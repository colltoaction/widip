# Makefile for Widip/Titi Monoidal Computer
# Entrypoint for bootstrapping and handling file dependencies

.PHONY: all bootstrap clean test install dev help parser examples
.DEFAULT_GOAL := help

# --- Configuration ---
PYTHON := python3
LEX := lex
YACC := yacc
CC := cc

# Directories
LIB_DIR := lib/computer
YAML_DIR := $(LIB_DIR)/yaml
PARSER_DIR := lib/yaml
SRC_DIR := src
BIN_DIR := bin
EXAMPLES_DIR := examples
HOME_DIR := home
TESTS_DIR := tests

# Source files
LEX_SRC := $(PARSER_DIR)/yaml.l
YACC_SRC := $(PARSER_DIR)/yaml.y

# Generated files
LEX_OUT := $(PARSER_DIR)/lex.yy.c
YACC_OUT := $(PARSER_DIR)/y.tab.c
YACC_HEADER := $(PARSER_DIR)/y.tab.h
PARSER_BIN := $(PARSER_DIR)/_yaml_parser

# YAML files
YAML_FILES := $(shell find $(EXAMPLES_DIR) -name '*.yaml' 2>/dev/null)
SVG_FILES := $(YAML_FILES:.yaml=.svg)

# --- Help Target ---
help: ## Show this help message
	@echo "╔════════════════════════════════════════════════════════════╗"
	@echo "║  Widip/Titi Monoidal Computer - Build System              ║"
	@echo "╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# --- Bootstrap Target ---
bootstrap: parser install ## Bootstrap the entire system (build parser + install)
	@echo "╔════════════════════════════════════════════════════════════╗"
	@echo "║  Bootstrap Complete - Monoidal Computer Ready              ║"
	@echo "╚════════════════════════════════════════════════════════════╝"

# --- Parser Build Targets ---
parser: $(PARSER_BIN) ## Build the YAML parser from lex/yacc sources
	@echo "✓ YAML parser built successfully"

$(LEX_OUT): $(LEX_SRC)
	@echo "→ Running lex on $(LEX_SRC)..."
	cd $(PARSER_DIR) && $(LEX) yaml.l

$(YACC_OUT) $(YACC_HEADER): $(YACC_SRC)
	@echo "→ Running yacc on $(YACC_SRC)..."
	cd $(PARSER_DIR) && $(YACC) -d yaml.y

$(PARSER_BIN): $(LEX_OUT) $(YACC_OUT)
	@echo "→ Compiling parser..."
	$(CC) $(LEX_OUT) $(YACC_OUT) -lfl -o $(PARSER_BIN)

# --- Installation Targets ---
install: ## Install Python package and dependencies
	@echo "→ Installing titi package..."
	$(PYTHON) -m pip install -e .

install-dev: install ## Install with development dependencies
	@echo "→ Installing development dependencies..."
	$(PYTHON) -m pip install -e ".[test]"

# --- Testing Targets ---
test: ## Run core tests
	@echo "→ Running pytest on core tests..."
	PYTHONPATH=$$PYTHONPATH:$(LIB_DIR)/../ $(PYTHON) -m pytest $(TESTS_DIR) --ignore=$(TESTS_DIR)/test_yaml_suite.py -v

test-suite: ## Run YAML Test Suite
	@echo "→ Running pytest on YAML Test Suite..."
	PYTHONPATH=$$PYTHONPATH:$(LIB_DIR)/../ $(PYTHON) -m pytest $(TESTS_DIR)/test_yaml_suite.py -v

test-quick: ## Run tests without verbose output
	@$(PYTHON) -m pytest $(TESTS_DIR) --ignore=$(TESTS_DIR)/test_yaml_suite.py

test-watch: ## Run tests in watch mode (requires pytest-watch)
	@$(PYTHON) -m pytest-watch $(TESTS_DIR) --ignore=$(TESTS_DIR)/test_yaml_suite.py

# --- Development Targets ---
dev: install-dev parser ## Setup development environment
	@echo "✓ Development environment ready"

repl: ## Start the Titi REPL
	@$(PYTHON) -m titi

shell: ## Start interactive shell with titi loaded
	@$(PYTHON) -i -c "import titi; from titi import *"

# --- Example Targets ---
examples: $(SVG_FILES) ## Generate SVG diagrams from all YAML examples

%.svg: %.yaml
	@echo "Generating $@..."
	@echo "10" | $(PYTHON) -m titi $<

# --- Demonstration Targets ---
demo-bootstrap: parser ## Run the bootstrap demonstration
	@echo "→ Running bootstrap example..."
	@$(PYTHON) -m titi $(HOME_DIR)/$(EXAMPLES_DIR)/bootstrap.yaml

demo-supercompile: ## Run supercompilation examples
	@echo "→ Running supercompilation examples..."
	@$(PYTHON) -m titi $(HOME_DIR)/$(EXAMPLES_DIR)/supercompile.yaml

demo-hello: ## Run hello world example
	@$(PYTHON) -m titi $(HOME_DIR)/$(EXAMPLES_DIR)/hello-world.yaml

# --- Verification Targets ---
verify-parser: $(PARSER_BIN) ## Verify parser works on test YAML
	@echo "→ Testing parser with simple YAML..."
	@echo "test: value" | ./$(PARSER_BIN)

verify-build: parser test ## Verify complete build (parser + tests)
	@echo "✓ Build verification complete"

# --- Cleaning Targets ---
clean: ## Remove generated files
	@echo "→ Cleaning generated files..."
	@rm -f $(LEX_OUT) $(YACC_OUT) $(YACC_HEADER) $(PARSER_BIN)
	@rm -f $(PARSER_DIR)/lex.yy.c $(PARSER_DIR)/y.tab.c $(PARSER_DIR)/y.tab.h $(PARSER_DIR)/yaml_parser
	@rm -f $(SVG_FILES)
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name '*.pyc' -delete 2>/dev/null || true
	@echo "✓ Clean complete"

clean-all: clean ## Remove all generated files including build artifacts
	@echo "→ Deep cleaning..."
	@rm -rf build/ dist/ *.egg-info/
	@rm -rf .venv/
	@echo "✓ Deep clean complete"

# --- Rebuild Targets ---
rebuild: clean bootstrap ## Clean and rebuild everything
	@echo "✓ Rebuild complete"

rebuild-parser: ## Rebuild just the parser
	@rm -f $(LEX_OUT) $(YACC_OUT) $(YACC_HEADER) $(PARSER_BIN)
	@$(MAKE) parser

# --- Code Quality Targets ---
lint: ## Run linting (if configured)
	@echo "→ Running linters..."
	@$(PYTHON) -m pylint titi/ lib/ || true

format: ## Format code (if configured)
	@echo "→ Formatting code..."
	@$(PYTHON) -m black titi/ lib/ || true

# --- Documentation Targets ---
docs: ## Generate documentation
	@echo "→ Documentation generation not yet configured"

# --- Utility Targets ---
check-deps: ## Check if required tools are available
	@echo "→ Checking dependencies..."
	@command -v $(LEX) >/dev/null 2>&1 || { echo "✗ lex not found"; exit 1; }
	@command -v $(YACC) >/dev/null 2>&1 || { echo "✗ yacc not found"; exit 1; }
	@command -v $(CC) >/dev/null 2>&1 || { echo "✗ cc not found"; exit 1; }
	@command -v $(PYTHON) >/dev/null 2>&1 || { echo "✗ python3 not found"; exit 1; }
	@echo "✓ All required tools available"

show-config: ## Show build configuration
	@echo "Build Configuration:"
	@echo "  LEX:        $(LEX)"
	@echo "  YACC:       $(YACC)"
	@echo "  CC:         $(CC)"
	@echo "  PYTHON:     $(PYTHON)"
	@echo "  LEX_SRC:    $(LEX_SRC)"
	@echo "  YACC_SRC:   $(YACC_SRC)"
	@echo "  PARSER_BIN: $(PARSER_BIN)"

# --- All Target ---
all: bootstrap test ## Build everything and run tests
	@echo "✓ All targets complete"

# --- Watch Target ---
watch: ## Watch for changes and rebuild (requires entr)
	@echo "→ Watching for changes (Ctrl+C to stop)..."
	@find $(LIB_DIR) -name '*.l' -o -name '*.y' | entr -c make parser
