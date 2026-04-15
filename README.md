# extension_poc

Proof of concept [X4: Foundations](https://wiki.egosoft.com/X4%20Foundations%20Wiki/Modding%20Support/) extension mod template.

Uses [x4cat](https://github.com/meethune/x4cat) to pack mod files into `.cat/.dat` catalogs, generate and validate diff patches, and manage translations. See the [x4cat documentation](https://meethune.github.io/x4cat/) for full reference.

## Structure

```
content.xml              — Extension manifest (loose file, required by X4)
src/                     — Mod files (packed into catalog)
  md/                    — Mission Director scripts
  aiscripts/             — AI behavior scripts
  libraries/             — Library XML diff patches
dist/                    — Build output (do not commit)
base/                    — Extracted base files for xmldiff workflow (do not commit)
modified/                — Modified files for xmldiff workflow (do not commit)
schemas/                 — XSD schemas extracted from game (do not commit)
tests/                   — Build validation tests
```

## Setup

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Development workflow

The recommended workflow for modifying base game files uses XML diff patches
rather than full file replacement. This ensures compatibility with other mods
and game updates.

```bash
# 1. Extract the base game file you want to modify
x4cat extract "/path/to/X4 Foundations" -o ./base -g 'libraries/wares.xml'

# 2. Copy and edit
cp -r ./base ./modified
# ... edit files in ./modified ...

# 3. Generate a diff patch
x4cat xmldiff --base ./base/libraries/wares.xml \
              --mod  ./modified/libraries/wares.xml \
              -o src/libraries/wares.xml

# 4. Validate your patches against the game
make lint X4_GAME_DIR="/path/to/X4 Foundations"

# 5. Validate translations
make check-translations

# 6. Build and test
make all
```

Or use scaffolding to generate boilerplate:

```bash
# Scaffold a new ware
x4cat scaffold ware --id mymod_fuel --name "Super Fuel" --price-avg 500 -o src/

# Scaffold equipment by cloning an existing asset
x4cat scaffold equipment --id mymod_engine_macro --name "Fast Engine" \
  --clone-from engine_arg_s_allround_01_mk1_macro -o src/
```

## Build

```bash
make all                # validate, build, test
make build              # pack src/ into dist/ext_01.cat + copy content.xml
make validate           # XML well-formedness + structural checks
make check-translations # validate text references against t/*.xml
make test               # full test suite (includes build verification)
make clean              # remove dist/
```

## Diff patch linting

Validate that all XML diff patches in `src/` have XPath selectors that match
the base game files they target:

```bash
make lint X4_GAME_DIR="/path/to/X4 Foundations"
```

## Conflict checking

Check your mod against another mod for overlapping diff patches:

```bash
x4cat check-conflicts src/ /path/to/other_mod/src/
```

## Schema validation

Optionally extract XSD schemas from your X4 install for full schema validation
of MD and AI scripts:

```bash
make schemas X4_GAME_DIR="/path/to/X4 Foundations"
make schema-validate
```

Note: full XSD validation is slow (~70s) due to the size of Egosoft's schemas.
The default `make all` uses fast structural checks instead.

## Installing

Copy the contents of `dist/` into your X4 extensions directory:
```
<X4 install>/extensions/extension_poc/
```

The directory should contain `content.xml`, `ext_01.cat`, and `ext_01.dat`.

## License

MIT
