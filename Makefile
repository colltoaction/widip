YAML_FILES = $(shell find src/ -type f -name '*.yaml')
DIAGRAM_FILES = $(patsubst src/%.yaml, src/%.jpg, $(YAML_FILES))

.PHONY: all
all: Pipfile.lock $(DIAGRAM_FILES)

%.jpg: __main__.py %.yaml
	pipenv run python $^

Pipfile.lock: Pipfile
	pipenv install
