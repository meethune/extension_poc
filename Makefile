.PHONY: build clean validate test all

DIST := dist
SRC := src

all: validate build test

build: $(DIST)/ext_01.cat

$(DIST)/ext_01.cat: $(shell find $(SRC) -type f 2>/dev/null) content.xml
	@mkdir -p $(DIST)
	uv run x4cat pack $(SRC) -o $(DIST)/ext_01.cat
	cp content.xml $(DIST)/content.xml
	@echo "Build complete: $(DIST)/"

validate:
	uv run python -m pytest tests/test_mod.py::TestValidate -q

test: build
	uv run pytest -q

clean:
	rm -rf $(DIST)
