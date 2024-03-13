YAML_FILES = $(shell find src/ -type f -name '*.yaml')
GIF_FILES = $(patsubst src/%.yaml, src/%.gif, $(YAML_FILES))

.PHONY: all
all: Pipfile.lock $(GIF_FILES)

%.gif: __main__.py %.yaml
	pipenv run python $^

Pipfile.lock: Pipfile
	pipenv install
