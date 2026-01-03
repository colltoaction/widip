YAML_FILES := $(shell find examples -name '*.yaml')
SVG_FILES := $(YAML_FILES:.yaml=.svg)

.PHONY: all clean

all: $(SVG_FILES)

%.svg: %.yaml
	@echo "Generating $@..."
	@echo "10" | python3 -m widip $<

clean:
	rm -f $(SVG_FILES)
