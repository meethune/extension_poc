.PHONY: build clean validate test all schemas schema-validate lint

DIST := dist
SRC := src
SCHEMAS := schemas

all: validate build test

build: $(DIST)/ext_01.cat

$(DIST)/ext_01.cat: $(shell find $(SRC) -type f 2>/dev/null) content.xml
	@mkdir -p $(DIST)
	uv run x4cat pack $(SRC) -o $(DIST)/ext_01.cat
	cp content.xml $(DIST)/content.xml
	@echo "Build complete: $(DIST)/"

schemas:
ifndef X4_GAME_DIR
	$(error X4_GAME_DIR not set — e.g. make schemas X4_GAME_DIR="/path/to/X4 Foundations")
endif
	uv run x4cat extract "$(X4_GAME_DIR)" -o $(SCHEMAS) -g '*.xsd'
	@echo "Schemas extracted to $(SCHEMAS)/"

lint:
ifndef X4_GAME_DIR
	$(error X4_GAME_DIR not set — e.g. make lint X4_GAME_DIR="/path/to/X4 Foundations")
endif
	uv run x4cat validate-diff "$(X4_GAME_DIR)" $(SRC)

schema-validate:
	uv run pytest tests/test_mod.py::TestSchema -q

validate:
	uv run pytest tests/test_mod.py::TestValidate -q

test: build
	uv run pytest -q -k "not TestSchema"

clean:
	rm -rf $(DIST)
