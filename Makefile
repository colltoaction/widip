JPG_FILES := $(shell git ls-files '*.jpg')
YAML_FILES := $(JPG_FILES:.jpg=.yaml)

.PHONY: all clean

all: $(JPG_FILES)

%.jpg: %.yaml
	@echo "Generating $@..."
	@echo $< | bin/yaml/shell.yaml

clean:
	rm -f $(JPG_FILES)
